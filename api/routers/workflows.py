"""Workflow engine routes — Company OS recipes."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

from typing import Any

from pydantic import BaseModel, Field

router = APIRouter(prefix="/workflows", tags=["workflows"])


class WorkflowRunRequest(BaseModel):
    recipe_id: str = Field(..., min_length=1, max_length=64)
    context: dict[str, Any] = Field(default_factory=dict)


class WorkflowAbortRequest(BaseModel):
    agent_id: str = Field(default="coo", min_length=1, max_length=64)
    reason: str = Field(default="", max_length=400)


class WorkflowApproveStepRequest(BaseModel):
    step_id: str = Field(..., min_length=1, max_length=64)
    approver_agent_id: str = Field(default="ceo", min_length=1, max_length=64)


@router.get("/recipes")
def workflows_list_recipes() -> list[dict[str, Any]]:
    from services.workflow_engine import list_recipes

    return list_recipes()


@router.get("/runs")
def workflows_list_runs(
    limit: int = 30,
    recipe_id: str | None = None,
    waiting: str | None = None,
) -> dict[str, Any]:
    from services.workflow_engine import list_runs

    waiting_a_verifier = (waiting or "").strip().lower() == "a_verifier"
    return {
        "runs": list_runs(
            limit=min(limit, 100),
            recipe_id=recipe_id,
            waiting_a_verifier=waiting_a_verifier,
        )
    }


@router.get("/runs/{run_id}")
def workflows_get_run(run_id: str) -> dict[str, Any]:
    from services.workflow_engine import get_run

    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run introuvable")
    return run.model_dump()


@router.post("/runs/{run_id}/abort")
def workflows_abort_run(run_id: str, body: WorkflowAbortRequest | None = None) -> dict[str, Any]:
    from services.input_sanitizer import sanitize_user_input
    from services.workflow_engine import abort_workflow_run, get_run

    if not get_run(run_id):
        raise HTTPException(status_code=404, detail="Run introuvable")
    req = body or WorkflowAbortRequest()
    reason = sanitize_user_input(req.reason, redact_pii_enabled=False)[:400]
    result = abort_workflow_run(run_id, agent_id=req.agent_id, reason=reason)
    if result.get("error") == "capability_denied":
        raise HTTPException(status_code=403, detail=result.get("detail") or "capability denied")
    return result


@router.post("/runs/{run_id}/approve-step")
def workflows_approve_step(
    run_id: str,
    body: WorkflowApproveStepRequest,
) -> dict[str, Any]:
    """CEO approves an A_VERIFIER step and continues the workflow run."""
    from services.workflow_engine import approve_workflow_step, get_run

    if not get_run(run_id):
        raise HTTPException(status_code=404, detail="Run introuvable")
    result = approve_workflow_step(
        run_id,
        body.step_id,
        approver_agent_id=body.approver_agent_id,
    )
    if result.get("error") == "not_found":
        raise HTTPException(status_code=404, detail="Run introuvable")
    if result.get("error") == "step_not_found":
        raise HTTPException(status_code=404, detail=f"Step introuvable : {body.step_id}")
    if result.get("error") in {"not_a_verifier", "still_a_verifier", "handler_missing"}:
        raise HTTPException(
            status_code=409,
            detail=result.get("detail") or result.get("error"),
        )
    if result.get("error") == "step_ecart":
        raise HTTPException(status_code=422, detail=result.get("detail") or "Step ECART")
    return result


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


@router.get("/idle/queue")
def workflows_idle_queue() -> dict[str, Any]:
    """File du jour idle (DEC-021)."""
    from services.idle_work_queue import load_queue

    return load_queue()


class IdleValidateRequest(BaseModel):
    validated: bool = True


@router.post("/idle/validate")
def workflows_idle_validate(body: IdleValidateRequest) -> dict[str, Any]:
    """CEO valide la file du jour → débloque items L2."""
    from services.idle_work_queue import validate_day_queue

    return validate_day_queue(validated=body.validated)


@router.post("/idle/plan")
def workflows_idle_plan() -> dict[str, Any]:
    from services.workflow_scheduler import run_scheduled_idle_plan

    return run_scheduled_idle_plan()


@router.post("/idle/drain")
def workflows_idle_drain() -> dict[str, Any]:
    from services.workflow_scheduler import run_scheduled_idle_drain

    return run_scheduled_idle_drain()


@router.get("/idle/deliverables")
def workflows_idle_deliverables(limit: int = 30) -> dict[str, Any]:
    from services.idle_work_deliverables import list_deliverables

    return {"deliverables": list_deliverables(limit=limit)}


@router.get("/idle/deliverables/{item_id}")
def workflows_idle_deliverable(item_id: str) -> dict[str, Any]:
    from services.idle_work_deliverables import get_deliverable

    data = get_deliverable(item_id)
    if not data:
        raise HTTPException(status_code=404, detail="Livrable idle introuvable")
    return data


class IdlePromoteRequest(BaseModel):
    item_id: str | None = None
    project_id: str | None = None
    dry_run: bool = False


@router.post("/idle/promote-tickets")
def workflows_idle_promote_tickets(body: IdlePromoteRequest) -> dict[str, Any]:
    """Crée des tickets Hub [idle-ok] depuis un triage L1 (sans LLM)."""
    from services.idle_work_deliverables import promote_triage_to_tickets

    return promote_triage_to_tickets(
        item_id=body.item_id,
        project_id=body.project_id,
        dry_run=body.dry_run,
    )
