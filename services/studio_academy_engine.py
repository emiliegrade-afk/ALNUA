"""Studio Academy — runner, generic engine (SPEC_STUDIO_ACADEMIES / DEC-036).

Flow: pick exercise → invoke the agent's real method → write deliverable in the
write-only workspace (rnd_workspace conventions) → QA review by the program's
QA agent → record progress + competition points. Triggered by the idle queue
(kind ``<program>_academy_exercise``) or manually via the program's router.

Department wrappers (``gaming_academy_runner``, ``robo_academy_runner``) pass
their own ``get_agent``/``qa_review`` hooks so tests can monkeypatch dispatch.
"""

from __future__ import annotations

import importlib
import logging
from pathlib import Path
from typing import Any

from services.studio_academy_program import AcademyProgram, StudioExercise
from services.studio_academy_state import (
    MAX_QA_ATTEMPTS,
    load_progress,
    next_pending_exercise,
    record_exercise_result,
)

logger = logging.getLogger(__name__)

# Same DoD contract as QaGamingAgent.review_deliverable — used for programs
# whose QA agent is a plain AgentBase (run_json_task), e.g. qa_robot.
_QA_PROMPT_TEMPLATE = """Relis ce livrable de la {title} contre sa Definition of Done.

Livrable : {exercise_title}

Definition of Done :
{checklist}

Contenu du livrable :
---
{content}
---

Pour chaque point du DoD, décide pass/fail avec une justification courte.
Le DoD est le contrat : verdict "validated" si et seulement si tous les points du DoD
passent ET qu'il n'y a pas de contradiction canon avec {subject}. Ne rejette jamais
pour un critère absent du DoD (formatage, niveau de détail, conventions internes) :
mets ces remarques dans "feedback" comme suggestions non bloquantes.

Réponds en JSON :
{{
  "verdict": "validated|rejected",
  "dod_checks": [{{ "check": "string", "passed": true, "note": "string" }}],
  "canon_conflict": false,
  "feedback": "Feedback actionnable pour l'agent (vide si validated)"
}}"""


def _get_agent(program: AcademyProgram, agent_id: str) -> Any:
    module_name, class_name = program.agent_classes[agent_id]
    cls = getattr(importlib.import_module(module_name), class_name)
    return cls()


def _read_refs(program: AcademyProgram, exercise: StudioExercise) -> str:
    if not exercise.context_refs:
        return ""
    from services.rnd_workspace import read_deliverable

    parts: list[str] = []
    for ref in exercise.context_refs:
        try:
            content = read_deliverable(program.pole, program.slug, ref)
        except Exception:
            content = None
        if content:
            parts.append(f"### {ref}\n{content[:1500]}")
    if not parts:
        return ""
    return "Livrables existants à respecter (canon) :\n\n" + "\n\n".join(parts)


def _build_kwargs(program: AcademyProgram, exercise: StudioExercise, context: str) -> dict[str, Any]:
    """Map exercise → real method kwargs. Context goes to the method's natural
    free-text param when it exists, else appended to the brief-bearing arg."""
    kwargs: dict[str, Any] = dict(exercise.method_kwargs)
    if exercise.method == "handle_instruction":
        kwargs["instruction"] = exercise.brief + (f"\n\n{context}" if context else "")
        return kwargs
    if exercise.method == "run_json_task":
        # Agents whose public methods all write to production tables (comms
        # queues, campaigns) train via the shared AgentBase JSON path — same
        # LLM capability, no side effects (DEC-036).
        kwargs.setdefault("action", "academy_exercise")
        kwargs["prompt"] = exercise.brief + (f"\n\n{context}" if context else "")
        kwargs.setdefault("learning_key", exercise.title)
        kwargs.setdefault("input_summary", exercise.title[:100])
        return kwargs
    if exercise.method == "run_studio_task":
        kwargs["title"] = exercise.title
        kwargs["description"] = exercise.brief + (f"\n\n{context}" if context else "")
        return kwargs
    if program.subject_kwarg:
        kwargs.setdefault(program.subject_kwarg, program.subject)
    if not context:
        return kwargs
    target = program.context_params.get(exercise.method)
    if target:
        kwargs[target] = (kwargs.get(target, "") + f"\n\n{context}").strip()
    elif kwargs:
        # Fallback: last declared kwarg is always a free-text descriptor here.
        last = next(reversed(kwargs))
        kwargs[last] = f"{kwargs[last]}\n\n{context}"
    return kwargs


def _render_markdown(program: AcademyProgram, exercise: StudioExercise, result: dict[str, Any]) -> str:
    lines = [
        f"# {exercise.title}",
        "",
        f"> Exercice {exercise.exercise_id} — N{exercise.level} — agent `{exercise.agent_id}` — {program.title}",
        "",
        "## Brief",
        "",
        exercise.brief,
        "",
        "## Contenu",
        "",
    ]
    for key, value in result.items():
        lines.append(f"### {key}")
        lines.append("")
        lines.append(_render_value(value))
        lines.append("")
    return "\n".join(lines)


