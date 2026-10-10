"""Comms Academy API — Lancement NAÏA training (SPEC_STUDIO_ACADEMIES / DEC-036)."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter(prefix="/comms-academy", tags=["comms-academy"])


@router.get("/status")
def comms_academy_status() -> dict[str, Any]:
    """Snapshot CEO : progression, niveaux, gate, prochain exercice."""
    from services.comms_academy_runner import studio_status

    return studio_status()


@router.get("/curriculum")
def comms_academy_curriculum(level: int | None = None) -> dict[str, Any]:
    """Liste des exercices (tous ou filtrés par niveau), avec état courant."""
    from services.academy_curriculum_comms import LEVEL_META, all_exercises
    from services.academy_program_comms import COMMS_PROGRAM
    from services.studio_academy_program import exercise_sort_key
    from services.studio_academy_state import load_progress

    states = (load_progress(COMMS_PROGRAM).get("exercises") or {})
    exercises = [e for e in sorted(all_exercises(), key=exercise_sort_key) if level is None or e.level == level]
    return {
        "levels": LEVEL_META,
        "count": len(exercises),
        "exercises": [
            {
                "id": e.exercise_id,
                "level": e.level,
                "agent_id": e.agent_id,
                "method": e.method,
                "title": e.title,
                "deliverable": e.deliverable_path,
                "refs": e.context_refs,
                "dod": e.dod,
                "status": (states.get(e.exercise_id) or {}).get("status") or "pending",
            }
            for e in exercises
        ],
    }


@router.get("/gate")
def comms_academy_gate() -> dict[str, Any]:
    """Évalue (et persiste) les critères « Academy → activation réelle NAÏA »."""
    from services.academy_program_comms import COMMS_PROGRAM
    from services.studio_academy_gate import evaluate_gate

    return evaluate_gate(COMMS_PROGRAM)


@router.post("/run-next")
def comms_academy_run_next() -> dict[str, Any]:
    """Trigger CEO manuel — exécute le prochain exercice en attente (agent + QA)."""
    from services.comms_academy_runner import run_next_exercise

    return run_next_exercise()


@router.post("/run/{exercise_id}")
def comms_academy_run(exercise_id: str) -> dict[str, Any]:
    """Trigger ciblé sur un exercice précis (ex. CN1.1). Idempotent sur états terminaux."""
    from services.comms_academy_runner import run_exercise

    return run_exercise(exercise_id)
