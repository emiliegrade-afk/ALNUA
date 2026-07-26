"""
skill_ads.py — Paid advertising orchestration for Meta/Google/TikTok Ads.

Agents: Léo Morel (ads)
Creates campaigns, amplifies organic posts, A/B tests creatives,
tracks budget and ROI across platforms.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

VALID_PLATFORMS = frozenset({"meta", "google", "tiktok"})
OBJECTIVES = frozenset({"awareness", "traffic", "conversions", "engagement", "video_views"})


def draft_campaign(
    brief: str,
    platform: str = "meta",
    budget_usd: float = 50.0,
    objective: str = "awareness",
    audience: str = "lookalike",
) -> dict[str, Any]:
    """Draft a paid campaign structure before live launch."""
    if platform not in VALID_PLATFORMS:
        return {"ok": False, "error": f"invalid_platform: {platform}", "valid": sorted(VALID_PLATFORMS)}
    if objective not in OBJECTIVES:
        return {"ok": False, "error": f"invalid_objective: {objective}", "valid": sorted(OBJECTIVES)}

    return {
        "ok": True,
        "status": "draft",
        "platform": platform,
        "budget_usd": budget_usd,
        "objective": objective,
        "audience": audience,
        "brief_preview": brief[:300],
        "creative_variations": [
            {"variant": "A", "hook": brief[:100], "cta": "En savoir plus"},
            {"variant": "B", "hook": f"Tu savais que {brief[:80]}", "cta": "Découvrir"},
        ],
    }


def amplify_organic_post(
    post_id: str,
    platform: str = "meta",
    budget_usd: float = 10.0,
    audience: str = "lookalike",
) -> dict[str, Any]:
    """Boost an existing organic post with paid budget."""
    return {
        "ok": True,
        "action": "amplify",
        "post_id": post_id,
        "platform": platform,
        "budget_usd": budget_usd,
        "audience": audience,
        "daily_cap": budget_usd,
        "duration_days": 5,
    }


def campaign_roi_report(campaign_id: str) -> dict[str, Any]:
    """Stub — live ROI report from ad platforms."""
    return {
        "campaign_id": campaign_id,
        "spend": 0,
        "impressions": 0,
        "clicks": 0,
        "ctr": 0,
        "conversions": 0,
        "roas": 0,
        "note": "live Meta/Google/TikTok API integration pending",
    }


def check_budget_alert(
    monthly_budget: float,
    spent: float,
) -> dict[str, Any]:
    """Alert if spending exceeds thresholds."""
    pct = (spent / monthly_budget * 100) if monthly_budget > 0 else 0
    if pct >= 90:
        level = "critical"
    elif pct >= 75:
        level = "warning"
    else:
        level = "ok"
    return {
        "monthly_budget": monthly_budget,
        "spent": spent,
        "pct": round(pct, 1),
        "level": level,
    }