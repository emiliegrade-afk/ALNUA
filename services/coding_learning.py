"""Mem0 + journal hooks for the autonomous coding pipeline."""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

_QA_ERROR_RE = re.compile(r"QA pre-PR|Fichier vide|Fichier suspect|tsc --noEmit|expo-\*", re.I)


def _parse_qa_errors(error_message: str) -> list[str]:
    return [line.strip() for line in error_message.split("\n") if line.strip()][:10]


def record_qa_failure(
    *,
    agent_name: str,
    task_id: str | None,
    repo_slug: str | None,
    error_message: str,
    task_context: str = "",
) -> None:
    """Log QA failure + distill lesson into Mem0 for dev_app."""
    from services.coding_error_journal import record_coding_error
    from skills.skill_agent_learning import learn_from_failure, memory_agent_id
    from skills.skill_error_journal import log_error

    qa_errors = _parse_qa_errors(error_message)
    error_type = "QAError" if _QA_ERROR_RE.search(error_message) else "CodingError"

    try:
        record_coding_error(
            agent_name=agent_name,
            task_id=task_id,
            repo_slug=repo_slug,
            error_type=error_type,
            error_message=error_message,
            qa_errors=qa_errors,
            status="open",
        )
    except Exception as exc:
        logger.warning("[CodingLearning] journal write failed: %s", exc)

    try:
        log_error(
            agent_name=agent_name,
            error_type=error_type,
            error_message=error_message[:2000],
            context=(task_context or "")[:1000],
            task_id=task_id,
        )
    except Exception:
        pass

    lesson = (
        f"Échec QA coding ({task_id or 'task'}) sur repo {repo_slug or '?'}: "
        f"{error_message[:400]}. "
        "Règles: jamais de fichier vide, pas de noms suspects, "
        "expo install pour deps SDK 56, tsc --noEmit doit passer avant PR."
    )
    try:
        learn_from_failure(
            agent_id=memory_agent_id(agent_name),
            task=task_context or str(task_id or "coding"),
            error=lesson,
        )
    except Exception as exc:
        logger.warning("[CodingLearning] mem0 failure lesson: %s", exc)


def record_coding_success(
    *,
    agent_name: str,
    task_id: str | None,
    repo_slug: str | None,
    outcome_summary: str,
) -> None:
    """Resolve journal entries + positive Mem0 lesson after successful PR."""
    from services.coding_error_journal import resolve_matching_errors
    from skills.skill_agent_learning import learn_from_outcome, memory_agent_id

    try:
        resolve_matching_errors(
            task_id=task_id,
            error_type=None,
            solution=f"PR créée: {outcome_summary[:300]}",
        )
    except Exception:
        pass

    try:
        learn_from_outcome(
            agent_id=memory_agent_id(agent_name),
            task=f"{repo_slug or 'repo'}:{task_id or 'task'}",
            outcome=outcome_summary[:600],
            success=True,
        )
    except Exception:
        pass


def enrich_spec_with_lessons(spec: dict[str, Any]) -> dict[str, Any]:
    """Add QA pattern block to coding spec description."""
    from services.coding_error_journal import build_lessons_block

    block = build_lessons_block()
    if not block:
        return spec
    enriched = dict(spec)
    enriched["description"] = (spec.get("description") or "") + block
    return enriched
