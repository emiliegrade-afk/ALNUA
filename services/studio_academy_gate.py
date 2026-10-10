"""Studio Academy — production gate, generic engine (SPEC_STUDIO_ACADEMIES / DEC-036).

Weighted checks, readiness %, persisted in the program's progress file.
Gate open = department declared ready for real production (UE5.8 for gaming,
Eve prototype for robo). The 5th check is program-specific (``gate_extra``).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.studio_academy_program import AcademyProgram
from services.studio_academy_state import load_progress, save_progress


def evaluate_gate(
    program: AcademyProgram,
    *,
    persist: bool = True,
    progress_path: Path | None = None,
) -> dict[str, Any]:
    """Evaluate readiness checks and persist them into the progress file."""
    progress = load_progress(program, progress_path)
    exercises = progress.get("exercises") or {}

    success_rate = float(progress.get("success_rate_pct") or 0.0)
    finished = int(progress.get("completed_exercises") or 0) + int(progress.get("failed_exercises") or 0)

    n3_meta = program.level_meta[3]
    n3_done = int((progress.get("levels") or {}).get("3", {}).get("done") or 0)

    validated_agents = {
        ex.agent_id
        for ex in program.exercises()
        if (exercises.get(ex.exercise_id) or {}).get("status") == "validated"
    }
    roles_covered = len(set(program.studio_roles) & validated_agents)

    open_canon_conflicts = sum(
        1
        for state in exercises.values()
        if state.get("canon_conflict") and state.get("status") != "validated"
    )

    extra_name, extra_ok = program.gate_extra()
    checks: dict[str, Any] = {
        "success_rate_65": success_rate >= 65.0 and finished >= 10,
        program.gate_n3_check: n3_done >= int(n3_meta["exercises"]),
        f"roles_coverage_{len(program.studio_roles)}": roles_covered >= len(program.studio_roles),
        # Meaningful only once work exists — vacuous "no conflicts" on an empty
        # academy would inflate readiness.
        "canon_clean": finished > 0 and open_canon_conflicts == 0,
        extra_name: extra_ok,
    }
    passed = sum(1 for ok in checks.values() if ok)
    readiness = round(100.0 * passed / len(checks), 1)
    gate = {
        **checks,
        "roles_covered": roles_covered,
        "open_canon_conflicts": open_canon_conflicts,
        "gate_open": passed == len(checks),
        "readiness_pct": readiness,
    }
    if persist:
        progress["gate"] = gate
        progress["gate_evaluated_at"] = datetime.now(timezone.utc).isoformat()
        save_progress(program, progress, progress_path)
    return gate
