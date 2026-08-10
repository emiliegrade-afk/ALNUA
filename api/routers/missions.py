"""Mission Graph API — Phase B (DEC-023)."""

from __future__ import annotations

from typing import Any

from api.route_common import *  # noqa: F403
from pydantic import BaseModel, Field

router = APIRouter(tags=["missions"])


class MissionTaskIn(BaseModel):
    task_id: str = Field(..., min_length=1, max_length=64)
    description: str = Field(default="", max_length=500)
    agent_id: str = Field(..., min_length=1, max_length=64)
    method: str = Field(..., min_length=1, max_length=64)
    kwargs: dict[str, Any] = Field(default_factory=dict)
    depends_on: list[str] = Field(default_factory=list)
    lock_keys: list[str] = Field(default_factory=list)
    repo_slug: str = ""
    repo_path: str = ""
    project_id: str | None = None


class MissionCreateRequest(BaseModel):
    """Create from objective (COO decompose) OR explicit title+tasks."""

    objective: str | None = Field(default=None, max_length=2000)
    context: str = Field(default="", max_length=4000)
    title: str | None = Field(default=None, max_length=200)
    tasks: list[MissionTaskIn] | None = None
    run: bool = False
    max_concurrent: int = Field(default=4, ge=1, le=8)
    stop_on_failure: bool = False


class MissionFromPlanRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    objective: str = Field(default="", max_length=2000)
    context: str = Field(default="", max_length=4000)
    steps: list[MissionTaskIn] = Field(..., min_length=1)
    run: bool = False
    max_concurrent: int = Field(default=4, ge=1, le=8)
    stop_on_failure: bool = False


class MissionRunRequest(BaseModel):
    max_concurrent: int = Field(default=4, ge=1, le=8)
    stop_on_failure: bool = False
    max_retries: int = Field(default=2, ge=0, le=3)


class MissionAbortRequest(BaseModel):
    agent_id: str = Field(default="coo", min_length=1, max_length=64)
    reason: str = Field(default="", max_length=400)


@router.get("/missions")
def missions_list(
    limit: int = Query(default=30, ge=1, le=100),
    status: str | None = Query(default=None),
) -> dict[str, Any]:
    from services.mission_graph import list_missions

    return {"missions": list_missions(limit=limit, status=status)}


@router.get("/missions/{mission_id}")
def missions_get(mission_id: str) -> dict[str, Any]:
    from services.mission_graph import get_mission

    m = get_mission(mission_id)
    if not m:
        raise HTTPException(status_code=404, detail="Mission not found")
    return m.to_dict()


@router.post("/missions")
def missions_create(body: MissionCreateRequest) -> dict[str, Any]:
    from services.input_sanitizer import sanitize_user_input
    from services.mission_graph import (
        get_mission,
        mission_from_objective,
        mission_from_steps,
        run_mission,
    )

    if body.tasks:
        title = sanitize_user_input(body.title or body.objective or "Mission", redact_pii_enabled=False)[
            :200
        ]
        mission = mission_from_steps(
            title=title,
            objective=sanitize_user_input(body.objective or title, redact_pii_enabled=False)[:2000],
            context=sanitize_user_input(body.context, redact_pii_enabled=False)[:4000],
            tasks=[t.model_dump() for t in body.tasks],
            source="manual",
        )
    elif body.objective and body.objective.strip():
        mission = mission_from_objective(
            sanitize_user_input(body.objective, redact_pii_enabled=False)[:2000],
            sanitize_user_input(body.context, redact_pii_enabled=False)[:4000],
        )
    else:
        raise HTTPException(
            status_code=400,
            detail="Provide objective (COO decompose) or title+tasks",
        )

    if body.run:
        run_result = run_mission(
            mission.mission_id,
            max_concurrent=body.max_concurrent,
            stop_on_failure=body.stop_on_failure,
        )
        fresh = get_mission(mission.mission_id)
        return {"mission": fresh.to_dict() if fresh else mission.to_dict(), "run": run_result}
    return {"mission": mission.to_dict()}


@router.post("/missions/from-plan")
def missions_from_plan(body: MissionFromPlanRequest) -> dict[str, Any]:
    from services.input_sanitizer import sanitize_user_input
    from services.mission_graph import get_mission, mission_from_steps, run_mission

    mission = mission_from_steps(
        title=sanitize_user_input(body.title, redact_pii_enabled=False)[:200],
        objective=sanitize_user_input(body.objective or body.title, redact_pii_enabled=False)[:2000],
        context=sanitize_user_input(body.context, redact_pii_enabled=False)[:4000],
        tasks=[t.model_dump() for t in body.steps],
        source="from_plan",
    )
    if body.run:
        run_result = run_mission(
            mission.mission_id,
            max_concurrent=body.max_concurrent,
            stop_on_failure=body.stop_on_failure,
        )
        fresh = get_mission(mission.mission_id)
        return {"mission": fresh.to_dict() if fresh else mission.to_dict(), "run": run_result}
    return {"mission": mission.to_dict()}


@router.post("/missions/{mission_id}/run")
def missions_run(mission_id: str, body: MissionRunRequest | None = None) -> dict[str, Any]:
    from services.mission_graph import get_mission, run_mission

    if not get_mission(mission_id):
        raise HTTPException(status_code=404, detail="Mission not found")
    req = body or MissionRunRequest()
    return run_mission(
        mission_id,
        max_concurrent=req.max_concurrent,
        stop_on_failure=req.stop_on_failure,
        max_retries=req.max_retries,
    )


@router.post("/missions/{mission_id}/abort")
def missions_abort(mission_id: str, body: MissionAbortRequest | None = None) -> dict[str, Any]:
    from services.input_sanitizer import sanitize_user_input
    from services.mission_graph import abort_mission, get_mission

    if not get_mission(mission_id):
        raise HTTPException(status_code=404, detail="Mission not found")
    req = body or MissionAbortRequest()
    reason = sanitize_user_input(req.reason, redact_pii_enabled=False)[:400]
    result = abort_mission(mission_id, agent_id=req.agent_id, reason=reason)
    if result.get("error") == "capability_denied":
        raise HTTPException(status_code=403, detail=result.get("detail") or "capability denied")
    return result
