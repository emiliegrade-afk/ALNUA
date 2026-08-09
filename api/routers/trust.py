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
