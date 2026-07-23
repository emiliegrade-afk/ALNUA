"""Workflow engine routes — Company OS recipes."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

from typing import Any

from pydantic import BaseModel, Field

router = APIRouter(prefix="/workflows", tags=["workflows"])


class WorkflowRunRequest(BaseModel):
    recipe_id: str = Field(..., min_length=1, max_length=64)
    context: dict[str, Any] = Field(default_factory=dict)


@router.get("/recipes")
def workflows_list_recipes() -> list[dict[str, Any]]:
    from services.workflow_engine import list_recipes

    return list_recipes()


@router.get("/runs")
def workflows_list_runs(
    limit: int = 30,
    recipe_id: str | None = None,
) -> dict[str, Any]:
    from services.workflow_engine import list_runs

    return {"runs": list_runs(limit=min(limit, 100), recipe_id=recipe_id)}


@router.get("/runs/{run_id}")
def workflows_get_run(run_id: str) -> dict[str, Any]:
    from services.workflow_engine import get_run

    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run introuvable")
    return run.model_dump()


@router.post("/run")
def workflows_run(body: WorkflowRunRequest) -> dict[str, Any]:
    """Execute a workflow recipe (dossier_ceo, ship_app, run_ops, explore)."""
    from services.workflow_engine import run_workflow

    return run_workflow(body.recipe_id, body.context)


@router.post("/ops/run")
def workflows_run_ops() -> dict[str, Any]:
    """RUN ops now (autonomous — CEO keeps product decisions)."""
    from services.workflow_scheduler import run_scheduled_ops

    return run_scheduled_ops(auto_remediate=True)


@router.post("/semaine/run")
def workflows_run_semaine() -> dict[str, Any]:
    from services.workflow_scheduler import run_scheduled_semaine

    return run_scheduled_semaine(weekly_plan=True)


class ShipReleaseRequest(BaseModel):
    slug: str = Field(..., min_length=1, max_length=64)
    target_status: str = "beta"


@router.post("/ship/game")
def workflows_ship_game(body: ShipReleaseRequest) -> dict[str, Any]:
    """Release jeu — registry gaming + GDD/Godot readiness."""
    from services.workflow_engine import run_workflow

    return run_workflow(
        "ship_game",
        {"slug": body.slug, "target_status": body.target_status},
    )


@router.post("/ship/robo")
def workflows_ship_robo(body: ShipReleaseRequest) -> dict[str, Any]:
    """Release robotique — registry robotics + BOM/hardware readiness."""
    from services.workflow_engine import run_workflow

    return run_workflow(
        "ship_robo",
        {"slug": body.slug, "target_status": body.target_status},
    )


@router.get("/watchdog/coverage")
def workflows_watchdog_coverage() -> dict[str, Any]:
    """RUN ops — registry ↔ watchdog mapping report."""
    from services.run_watchdog_registry import build_watchdog_coverage_report

    return build_watchdog_coverage_report()
