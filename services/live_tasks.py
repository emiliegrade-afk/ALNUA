"""Jarvis Live — background task registry (SPEC_JARVIS_LIVE §5, DEC-038).

A voice or UI front-end creates tasks; agents of the Hub execute them. No third
executor is introduced: ``coo`` / ``secretary`` reuse the Hub chat entry point and
``plan`` reuses ``plan_executor.run_coo_plan``.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from services.live_tasks_store import (
    ACTIVE_STATUSES,
    STATUS_CANCELLED,
    STATUS_DONE,
    STATUS_FAILED,
    STATUS_QUEUED,
    STATUS_RUNNING,
    LiveTask,
    LiveTaskStore,
    _now,
)

logger = logging.getLogger(__name__)

MAX_INSTRUCTION_CHARS = 4000
MAX_RESULT_CHARS = 8000
MAX_STEP_PREVIEW_CHARS = 300

_store = LiveTaskStore()
_pool: ThreadPoolExecutor | None = None


@dataclass
class Outcome:
    text: str
    artifacts: list[str] = field(default_factory=list)


def get_store() -> LiveTaskStore:
    return _store


# ── Executors ────────────────────────────────────────────────────────────────


def _run_chat_agent(agent_id: str, instruction: str, session_id: str) -> Outcome:
    from services.assistant_router import assistant_chat
    from services.live_session_context import with_session_context

    prompted = with_session_context(instruction, session_id)
    reply = assistant_chat(prompted, agent=agent_id, session_id=session_id, channel="live")  # type: ignore[arg-type]
    return Outcome(text=str(reply.get("response", "")).strip())


def _run_plan(instruction: str) -> Outcome:
    from services.plan_executor import run_coo_plan

    outcome = run_coo_plan(instruction)
    if outcome.get("error"):
        raise RuntimeError(str(outcome["error"]))
    total = int(outcome.get("total_steps", 0))
    ok = int(outcome.get("success_count", 0))
    if total and ok == 0:
        raise RuntimeError("Aucune étape du plan n'a abouti")
    lines = [f"{outcome.get('title', 'Plan')} — {ok}/{total} étapes réussies"]
    for step in outcome.get("results", []):
        mark = "OK" if step.get("success") else "ÉCHEC"
        detail = str(step.get("result") or step.get("error") or "")[:MAX_STEP_PREVIEW_CHARS]
        lines.append(f"[{mark}] {step.get('agent_id', '?')} — {detail}")
    return Outcome(text="\n".join(lines))


def _execute(agent_id: str, instruction: str, session_id: str) -> Outcome:
    from services.live_html_app import maybe_html
    from services.live_pc_find import maybe_find
    from services.live_pc_input import maybe_pc_input
    from services.live_pc_actions import maybe_open

    html = maybe_html(instruction)
    if html is not None:
        return Outcome(text=html)
    typed = maybe_pc_input(instruction)
    if typed is not None:
        return Outcome(text=typed)
    found = maybe_find(instruction)
    if found is not None:
        return Outcome(text=found)
    opened = maybe_open(instruction)
    if opened is not None:
        return Outcome(text=opened)
    if agent_id == "plan":
        return _run_plan(instruction)
    return _run_chat_agent(agent_id, instruction, session_id)


SUPPORTED_AGENTS = frozenset({"coo", "secretary", "plan"})


# ── Registry ─────────────────────────────────────────────────────────────────


def allowed_agents() -> list[str]:
    from config.settings import get_settings

    configured = [a.strip() for a in get_settings().live_task_agents.split(",")]
    return [a for a in configured if a in SUPPORTED_AGENTS]


def _submit(fn: Callable[..., None], *args: Any) -> None:
    """Indirection so tests can run tasks inline instead of in the worker pool."""
    global _pool
    if _pool is None:
        from config.settings import get_settings

        _pool = ThreadPoolExecutor(
            max_workers=get_settings().live_task_max_concurrent,
            thread_name_prefix="live-task",
        )
    _pool.submit(fn, *args)


def _notify(task: LiveTask) -> None:
    # A broken event bus must never fail the task it describes.
    try:
        from services.event_bus import emit

        emit(
            "live_task_updated",
            {"task_id": task.id, "status": task.status, "agent_id": task.agent_id},
            source_agent=task.agent_id,
        )
    except Exception:
        logger.debug("live_task_updated emit failed", exc_info=True)


def _update(task_id: str, **fields: Any) -> LiveTask | None:
    task = _store.update(task_id, **fields)
    if task is not None:
        _notify(task)
    return task


def create_task(
    agent_id: str,
    instruction: str,
    session_id: str = "live",
    file_ids: list[str] | None = None,
) -> LiveTask:
    """Validate, persist and enqueue a task. Raises ValueError on bad input."""
    from services.hub_user_files import MAX_FILES_PER_TASK, build_attachment_context
    from services.input_sanitizer import sanitize_user_input

    if agent_id not in allowed_agents():
        raise ValueError(f"Agent non autorisé pour Jarvis Live : {agent_id}")
    ids = [f.strip() for f in (file_ids or []) if f and f.strip()]
    if len(ids) > MAX_FILES_PER_TASK:
        raise ValueError(f"Maximum {MAX_FILES_PER_TASK} fichiers par tâche.")
    if ids:
        build_attachment_context(ids)
    # Business data on purpose (same choice as the other agent endpoints): no PII redaction.
    safe = sanitize_user_input(instruction, max_length=MAX_INSTRUCTION_CHARS, redact_pii_enabled=False)
    if not safe and not ids:
        raise ValueError("Instruction vide après nettoyage")

    task = _store.add(
        agent_id,
        safe or "Voir les pièces jointes.",
        session_id=(session_id or "live")[:64],
        file_ids=ids,
    )
    _notify(task)
    _submit(run_task, task.id)
    return task


def _verify(outcome: Outcome) -> str:
    """Return an error code, or '' when the *real* state backs the agent's claim."""
    if not outcome.text:
        return "empty_result"
    for path in outcome.artifacts:
        if not Path(path).exists():
            return f"missing_artifact:{path}"
    return ""


