"""Review Chain — AUTO → BOARD → POLICY → INTEGRATE → DONE (DEC-025)."""

from __future__ import annotations

import logging
from typing import Any

from services.review_chain_gates import (
    AutoCheckFn,
    run_auto_gates,
    run_board_gate,
    run_policy_gate,
)
from services.review_chain_integrate import IntegrateFn, needs_integrate, run_integrate
from services.review_chain_models import (
    GateResult,
    ReviewChainResult,
    _now_iso,
    new_chain_id,
)

logger = logging.getLogger(__name__)


def _emit(event_type: str, payload: dict[str, Any]) -> None:
    try:
        from services.event_bus import emit

        emit(event_type, payload=payload, source_agent="review_chain")
    except Exception:
        pass


def run_review_chain(
    *,
    department: str = "default",
    artifact: dict[str, Any] | None = None,
    producer_agent_id: str | None = None,
    merge_agent_id: str = "dev_integrator",
    target_branch: str = "staging",
    repo_slug: str | None = None,
    repo_path: str | None = None,
    feature_branches: list[str] | None = None,
    integration_branch: str | None = None,
    auto_checks: list[AutoCheckFn] | None = None,
    auto_preapproved: bool = False,
    board_preapproved: bool = False,
    skip_board: bool = False,
    human_approved: bool = False,
    dry_run: bool = False,
    integrate_fn: IntegrateFn | None = None,
) -> ReviewChainResult:
    """Ordered Review Chain. Auto always before board/human (AAF ADR-012)."""
    started = _now_iso()
    chain_id = new_chain_id()
    art = dict(artifact or {})
    if producer_agent_id and "producer_agent_id" not in art:
        art["producer_agent_id"] = producer_agent_id
    feedback: list[str] = []
    gates: list[GateResult] = []
    merge_mode = ""
    integrate_meta: dict[str, Any] | None = None

    _emit("review_chain.started", {"chain_id": chain_id, "department": department})

    auto = run_auto_gates(
        auto_checks,
        preapproved=auto_preapproved,
    )
    gates.append(auto)
    if auto.outcome == "fail":
        if auto.feedback:
            feedback.append(auto.feedback)
        result = ReviewChainResult(
            chain_id=chain_id,
            status="REJECTED",
            gates=gates,
            feedback_log=feedback,
            started_at=started,
            finished_at=_now_iso(),
        )
        _emit("review_chain.completed", result.to_dict())
        return result

    board = run_board_gate(
        department=department,
        artifact=art,
        producer_agent_id=producer_agent_id,
        skip=skip_board,
        preapproved=board_preapproved,
    )
    gates.append(board)
    if board.outcome == "fail":
        if board.feedback:
            feedback.append(board.feedback)
        result = ReviewChainResult(
            chain_id=chain_id,
            status="REJECTED",
            gates=gates,
            feedback_log=feedback,
            started_at=started,
            finished_at=_now_iso(),
        )
        _emit("review_chain.completed", result.to_dict())
        return result

    policy = run_policy_gate(
        agent_id=merge_agent_id,
        target_branch=target_branch,
        repo_slug=repo_slug,
        department=department,
        producer_agent_id=producer_agent_id,
        human_approved=human_approved,
    )
    gates.append(policy)
    merge_mode = str((policy.meta or {}).get("mode") or "")
    if policy.outcome == "fail":
        if policy.feedback:
            feedback.append(policy.feedback)
        result = ReviewChainResult(
            chain_id=chain_id,
            status="BLOCKED_POLICY",
            gates=gates,
            feedback_log=feedback,
            merge_mode=merge_mode or "deny",
            started_at=started,
            finished_at=_now_iso(),
        )
        _emit("review_chain.completed", result.to_dict())
        return result
    if policy.outcome == "human_required":
        result = ReviewChainResult(
            chain_id=chain_id,
            status="A_VERIFIER",
            gates=gates,
            feedback_log=feedback,
            merge_mode="human_required",
            started_at=started,
            finished_at=_now_iso(),
        )
        _emit("review_chain.completed", result.to_dict())
        return result

    branches = [b for b in (feature_branches or []) if b]
    if needs_integrate(branches):
        if not repo_path and not dry_run and integrate_fn is None:
            g = GateResult(
                gate="INTEGRATE",
                outcome="fail",
                detail="repo_path required for integrate",
                feedback="Cannot integrate without repo_path",
            )
            gates.append(g)
            feedback.append(g.feedback)
            result = ReviewChainResult(
                chain_id=chain_id,
                status="INTEGRATE_FAILED",
                gates=gates,
                feedback_log=feedback,
                merge_mode=merge_mode,
                started_at=started,
                finished_at=_now_iso(),
            )
            _emit("review_chain.completed", result.to_dict())
            return result
        integ = run_integrate(
            repo_path=repo_path or "",
            integration_branch=integration_branch or f"integrate/{chain_id}",
            feature_branches=branches,
            base_branch=target_branch,
            dry_run=dry_run,
            integrate_fn=integrate_fn,
        )
        gates.append(integ)
        integrate_meta = (integ.meta or {}).get("integrate")
        if integ.outcome == "fail":
            if integ.feedback:
                feedback.append(integ.feedback)
            result = ReviewChainResult(
                chain_id=chain_id,
                status="INTEGRATE_FAILED",
                gates=gates,
                feedback_log=feedback,
                merge_mode=merge_mode,
                integrate=integrate_meta,
                started_at=started,
                finished_at=_now_iso(),
            )
            _emit("review_chain.completed", result.to_dict())
            return result
    else:
        gates.append(
            GateResult(
                gate="INTEGRATE",
                outcome="skip",
                detail="single branch — integrate not required",
            )
        )

    gates.append(GateResult(gate="DONE", outcome="pass", detail="chain approved"))
    result = ReviewChainResult(
        chain_id=chain_id,
        status="APPROVED",
        gates=gates,
        feedback_log=feedback,
        merge_mode=merge_mode or "auto",
        integrate=integrate_meta,
        started_at=started,
        finished_at=_now_iso(),
    )
    _emit("review_chain.completed", result.to_dict())
    return result


def staging_trust_min() -> float:
    try:
        from config.settings import get_settings

        return float(getattr(get_settings(), "review_chain_staging_trust_min", 0.70))
    except Exception:
        return 0.70


__all__ = [
    "run_review_chain",
    "staging_trust_min",
]
