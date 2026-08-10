"""Review Chain gate helpers — AUTO / BOARD / POLICY (DEC-025)."""

from __future__ import annotations

from typing import Any, Callable

from services.review_chain_models import GateResult


AutoCheckFn = Callable[[], GateResult]


def run_auto_gates(
    checks: list[AutoCheckFn] | None,
    *,
    preapproved: bool = False,
    preapproved_detail: str = "auto gates pre-satisfied",
) -> GateResult:
    """Fail-fast AUTO stage. preapproved=True when caller already ran tests/QA."""
    if preapproved:
        return GateResult(
            gate="AUTO",
            outcome="pass",
            detail=preapproved_detail,
            meta={"preapproved": True},
        )
    for fn in checks or []:
        result = fn()
        result.gate = "AUTO"
        if result.outcome == "fail":
            return result
    if not checks:
        return GateResult(
            gate="AUTO",
            outcome="pass",
            detail="no auto checks registered",
            meta={"empty": True},
        )
    return GateResult(gate="AUTO", outcome="pass", detail="all auto checks passed")


def run_board_gate(
    *,
    department: str,
    artifact: dict[str, Any],
    producer_agent_id: str | None,
    skip: bool = False,
    preapproved: bool = False,
    preapproved_detail: str = "board pre-satisfied (QA/Spec)",
) -> GateResult:
    if skip or preapproved:
        return GateResult(
            gate="BOARD",
            outcome="pass" if preapproved or skip else "skip",
            detail=preapproved_detail if preapproved else "board skipped",
            meta={"preapproved": preapproved, "skipped": skip},
        )
    from services.review_board import evaluate_submission

    board = evaluate_submission(
        department=department or "default",
        artifact=artifact,
        producer_agent_id=producer_agent_id,
        record_trust=True,
    )
    ok = bool(board.get("gate_open"))
    rec = str(board.get("recommendation") or "")
    detail = f"score={board.get('score')} rec={rec}"
    feedback = ""
    if not ok:
        fails = [
            c.get("id")
            for c in (board.get("checks") or [])
            if isinstance(c, dict) and not c.get("ok")
        ]
        feedback = f"Board rejected: {', '.join(str(x) for x in fails) or detail}"
    return GateResult(
        gate="BOARD",
        outcome="pass" if ok else "fail",
        detail=detail,
        feedback=feedback,
        meta={"board": board},
    )


def run_policy_gate(
    *,
    agent_id: str,
    target_branch: str,
    repo_slug: str | None,
    department: str | None,
    producer_agent_id: str | None,
    human_approved: bool,
) -> GateResult:
    from services.merge_policy import assert_can_merge, merge_autonomy, MergeDeniedError

    # Autonomy first (main → human) so capability deny does not mask A_VERIFIER.
    autonomy = merge_autonomy(
        target_branch,
        repo_slug=repo_slug,
        department=department,
        producer_agent_id=producer_agent_id,
        actor_agent_id=agent_id,
        human_approved=human_approved,
    )
    mode = str(autonomy.get("mode") or "deny")
    if mode == "deny":
        return GateResult(
            gate="POLICY",
            outcome="fail",
            detail=str(autonomy.get("reason") or "denied"),
            feedback=str(autonomy.get("reason") or "merge denied by autonomy"),
            meta=autonomy,
        )
    if mode == "human_required":
        return GateResult(
            gate="POLICY",
            outcome="human_required",
            detail=str(autonomy.get("reason") or "human required"),
            feedback="",
            meta=autonomy,
        )

    try:
        assert_can_merge(
            agent_id,
            target_branch,
            repo_slug=repo_slug,
            human_approved=human_approved,
        )
    except MergeDeniedError as exc:
        return GateResult(
            gate="POLICY",
            outcome="fail",
            detail=str(exc),
            feedback=str(exc),
            meta={"reason": "actor_or_capability_denied", **autonomy},
        )

    return GateResult(
        gate="POLICY",
        outcome="pass",
        detail=str(autonomy.get("reason") or "auto"),
        meta=autonomy,
    )
