"""Workflow step handlers — mission_ship / review chain (DEC-025)."""

from __future__ import annotations

from typing import Any


def _step_review_chain(ctx: dict[str, Any]) -> dict[str, Any]:
    """Run full Review Chain from workflow context (dry_run default True)."""
    from services.review_chain import run_review_chain

    branches = list(ctx.get("feature_branches") or [])
    result = run_review_chain(
        department=str(ctx.get("department") or ctx.get("slug") or "default"),
        artifact={
            "title": str(ctx.get("title") or ctx.get("slug") or "mission_ship"),
            "body": str(ctx.get("summary") or ctx.get("objective") or "Review chain ship"),
            "status": "to_review",
            "project_id": ctx.get("slug") or ctx.get("project_id"),
        },
        producer_agent_id=ctx.get("producer_agent_id") or ctx.get("head_agent"),
        merge_agent_id=str(ctx.get("merge_agent_id") or "dev_integrator"),
        target_branch=str(ctx.get("target_branch") or "staging"),
        repo_slug=ctx.get("repo_slug") or ctx.get("slug"),
        repo_path=ctx.get("repo_path"),
        feature_branches=branches,
        integration_branch=ctx.get("integration_branch"),
        auto_preapproved=bool(ctx.get("auto_preapproved", True)),
        board_preapproved=bool(ctx.get("board_preapproved", False)),
        skip_board=bool(ctx.get("skip_board", False)),
        human_approved=bool(ctx.get("human_approved", False)),
        dry_run=bool(ctx.get("dry_run", True)),
    )
    payload = result.to_dict()
    # Share chain outcome with later steps (require_integrate).
    ctx["_review_chain"] = payload
    if result.status == "APPROVED":
        gates = {g.get("gate"): g for g in (payload.get("gates") or []) if isinstance(g, dict)}
        integ = gates.get("INTEGRATE") or {}
        if integ.get("outcome") in {"pass", "skip"} or ctx.get("dry_run"):
            ctx["integrate_done"] = True
        return {"status": "OK", "detail": "review chain approved", "result": payload, "gaps": []}
    if result.status == "A_VERIFIER":
        return {
            "status": "A_VERIFIER",
            "detail": "human approval required before merge",
            "result": payload,
            "gaps": ["review_chain.human"],
        }
    if result.status == "BLOCKED_POLICY":
        return {
            "status": "ECART",
            "detail": "merge policy blocked",
            "result": payload,
            "gaps": ["review_chain.policy"],
            "feedback": (result.feedback_log[-1] if result.feedback_log else "policy"),
        }
    if result.status == "INTEGRATE_FAILED":
        return {
            "status": "RETRYABLE",
            "detail": "integrate failed",
            "result": payload,
            "gaps": ["review_chain.integrate"],
            "feedback": (result.feedback_log[-1] if result.feedback_log else "integrate"),
        }
    return {
        "status": "ECART",
        "detail": f"review chain {result.status}",
        "result": payload,
        "gaps": ["review_chain.rejected"],
        "feedback": (result.feedback_log[-1] if result.feedback_log else result.status),
    }


def _step_require_integrate(ctx: dict[str, Any]) -> dict[str, Any]:
    """ECART if N>1 feature branches but integrate not marked done."""
    branches = [b for b in (ctx.get("feature_branches") or []) if b]
    if len(branches) <= 1:
        return {
            "status": "OK",
            "detail": "integrate not required (≤1 branch)",
            "gaps": [],
            "result": {"branches": branches},
        }
    if ctx.get("integrate_done") or ctx.get("dry_run"):
        return {
            "status": "OK",
            "detail": "integrate acknowledged",
            "gaps": [],
            "result": {"branches": branches},
        }
    prior = ctx.get("_review_chain") or {}
    if prior.get("status") == "APPROVED" and prior.get("integrate"):
        return {
            "status": "OK",
            "detail": "integrate from review chain",
            "gaps": [],
            "result": prior.get("integrate"),
        }
    return {
        "status": "ECART",
        "detail": f"{len(branches)} feature branches require integrate",
        "gaps": ["integrate.required"],
        "feedback": "Call review_chain with feature_branches or set integrate_done",
    }