def run_task(task_id: str) -> None:
    """Worker entry point. Never raises: failures are recorded on the task."""
    task = _store.get(task_id)
    if task is None or task.status != STATUS_QUEUED:
        return  # cancelled while waiting, or unknown

    _update(task_id, status=STATUS_RUNNING, started_at=_now())
    try:
        from services.hub_user_files import merge_instruction_with_files

        prompt = merge_instruction_with_files(task.instruction, task.file_ids)
        outcome = _execute(task.agent_id, prompt, task.session_id)
        error = _verify(outcome)
    except Exception as exc:
        logger.warning("live task %s failed: %s", task_id, exc)
        _finish(task_id, STATUS_FAILED, error=f"{type(exc).__name__}: {exc}"[:500])
        return

    if error:
        _finish(task_id, STATUS_FAILED, error=error)
    else:
        _finish(
            task_id,
            STATUS_DONE,
            result=outcome.text[:MAX_RESULT_CHARS],
            artifacts=outcome.artifacts,
        )


def _finish(task_id: str, status: str, **fields: Any) -> None:
    current = _store.get(task_id)
    if current is None or current.status == STATUS_CANCELLED:
        return  # the user cancelled while it ran: the late result is dropped
    _update(task_id, status=status, finished_at=_now(), **fields)


def cancel_task(task_id: str) -> LiveTask | None:
    """Cancel a queued or running task.

    A running agent call cannot be interrupted mid-flight; its result is discarded
    when it returns (see ``_finish``).
    """
    task = _store.get(task_id)
    if task is None:
        return None
    if task.status not in ACTIVE_STATUSES:
        return task
    return _update(task_id, status=STATUS_CANCELLED, finished_at=_now())


def get_task(task_id: str) -> LiveTask | None:
    return _store.get(task_id)


def list_tasks(status: str | None = None, limit: int = 50) -> list[LiveTask]:
    return _store.list_tasks(status=status, limit=limit)
