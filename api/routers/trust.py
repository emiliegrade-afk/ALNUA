"""Trust + Review Board + quality gates — Phase 31/32 MVP."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

from typing import Any

from pydantic import BaseModel, Field

router = APIRouter(tags=["trust"])


class ReviewBoardRequest(BaseModel):
    department: str = Field(..., min_length=1, max_length=64)
    artifact: dict[str, Any] = Field(default_factory=dict)
    producer_agent_id: str | None = Field(default=None, max_length=64)
    record_trust: bool = True
    reviewers: list[str] | None = None


@router.get("/agents/trust")
def trust_list(limit: int = Query(default=50, ge=1, le=500)) -> dict[str, Any]:
    from services.agent_trust import list_trust

    return {"agents": list_trust(limit=limit)}


@router.get("/agents/trust/{agent_id}")
def trust_get(agent_id: str) -> dict[str, Any]:
    from services.agent_trust import get_trust

    return get_trust(agent_id)


@router.get("/capabilities")
def capabilities_list() -> dict[str, Any]:
    from config.capability_catalog import list_capabilities

    return {"capabilities": list_capabilities()}


@router.get("/capabilities/packs")
def capabilities_packs() -> dict[str, Any]:
    from config.capability_packs import list_packs

    return {"packs": list_packs()}


@router.get("/capabilities/packs/{agent_id}")
def capabilities_pack_for(agent_id: str) -> dict[str, Any]:
    from config.capability_packs import AGENT_CAPABILITY_PACKS, normalize_agent_id, pack_for
    from services.input_sanitizer import sanitize_user_input

    aid = normalize_agent_id(sanitize_user_input(agent_id, redact_pii_enabled=False)[:64])
    return {
        "agent_id": aid,
        "capabilities": sorted(pack_for(aid)),
        "known": aid in AGENT_CAPABILITY_PACKS,
    }


class PermissionCheckBody(BaseModel):
    agent_id: str = Field(..., min_length=1, max_length=64)
    capability: str = Field(..., min_length=1, max_length=128)
    resource: str | None = Field(default=None, max_length=300)


@router.post("/permission-guard/check")
def permission_guard_check(body: PermissionCheckBody) -> dict[str, Any]:
    from services.input_sanitizer import sanitize_user_input
    from services.permission_guard import check_capability

    return check_capability(
        sanitize_user_input(body.agent_id, redact_pii_enabled=False)[:64],
        sanitize_user_input(body.capability, redact_pii_enabled=False)[:128],
        resource=(
            sanitize_user_input(body.resource, redact_pii_enabled=False)[:300]
            if body.resource
            else None
        ),
        log=True,
    )


@router.get("/trust-graph/recent")
def trust_graph_recent(
    limit: int = Query(default=50, ge=1, le=200),
    agent_id: str | None = None,
    allowed: bool | None = None,
) -> dict[str, Any]:
    from services.input_sanitizer import sanitize_user_input
    from services.trust_graph import list_recent

    aid = (
        sanitize_user_input(agent_id, redact_pii_enabled=False)[:64] if agent_id else None
    )
    return {"decisions": list_recent(limit=limit, agent_id=aid, allowed=allowed)}


@router.get("/mcp-capability-routes")
def mcp_capability_routes() -> dict[str, Any]:
    """Mapped MCP/HTTP routes enforced when X-MCP-Agent is present."""
    from config.mcp_capability_routes import list_mcp_route_rules

    return {"rules": list_mcp_route_rules()}


@router.get("/quality-gates")
def quality_gates_list() -> dict[str, Any]:
    from config.quality_gates import DEPARTMENT_THRESHOLDS

    return {"thresholds": dict(DEPARTMENT_THRESHOLDS)}


@router.post("/review-board/evaluate")
def review_board_evaluate(body: ReviewBoardRequest) -> dict[str, Any]:
    from services.input_sanitizer import sanitize_user_input
    from services.review_board import evaluate_submission

    artifact = dict(body.artifact)
    for key in ("title", "name", "body", "description"):
        if key in artifact and isinstance(artifact[key], str):
            artifact[key] = sanitize_user_input(artifact[key], redact_pii_enabled=False)

    return evaluate_submission(
        department=sanitize_user_input(body.department, redact_pii_enabled=False)[:64],
        artifact=artifact,
        producer_agent_id=body.producer_agent_id,
        record_trust=body.record_trust,
        reviewers=body.reviewers,
    )


@router.get("/cross-dept/queue")
def cross_dept_queue(limit: int = Query(default=50, ge=1, le=200)) -> dict[str, Any]:
    from services.cross_dept_handlers import list_cross_dept_queue

    return {"items": list_cross_dept_queue(limit=limit)}