def _render_value(value: Any, indent: int = 0) -> str:
    pad = "  " * indent
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)) or value is None:
        return str(value)
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            if isinstance(item, dict):
                # First string field becomes the bullet head; skip it in the
                # detail lines so it isn't duplicated (QA reads this markdown).
                head_key = next((k for k, v in item.items() if isinstance(v, str)), None)
                if head_key is None:
                    out.append(f"{pad}- {_render_value(item, indent)}")
                    continue
                out.append(f"{pad}- **{item[head_key]}**")
                for k, v in item.items():
                    if k == head_key:
                        continue
                    out.extend(_render_kv(pad, k, v, indent))
            else:
                out.append(f"{pad}- {_render_value(item, indent)}")
        return "\n".join(out)
    if isinstance(value, dict):
        out = []
        for k, v in value.items():
            out.extend(_render_kv(pad, k, v, indent))
        return "\n".join(out)
    return str(value)


def _render_kv(pad: str, key: str, value: Any, indent: int) -> list[str]:
    """Nested lists/dicts go on their own lines — inline gluing is unreadable."""
    if isinstance(value, (list, dict)):
        return [f"{pad}  - {key} :", _render_value(value, indent + 2)]
    return [f"{pad}  - {key} : {_render_value(value, indent + 1)}"]


def _write_versioned(program: AcademyProgram, exercise: StudioExercise, content: str) -> str:
    """Write-only: never overwrite — a retry after QA rejection writes -v2, -v3…"""
    from services.rnd_workspace import pole_path, write_deliverable

    path = exercise.deliverable_path
    if (pole_path(program.pole, program.slug) / path).exists():
        stem, dot, suffix = path.rpartition(".")
        base = stem if dot else path
        ext = f".{suffix}" if dot else ""
        v = 2
        while (pole_path(program.pole, program.slug) / f"{base}-v{v}{ext}").exists():
            v += 1
        path = f"{base}-v{v}{ext}"
    write_deliverable(program.pole, program.slug, path, content)
    return path


def _default_qa_review(program: AcademyProgram, exercise: StudioExercise, content: str) -> dict[str, Any]:
    """QA via the program's QA agent (AgentBase.run_json_task) — DoD contract."""
    qa = _get_agent(program, program.qa_agent_id)
    checklist = "\n".join(f"- {c}" for c in exercise.dod) or "- (qualité générale)"
    prompt = _QA_PROMPT_TEMPLATE.format(
        title=program.title,
        exercise_title=exercise.title,
        checklist=checklist,
        content=content[:6000],
        subject=program.subject,
    )
    return qa.run_json_task(
        action="review_deliverable",
        prompt=prompt,
        learning_key=exercise.title,
        input_summary=f"review | {exercise.title}",
        output_summary=lambda r: f"{r.get('verdict')} ({len(r.get('dod_checks', []))} checks)",
        temperature=0.3,
        max_tokens=2048,
    )


def _award(agent_id: str, reason: str, note: str) -> None:
    try:
        from services.competition import add_points

        add_points(agent_id, reason, note=note)
    except Exception:
        pass


def _record_trust(program: AcademyProgram, exercise: StudioExercise, *, success: bool, weight: float) -> float | None:
    """Feed the autonomy loop (DEC-043): academy QA outcomes update agent trust
    (paper weight — successes capped at ACADEMY_TRUST_CAP by the trust store)."""
    try:
        from services.agent_trust import record_validation

        row = record_validation(
            exercise.agent_id,
            success=success,
            weight=weight,
            note=f"{program.title} {exercise.exercise_id}",
            source=f"academy:{program.program_id}",
        )
        return float(row.get("score") or 0.0)
    except Exception:
        return None


def _manifest(program: AcademyProgram, agent_id: str, status: str, path: str) -> None:
    try:
        from services.rnd_workspace import update_manifest_agent

        update_manifest_agent(program.slug, agent_id, status=status, files=[path])
    except Exception as exc:
        logger.warning("%s academy manifest update failed: %s", program.program_id, exc)


