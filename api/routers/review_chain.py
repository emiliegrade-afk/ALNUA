"""Review Chain API — Phase D (DEC-025)."""

from __future__ import annotations

from typing import Any

from api.route_common import *  # noqa: F403
from pydantic import BaseModel, Field

router = APIRouter(tags=["review-chain"])


class ReviewChainRunBody(BaseModel):
    department: str = Field(default="default", max_length=64)
    artifact: dict[str, Any] = Field(default_factory=dict)
    producer_agent_id: str | None = Field(default=None, max_length=64)
    merge_agent_id: str = Field(default="dev_integrator", max_length=64)
    target_branch: str = Field(default="staging", max_length=128)
    repo_slug: str | None = Field(default=None, max_length=128)
    repo_path: str | None = Field(default=None, max_length=512)
    feature_branches: list[str] = Field(default_factory=list)
    integration_branch: str | None = Field(default=None, max_length=128)
    auto_preapproved: bool = False
    board_preapproved: bool = False
    skip_board: bool = False
    human_approved: bool = False
    dry_run: bool = True


@router.get("/review-chain/defaults")
def review_chain_defaults() -> dict[str, Any]:
    from services.merge_policy import merge_autonomy
    from services.review_chain import staging_trust_min

    try:
        from config.settings import get_settings

        s = get_settings()
        thr = float(s.review_chain_staging_trust_min)
    except Exception:
        thr = staging_trust_min()
    return {
        "staging_trust_min": thr,
        "order": ["AUTO", "BOARD", "POLICY", "INTEGRATE", "DONE"],
        "human_departments": ["ads", "finances", "publish"],
        "examples": {
            "main": merge_autonomy("main"),
            "staging": merge_autonomy("staging", producer_agent_id="dev_app"),
            "academy": merge_autonomy("staging", repo_slug="academy"),
        },
    }


@router.post("/review-chain/run")
def review_chain_run(body: ReviewChainRunBody) -> dict[str, Any]:
    from services.input_sanitizer import sanitize_user_input
    from services.review_chain import run_review_chain

    dept = sanitize_user_input(body.department, redact_pii_enabled=False)[:64]
    producer = (
        sanitize_user_input(body.producer_agent_id, redact_pii_enabled=False)[:64]
        if body.producer_agent_id
        else None
    )
    merge_agent = sanitize_user_input(body.merge_agent_id, redact_pii_enabled=False)[:64]
    target = sanitize_user_input(body.target_branch, redact_pii_enabled=False)[:128]
    branches = [
        sanitize_user_input(b, redact_pii_enabled=False)[:128]
        for b in (body.feature_branches or [])
        if b
    ]
    result = run_review_chain(
        department=dept,
        artifact=body.artifact,
        producer_agent_id=producer,
        merge_agent_id=merge_agent or "dev_integrator",
        target_branch=target or "staging",
        repo_slug=body.repo_slug,
        repo_path=body.repo_path,
        feature_branches=branches,
        integration_branch=body.integration_branch,
        auto_preapproved=body.auto_preapproved,
        board_preapproved=body.board_preapproved,
        skip_board=body.skip_board,
        human_approved=body.human_approved,
        dry_run=body.dry_run,
    )
    return result.to_dict()
