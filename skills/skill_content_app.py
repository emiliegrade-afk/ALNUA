"""
skill_content_app.py — Dev-log-driven content for the App pole (all existing/future apps).

Agents: Esmée Diallo (content_app)
Pulls dev activity from GitHub (commits, PRs, releases) and generates
cross-platform social content (Instagram, TikTok, LinkedIn, X, blog).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

PLATFORMS = frozenset({"instagram", "tiktok", "x", "linkedin", "blog"})

CHARACTER_LIMITS: dict[str, int] = {
    "instagram": 2200,
    "tiktok": 2200,
    "x": 280,
    "linkedin": 3000,
    "blog": 10000,
}


def fetch_dev_activity(repo: str = "ALNUA", days: int = 7) -> dict[str, Any]:
    """
    Scan recent commits/PRs/releases for the App pole.
    Stub — live GitHub integration via skill_gh_issues in v2.
    """
    return {
        "commits": [],
        "prs": [],
        "releases": [],
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "note": "live GitHub scan via skill_gh_issues pending",
    }


def gen_content_from_dev_log(
    dev_log: str,
    platforms: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Transform a dev log into platform-specific post drafts.

    Returns list of {platform, content_type, text, hashtags, media_hint}.
    """
    target = [p for p in (platforms or []) if p in PLATFORMS] or list(PLATFORMS)
    posts: list[dict[str, Any]] = []
    for plat in target:
        limit = CHARACTER_LIMITS.get(plat, 500)
        posts.append({
            "platform": plat,
            "content_type": "behind_scenes",
            "text": dev_log[:limit],
            "hashtags": ["#ALNUA", "#buildinpublic", "#SoloDev"],
            "media_hint": "screenshot or short clip",
        })
    return posts


def build_app_editorial_calendar(apps: list[str] | None = None) -> dict[str, Any]:
    """Propose a weekly content calendar for the App pole."""
    week_start = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return {
        "week": week_start,
        "apps": apps or ["Naïa", "Eve Journey's"],
        "slots": [
            {"day": "Mon", "angle": "Dev update — ce qui a été mergé cette semaine"},
            {"day": "Wed", "angle": "Feature spotlight — une feature en détail"},
            {"day": "Fri", "angle": "Behind the build — galère, victoire, outil"},
        ],
        "note": "Adapter aux releases réelles du pôle.",
    }