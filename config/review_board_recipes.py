"""Default Review Board reviewers by department (Phase 35 / DEC-013 slice)."""

from __future__ import annotations

# When callers omit reviewers, resolve from this map.
# "brand" runs services.brand_design_system.review_brand_coherence.
DEFAULT_REVIEWERS: dict[str, list[str]] = {
    "marketing": ["brand", "qa"],
    "content": ["brand", "content_company", "qa"],
    "brand": ["brand", "content_company"],
    "comms": ["brand", "qa"],
    "app": ["qa", "pm"],
    "gaming": ["qa", "pm"],
    "robo": ["qa", "safety"],
    "rnd": ["qa", "pm"],
    "finances": ["qa", "controller"],
}


def resolve_reviewers(
    department: str,
    reviewers: list[str] | None = None,
) -> list[str]:
    if reviewers:
        return list(reviewers)
    dept = (department or "").strip().lower()
    return list(DEFAULT_REVIEWERS.get(dept, ["quality_gates"]))
