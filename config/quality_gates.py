"""Quality gates by department — Phase 32 MVP (DEC-013).

Consumed by workflow validation recipes and the generic review board.
Scores are 0–100; `gate_open` when score >= threshold.
"""

from __future__ import annotations

from typing import Any

# Thresholds from ROADMAP Phase 32 examples (Brand 90, Marketing 85, SEO 80).
DEPARTMENT_THRESHOLDS: dict[str, float] = {
    "brand": 90.0,
    "marketing": 85.0,
    "seo": 80.0,
    "content": 85.0,
    "app": 80.0,
    "gaming": 80.0,
    "robo": 85.0,
    "finances": 90.0,
    "rd": 85.0,
    "default": 80.0,
}


def threshold_for(department: str) -> float:
    key = (department or "default").strip().lower()
    return float(DEPARTMENT_THRESHOLDS.get(key, DEPARTMENT_THRESHOLDS["default"]))


def score_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
    """Heuristic structural score — no fabricated metrics, no LLM required."""
    checks: list[dict[str, Any]] = []
    title = str(artifact.get("title") or artifact.get("name") or "").strip()
    body = str(artifact.get("body") or artifact.get("description") or "").strip()
    status = str(artifact.get("status") or "").strip().lower()

    checks.append({"id": "has_title", "ok": len(title) >= 3, "weight": 25})
    checks.append({"id": "has_body", "ok": len(body) >= 40, "weight": 35})
    checks.append(
        {
            "id": "status_ready",
            "ok": status in {"ready", "approved", "active", "to_review", "draft"},
            "weight": 20,
        }
    )
    # Optional structured fields boost score without inventing data
    extras = 0
    if artifact.get("campaign_id") or artifact.get("project_id"):
        extras += 10
    if artifact.get("platform") or artifact.get("channel"):
        extras += 10
    checks.append({"id": "context_links", "ok": extras >= 10, "weight": 20 if extras else 0})

    earned = 0.0
    total = 0.0
    for c in checks:
        w = float(c["weight"])
        if w <= 0:
            continue
        total += w
        if c["ok"]:
            earned += w
    score = round(100.0 * earned / total, 1) if total else 0.0
    return {"score": score, "checks": checks, "title_len": len(title), "body_len": len(body)}


def evaluate_gate(department: str, artifact: dict[str, Any]) -> dict[str, Any]:
    scored = score_artifact(artifact)
    thr = threshold_for(department)
    score = float(scored["score"])
    return {
        "department": department or "default",
        "threshold": thr,
        "score": score,
        "gate_open": score >= thr,
        "checks": scored["checks"],
    }
