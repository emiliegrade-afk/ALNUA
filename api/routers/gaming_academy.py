"""Gaming Academy API — studio paper-slice training (SPEC_GAMING_ACADEMY / DEC-034)."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter(prefix="/gaming-academy", tags=["gaming-academy"])


@router.get("/status")
def gaming_academy_status() -> dict[str, Any]:
    """Snapshot CEO : progression, niveaux, gate, prochain exercice."""
    from services.gaming_academy_runner import studio_status

    return studio_status()


@router.get("/curriculum")
def gaming_academy_curriculum(level: int | None = None) -> dict[str, Any]:
    """Liste des exercices (tous ou filtrés par niveau), avec état courant."""
    from services.gaming_academy_curriculum import LEVEL_META, all_exercises, exercise_sort_key
    from services.gaming_academy_progress import load_progress

    states = load_progress().get("exercises") or {}
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
def gaming_academy_gate() -> dict[str, Any]:
    """Évalue (et persiste) les critères « Academy → production Wyrdheim »."""
    from services.gaming_academy_gate import evaluate_gate

    return evaluate_gate()


@router.post("/run-next")
def gaming_academy_run_next() -> dict[str, Any]:
    """Trigger CEO manuel — exécute le prochain exercice en attente (agent + QA)."""
    from services.gaming_academy_runner import run_next_exercise

    return run_next_exercise()


@router.post("/run/{exercise_id}")
def gaming_academy_run(exercise_id: str) -> dict[str, Any]:
    """Trigger ciblé sur un exercice précis (ex. GN1.3). Idempotent sur états terminaux."""
    from services.gaming_academy_runner import run_exercise

    return run_exercise(exercise_id)
