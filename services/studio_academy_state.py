"""Studio Academy — progress tracking, generic engine (SPEC_STUDIO_ACADEMIES / DEC-036).

State lives in ``data/<program.progress_filename>`` (env-overridable via
``program.progress_env``). Deliverables live in the write-only ALNUA workspace
(``rnd_workspace`` conventions, per-program pole/slug).
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.studio_academy_program import AcademyProgram, StudioExercise, exercise_sort_key

logger = logging.getLogger(__name__)

MAX_QA_ATTEMPTS = 3


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_progress(program: AcademyProgram) -> dict[str, Any]:
    levels = {
        str(lv): {
            "name": meta["name"],
            "total": meta["exercises"],
            "done": 0,
            "failed": 0,
            "in_progress": 0,
        }
        for lv, meta in program.level_meta.items()
    }
    return {
        "version": 1,
        "program": program.program_id,
        "updated_at": _now_iso(),
        "current_level": 1,
        "total_exercises": len(program.exercises()),
        "completed_exercises": 0,
        "failed_exercises": 0,
        "success_rate_pct": 0.0,
        "levels": levels,
        "exercises": {},  # exercise_id → {status, attempts, qa_verdict, path, run_id, ...}
        "gate": {"gate_open": False, "readiness_pct": 0.0},
        "notes": program.notes,
    }


def load_progress(program: AcademyProgram, progress_path: Path | None = None) -> dict[str, Any]:
    path = progress_path or program.progress_path()
    if not path.is_file():
        data = default_progress(program)
        save_progress(program, data, path)
        return data
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return default_progress(program)
        data.setdefault("exercises", {})
        data.setdefault("levels", default_progress(program)["levels"])
        return data
    except Exception as exc:
        logger.warning("%s academy progress load failed: %s", program.program_id, exc)
        return default_progress(program)


def save_progress(program: AcademyProgram, data: dict[str, Any], progress_path: Path | None = None) -> Path:
    path = progress_path or program.progress_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = _now_iso()
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def _recompute(program: AcademyProgram, data: dict[str, Any]) -> None:
    """Recompute level counters + success rate from the per-exercise map."""
    exercises = data.get("exercises") or {}
    levels: dict[str, dict[str, Any]] = data["levels"]
    for lv in levels.values():
        lv["done"] = lv["failed"] = lv["in_progress"] = 0
    for ex in program.exercises():
        state = exercises.get(ex.exercise_id) or {}
        status = state.get("status")
        lv = levels[str(ex.level)]
        if status == "validated":
            lv["done"] += 1
        elif status == "failed":
            lv["failed"] += 1
        elif status in ("in_progress", "rejected"):
            lv["in_progress"] += 1
    done = sum(lv["done"] for lv in levels.values())
    failed = sum(lv["failed"] for lv in levels.values())
    data["completed_exercises"] = done
    data["failed_exercises"] = failed
    total_finished = done + failed
    data["success_rate_pct"] = round(100.0 * done / total_finished, 1) if total_finished else 0.0
    # Current level = first level not fully finished
    data["current_level"] = next(
        (int(k) for k, lv in sorted(levels.items()) if lv["done"] + lv["failed"] < lv["total"]),
        max(int(k) for k in levels),
    )


def record_exercise_result(
    program: AcademyProgram,
    exercise_id: str,
    *,
    status: str,
    qa_verdict: str | None = None,
    qa_feedback: str = "",
    path: str = "",
    run_id: str | None = None,
    canon_conflict: bool | None = None,
    progress_path: Path | None = None,
) -> dict[str, Any]:
    """Record one exercise outcome and persist.

    status: in_progress (attempt start) | rejected (QA KO, retryable) |
    validated (QA OK, terminal) | failed (attempts exhausted, terminal).
    """
    data = load_progress(program, progress_path)
    entry = (data.get("exercises") or {}).get(exercise_id) or {"attempts": 0}
    if status == "in_progress":
        entry["attempts"] = int(entry.get("attempts") or 0) + 1
    entry.update(
        {
            "status": status,
            "qa_verdict": qa_verdict,
            "qa_feedback": (qa_feedback or "")[:500],
            "path": path,
            "run_id": run_id,
            "updated_at": _now_iso(),
        }
    )
    if canon_conflict is not None:
        entry["canon_conflict"] = bool(canon_conflict)
    data.setdefault("exercises", {})[exercise_id] = entry
    _recompute(program, data)
    save_progress(program, data, progress_path)
    return data


def next_pending_exercise(program: AcademyProgram, progress_path: Path | None = None) -> StudioExercise | None:
    """First exercise (level then id order) never attempted or rejected with attempts left."""
    exercises = load_progress(program, progress_path).get("exercises") or {}
    for ex in sorted(program.exercises(), key=exercise_sort_key):
        state = exercises.get(ex.exercise_id) or {}
        status = state.get("status")
        attempts = int(state.get("attempts") or 0)
        if status in ("validated", "failed"):
            continue
        if status == "rejected" and attempts >= MAX_QA_ATTEMPTS:
            continue
        return ex
    return None
