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

    reviewers: optional; if omitted, resolved from config.review_board_recipes.
    Brand / content_company reviewers run structural brand coherence (Phase 35).
    """
    from config.review_board_recipes import resolve_reviewers

    resolved = resolve_reviewers(department, reviewers)
    gate = evaluate_gate(department, artifact)
    checks = list(gate.get("checks") or [])
    score = float(gate.get("score") or 0)
    gate_open = bool(gate.get("gate_open"))

    brand_review: dict[str, Any] | None = None
    if any(r in ("brand", "content_company") for r in resolved):
        try:
            from services.brand_design_system import artifact_text, review_brand_coherence

            brand_review = review_brand_coherence(
                artifact_text(artifact),
                department=department,
            )
            checks.append(
                {
                    "id": "brand_coherence",
                    "ok": brand_review.get("ok"),
                    "flags": brand_review.get("flags"),
                    "reviewer": "brand",
                }
            )
            if not brand_review.get("ok"):
                gate_open = False
                # Quality gates are 0–100; brand fail soft-penalizes without zeroing.
                score = min(score, max(0.0, score - 15.0))
        except Exception as exc:
            checks.append({"id": "brand_coherence", "ok": False, "error": str(exc)[:200]})

    producer = (producer_agent_id or artifact.get("producer_agent_id") or "").strip() or None
    trust_before = get_trust(producer) if producer else None

    recommendation = "approve" if gate_open else "revise"
    if record_trust and producer:
        trust_after = record_validation(
            producer,
            success=bool(gate_open),
            weight=1.0,
            note=f"review_board:{department}:{recommendation}",
            source="review_board",
        )
    else:
        trust_after = trust_before

    result: dict[str, Any] = {
        "department": department,
        "gate_open": gate_open,
        "score": round(score, 4),
        "threshold": gate["threshold"],
        "recommendation": recommendation,
        "checks": checks,
        "reviewers": resolved,
        "producer_agent_id": producer,
        "trust_before": trust_before,
        "trust_after": trust_after,
        "deliberated": False,
        "mode": "structural_mvp",
        "brand_review": brand_review,
    }

    # Vague 3 — optional LLM debate behind REVIEW_BOARD_LLM (default off).
    try:
        from services.review_board_llm import run_optional_debate

        debate = run_optional_debate(
            department=department,
            artifact=artifact,
            gate=gate,
            reviewers=reviewers,
        )
        if debate:
            result.update(debate)
            verdict = (debate.get("debate") or {}).get("verdict")
            if verdict in ("approve", "revise"):
                result["recommendation"] = verdict
                result["gate_open"] = verdict == "approve"
    except Exception:
        pass

    return result
