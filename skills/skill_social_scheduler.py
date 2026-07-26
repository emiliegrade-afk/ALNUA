"""
skill_social_scheduler.py — Typefully-like social media scheduler for ALNUA.

Agents: content_app, content_gaming, content_robo, content_company, ads
Queue posts, review before publish, cross-post across platforms,
track analytics (impressions, engagement, clicks).
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

CALENDAR_PLATFORMS = frozenset({"instagram", "tiktok", "x", "youtube", "linkedin", "discord", "blog", "meta_ads", "google_ads", "tiktok_ads"})


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def queue_post(
    platform: str,
    content: str,
    hashtags: list[str] | None = None,
    media_hint: str = "",
    scheduled_for: str | None = None,
    author_agent: str = "",
    needs_review: bool = True,
) -> dict[str, Any]:
    """Add a post to the social scheduler queue for review and scheduling."""
    if platform not in CALENDAR_PLATFORMS:
        return {"ok": False, "error": f"invalid_platform: {platform}", "valid": sorted(CALENDAR_PLATFORMS)}

    return {
        "ok": True,
        "post_id": str(uuid.uuid4()),
        "status": "review" if needs_review else "scheduled",
        "platform": platform,
        "content_preview": content[:280],
        "hashtags": hashtags or [],
        "media_hint": media_hint,
        "scheduled_for": scheduled_for or _utc_now(),
        "author_agent": author_agent,
        "queued_at": _utc_now(),
    }


def get_queued_posts(
    status: str = "review",
    author_agent: str = "",
    limit: int = 20,
) -> dict[str, Any]:
    """Retrieve queued posts (stub — in-memory for v1, Supabase for v2)."""
    return {
        "posts": [],
        "total": 0,
        "filter_status": status,
        "note": "stub — Supabase persistence pending",
    }


def approve_post(post_id: str, reviewer: str = "ceo") -> dict[str, Any]:
    """Mark a post as reviewed and ready to publish."""
    return {
        "ok": True,
        "post_id": post_id,
        "status": "scheduled",
        "reviewed_by": reviewer,
        "reviewed_at": _utc_now(),
    }


def track_post_analytics(post_id: str, platform: str) -> dict[str, Any]:
    """Stub — fetch post analytics (impressions, engagement, clicks) after publishing."""
    return {
        "post_id": post_id,
        "platform": platform,
        "impressions": 0,
        "likes": 0,
        "comments": 0,
        "shares": 0,
        "clicks": 0,
        "fetched_at": _utc_now(),
        "note": "live platform analytics API integration pending",
    }