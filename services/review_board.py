"""Generic Review Board — Phase 32 MVP (DEC-013).

Generalizes the *gate* idea from academy_gate / rnd_council without requiring
a live multi-agent debate. Structural quality gates + optional producer trust.
"""

from __future__ import annotations

from typing import Any

from config.quality_gates import evaluate_gate
from services.agent_trust import get_trust, record_validation


def evaluate_submission(
    *,
    department: str,
    artifact: dict[str, Any],
    producer_agent_id: str | None = None,
    record_trust: bool = True,
    reviewers: list[str] | None = None,
) -> dict[str, Any]:
    """
    Returns gate decision for a department artifact.

    reviewers is accepted for API compatibility with future LLM boards;
    MVP does not call LLMs (honest structural score only).
    """
    gate = evaluate_gate(department, artifact)
    producer = (producer_agent_id or artifact.get("producer_agent_id") or "").strip() or None
    trust_before = get_trust(producer) if producer else None

    recommendation = "approve" if gate["gate_open"] else "revise"
    if record_trust and producer:
        trust_after = record_validation(
            producer,
            success=bool(gate["gate_open"]),
            weight=1.0,
            note=f"review_board:{department}:{recommendation}",
            source="review_board",
        )
    else:
        trust_after = trust_before

    return {
        "department": department,
        "gate_open": gate["gate_open"],
        "score": gate["score"],
        "threshold": gate["threshold"],
        "recommendation": recommendation,
        "checks": gate["checks"],
        "reviewers": reviewers or ["quality_gates"],
        "producer_agent_id": producer,
        "trust_before": trust_before,
        "trust_after": trust_after,
        "deliberated": False,
        "mode": "structural_mvp",
    }
