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
    """Draft a paid boost. Does not call Meta, Google, or TikTok."""
    return {
        "ok": True,
        "status": "draft",
        "platform_live": False,
        "action": "amplify",
        "post_id": post_id,
        "platform": platform,
        "budget_usd": budget_usd,
        "audience": audience,
        "daily_cap": budget_usd,
        "duration_days": 5,
        "note": "Brouillon seulement — aucune campagne n'est lancée sur la régie.",
    }


def campaign_roi_report(campaign_id: str) -> dict[str, Any]:
    """Spend from linked expense transactions, plus stats typed on the campaign.

    Reach, engagements, conversions, and revenue stay null until someone
    entered them. Ad-platform impressions, clicks, and CTR are omitted:
    those APIs are not connected, and a zero would look like a measurement.
    """
    cid = (campaign_id or "").strip()
    if not cid:
        return {"ok": False, "available": False, "platform_live": False, "error": "campaign_id manquant"}
    try:
        from database.supabase_client import get_supabase

        db = get_supabase()
        rows = db.select("campaigns", filters={"id": cid}) or []
        expenses = db.select("transactions", filters={"type": "expense"}) or []
    except Exception as exc:
        logger.warning("campaign ledger unread: %s", exc)
        return {
            "ok": False,
            "available": False,
            "campaign_id": cid,
            "source": "ledger",
            "platform_live": False,
            "error": "Campagne illisible",
        }
    if not rows or not isinstance(rows[0], dict):
        return {
            "ok": False,
            "available": False,
            "campaign_id": cid,
            "platform_live": False,
            "error": "Campagne introuvable",
        }

    row = rows[0]
    spent = round(
        sum(
            float(tx.get("amount") or 0)
            for tx in expenses
            if isinstance(tx, dict) and tx.get("campaign_id") == cid
        ),
        2,
    )
    revenue = row.get("revenue_generated_usd")
    roi_pct = None
    if revenue is not None and spent > 0:
        roi_pct = round((float(revenue) - spent) / spent * 100, 1)
    return {
        "ok": True,
        "available": True,
        "campaign_id": cid,
        "source": "ledger",
        "platform_live": False,
        "spent_usd": spent,
        "budget_allocated_usd": row.get("budget_allocated_usd"),
        "reach": row.get("reach"),
        "engagements": row.get("engagements"),
        "conversions": row.get("conversions"),
        "revenue_generated_usd": revenue,
        "roi_pct": roi_pct,
        "note": (
            "Dépense = transactions liées. Reach et ROI seulement s'ils ont été saisis. "
            "API Meta/Google/TikTok non branchée."
        ),
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