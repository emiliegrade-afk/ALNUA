"""ALNUA Academy API — curriculum, progress, seed, sprint."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter(prefix="/academy", tags=["academy"])


@router.get("/status")
def academy_status() -> dict[str, Any]:
    """Progression académie + gate NUAWAY + snippet Mem0."""
    from services.academy_progress import get_academy_status

    return get_academy_status()


@router.get("/curriculum")
def academy_curriculum(level: int | None = None) -> dict[str, Any]:
    """Liste des exercices (tous ou par niveau)."""
    from services.academy_curriculum import (
        LEVEL_META,
        all_exercises,
        exercises_for_level,
    )

    if level is not None:
        exercises = exercises_for_level(level)
    else:
        exercises = all_exercises()

    return {
        "level_meta": LEVEL_META,
        "count": len(exercises),
        "exercises": [
            {
                "id": e.exercise_id,
                "level": e.level,
                "title": e.title,
                "stack": e.stack,
                "github_title": e.github_title(),
            }
            for e in exercises
        ],
    }


@router.post("/sync")
def academy_sync() -> dict[str, Any]:
    """Sync GitHub → progress JSON + fermer issues agent-done."""
    from services.academy_issue_sync import run_academy_sync

    return run_academy_sync()


@router.get("/gate")
def academy_gate() -> dict[str, Any]:
    """Évalue la gate produit (Academy → Lounge, pas NUAWAY)."""
    from services.nuaway_gate import evaluate_nuaway_gate

    return evaluate_nuaway_gate(refresh_academy=True)


@router.post("/seed")
def academy_seed(body: AcademySeedRequest) -> dict[str, Any]:
    """Crée les issues GitHub pour un niveau (idempotent)."""
    from services.academy_seed import seed_level

    try:
        return seed_level(
            body.level,
            dry_run=body.dry_run,
            mark_first_ready=body.mark_first_ready,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/sprint")
def academy_sprint(body: AcademySprintRequest) -> dict[str, Any]:
    """Lance un sprint : seed optionnel + label agent-ready sur N issues."""
    from services.academy_seed import run_academy_sprint

    try:
        return run_academy_sprint(
            level=body.level,
            seed_if_missing=body.seed_if_missing,
            mark_ready_count=body.mark_ready_count,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