def run_exercise(
    program: AcademyProgram,
    exercise_id: str,
    *,
    qa_enabled: bool = True,
    get_agent: Any | None = None,
    qa_review: Any | None = None,
    progress_path: Path | None = None,
) -> dict[str, Any]:
    """Execute one exercise: agent → deliverable → QA → progress. Idempotent on
    terminal states (validated/failed are skipped)."""
    get_agent = get_agent or (lambda agent_id: _get_agent(program, agent_id))
    qa_review = qa_review or (lambda ex, content: _default_qa_review(program, ex, content))

    exercise = next((e for e in program.exercises() if e.exercise_id == exercise_id), None)
    if exercise is None:
        return {"ok": False, "error": f"unknown_exercise:{exercise_id}"}

    state = (load_progress(program, progress_path).get("exercises") or {}).get(exercise_id) or {}
    if state.get("status") in ("validated", "failed"):
        return {"ok": True, "skipped": True, "status": state["status"], "exercise_id": exercise_id}

    record_exercise_result(program, exercise_id, status="in_progress", progress_path=progress_path)
    attempts = int(state.get("attempts") or 0) + 1
    try:
        context = _read_refs(program, exercise)
        if state.get("qa_feedback"):
            context = (context + "\n\n" if context else "") + f"Feedback QA précédent à intégrer :\n{state['qa_feedback']}"
        agent = get_agent(exercise.agent_id)
        method = getattr(agent, exercise.method)
        raw = method(**_build_kwargs(program, exercise, context))
        result = raw if isinstance(raw, dict) else {"response": str(raw)}
    except Exception as exc:
        logger.exception("%s academy exercise %s failed", program.program_id, exercise_id)
        status = "failed" if attempts >= MAX_QA_ATTEMPTS else "rejected"
        record_exercise_result(
            program, exercise_id, status=status, qa_feedback=f"exception: {exc}"[:500], progress_path=progress_path
        )
        trust = _record_trust(program, exercise, success=False, weight=2.0 if status == "failed" else 1.0)
        return {"ok": False, "exercise_id": exercise_id, "status": status, "error": str(exc)[:300], "trust_score": trust}

    content = _render_markdown(program, exercise, result)
    path = _write_versioned(program, exercise, content)
    _award(exercise.agent_id, "task_completed", note=f"{program.title} {exercise_id}")

    review: dict[str, Any] = {"verdict": "validated", "dod_checks": [], "feedback": ""}
    if qa_enabled:
        try:
            review = qa_review(exercise, content)
        except Exception as exc:
            # QA unavailable must not silently validate — mark retryable.
            logger.warning("%s academy QA unavailable for %s: %s", program.program_id, exercise_id, exc)
            record_exercise_result(
                program, exercise_id, status="rejected",
                qa_feedback=f"qa_unavailable: {exc}"[:500], path=path, progress_path=progress_path,
            )
            return {"ok": False, "exercise_id": exercise_id, "status": "rejected", "error": f"qa:{exc}"[:300]}

    verdict = str(review.get("verdict") or "rejected")
    feedback = str(review.get("feedback") or "")
    canon_conflict = bool(review.get("canon_conflict"))
    if verdict == "validated":
        record_exercise_result(
            program, exercise_id, status="validated", qa_verdict=verdict,
            path=path, canon_conflict=canon_conflict, progress_path=progress_path,
        )
        _award(exercise.agent_id, "task_validated", note=f"{program.title} {exercise_id} QA OK")
        _manifest(program, exercise.agent_id, "success", path)
        trust = _record_trust(program, exercise, success=True, weight=0.5)
        return {"ok": True, "exercise_id": exercise_id, "status": "validated", "path": path, "review": review, "trust_score": trust}

    status = "failed" if attempts >= MAX_QA_ATTEMPTS else "rejected"
    record_exercise_result(
        program, exercise_id, status=status, qa_verdict=verdict, qa_feedback=feedback,
        path=path, canon_conflict=canon_conflict, progress_path=progress_path,
    )
    _manifest(program, exercise.agent_id, status, path)
    trust = _record_trust(program, exercise, success=False, weight=2.0 if status == "failed" else 1.0)
    return {"ok": status != "failed", "exercise_id": exercise_id, "status": status, "path": path, "review": review, "trust_score": trust}


def run_next_exercise(
    program: AcademyProgram,
    *,
    qa_enabled: bool = True,
    get_agent: Any | None = None,
    qa_review: Any | None = None,
    progress_path: Path | None = None,
) -> dict[str, Any]:
    """Pick and run the next pending exercise (idle drain entry point)."""
    exercise = next_pending_exercise(program, progress_path)
    if exercise is None:
        return {"ok": True, "reason": "nothing_pending"}
    return run_exercise(
        program, exercise.exercise_id,
        qa_enabled=qa_enabled, get_agent=get_agent, qa_review=qa_review, progress_path=progress_path,
    )


def studio_status(program: AcademyProgram, progress_path: Path | None = None) -> dict[str, Any]:
    """CEO-friendly snapshot for the cockpit / endpoints."""
    progress = load_progress(program, progress_path)
    nxt = next_pending_exercise(program, progress_path)
    return {
        "program": program.program_id,
        "subject": program.subject,
        "game": program.subject,  # cockpit compat (gaming key kept)
        "current_level": progress.get("current_level"),
        "completed": progress.get("completed_exercises"),
        "failed": progress.get("failed_exercises"),
        "total": progress.get("total_exercises"),
        "success_rate_pct": progress.get("success_rate_pct"),
        "levels": progress.get("levels"),
        "gate": progress.get("gate"),
        "next_exercise": (
            {"id": nxt.exercise_id, "title": nxt.title, "agent_id": nxt.agent_id} if nxt else None
        ),
        "deliverables_dir": f"ALNUA_WORKSPACE/{program.pole}/{program.slug}/",
        "progress_file": f"data/{program.progress_filename}",
    }
