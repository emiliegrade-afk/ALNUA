"""Academies API — generic program registry endpoints (SPEC_STUDIO_ACADEMIES / DEC-036).

One generic surface for every academy program (gaming, robo, comms and the
49.4 drills: analytics, finance, rnd). The per-department routers
(``/gaming-academy/*`` etc.) predate the program registry and stay untouched;
new programs only need an ``AcademyProgram`` entry — no new router file.
"""

from __future__ import annotations

import importlib

from api.route_common import *  # noqa: F403

router = APIRouter(prefix="/academies", tags=["academies"])


def _get_program_or_404(program_id: str):
    from services.studio_academy_program import get_program

    try:
        return get_program(program_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Programme académie inconnu: {program_id}") from None


def _runner(program):
    return importlib.import_module(program.runner_module)


@router.get("")
def academies_list() -> dict[str, Any]:
    """Vue CEO : tous les programmes académie avec progression compacte."""
    from services.studio_academy_program import all_programs

    programs = []
    for program in all_programs():
        status = _runner(program).studio_status()
        programs.append(
            {
                "program": status["program"],
                "title": program.title,
                "subject": status["subject"],
                "completed": status["completed"],
                "failed": status["failed"],
                "total": status["total"],
                "success_rate_pct": status["success_rate_pct"],
                "next_exercise": status["next_exercise"],
            }
        )
    return {"count": len(programs), "programs": programs}


@router.get("/{program_id}/status")
def academies_status(program_id: str) -> dict[str, Any]:
    """Snapshot CEO : progression, niveaux, gate, prochain exercice."""
    program = _get_program_or_404(program_id)
    return _runner(program).studio_status()


@router.get("/{program_id}/curriculum")
def academies_curriculum(program_id: str, level: int | None = None) -> dict[str, Any]:
    """Liste des exercices (tous ou filtrés par niveau), avec état courant."""
    from services.studio_academy_program import exercise_sort_key
    from services.studio_academy_state import load_progress

    program = _get_program_or_404(program_id)
    states = load_progress(program).get("exercises") or {}
    exercises = [e for e in sorted(program.exercises(), key=exercise_sort_key) if level is None or e.level == level]
    return {
        "levels": program.level_meta,
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


@router.get("/{program_id}/gate")
def academies_gate(program_id: str) -> dict[str, Any]:
    """Évalue (et persiste) les critères de gate du programme."""
    from services.studio_academy_gate import evaluate_gate

    return evaluate_gate(_get_program_or_404(program_id))


@router.post("/{program_id}/run-next")
def academies_run_next(program_id: str) -> dict[str, Any]:
    """Trigger CEO manuel — exécute le prochain exercice en attente (agent + QA)."""
    program = _get_program_or_404(program_id)
    return _runner(program).run_next_exercise()


@router.post("/{program_id}/run/{exercise_id}")
def academies_run(program_id: str, exercise_id: str) -> dict[str, Any]:
    """Trigger ciblé sur un exercice précis. Idempotent sur états terminaux."""
    program = _get_program_or_404(program_id)
    return _runner(program).run_exercise(exercise_id)
