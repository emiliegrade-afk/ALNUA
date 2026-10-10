"""
skill_content_gaming.py — Milestone-driven content for the Gaming pole (all existing/future games).

Agents: Kael Vex (content_gaming)
Tracks UE5/Godot milestones, transforms GDD/lore/captures into teasers
for TikTok, X, YouTube, Discord, Instagram.
Also handles Discord community engagement via skill_discord_wyrdheim.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

PLATFORMS = frozenset({"tiktok", "x", "youtube", "discord", "instagram"})


def fetch_gaming_milestones(project: str = "wyrdheim") -> dict[str, Any]:
    """Latest rows in ``gaming_builds``. Empty means the table was read and has no builds.

    Builds are stored by ``project_id``, not by the content slug, so ``project``
    labels the brief and does not filter the table.
    """
    scanned_at = datetime.now(timezone.utc).isoformat()
    try:
        from database.supabase_client import get_supabase

        rows = get_supabase().select(
            "gaming_builds",
            order_by="created_at",
            ascending=False,
            limit=10,
        ) or []
    except Exception as exc:
        logger.warning("gaming builds unread: %s", exc)
        return {
            "ok": False,
            "available": False,
            "project": project,
            "source": "gaming_builds",
            "milestones": [],
            "last_playable_build": None,
            "scanned_at": scanned_at,
            "note": "Builds Gaming illisibles.",
        }

    milestones = [
        {
            "build_number": row.get("build_number"),
            "status": row.get("status"),
            "branch": row.get("branch"),
            "game_version": row.get("game_version"),
            "engine_version": row.get("engine_version"),
            "created_at": row.get("created_at"),
            "notes": str(row.get("notes") or "")[:200],
        }
        for row in rows
        if isinstance(row, dict)
    ]
    playable = next((item for item in milestones if item.get("status") == "success"), None)
    return {
        "ok": True,
        "available": True,
        "empty": not milestones,
        "project": project,
        "source": "gaming_builds",
        "milestones": milestones,
        "last_playable_build": playable,
        "scanned_at": scanned_at,
        "note": (
            "Aucun build enregistré."
            if not milestones
            else "Derniers builds lus dans gaming_builds."
        ),
    }


def gen_hype_post(
    hook: str,
    lore_snippet: str = "",
    media_type: str = "screenshot",
    platforms: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Generate hype posts across platforms from a hook + optional lore snippet."""
    target = [p for p in (platforms or []) if p in PLATFORMS] or list(PLATFORMS)
    posts: list[dict[str, Any]] = []
    for plat in target:
        posts.append({
            "platform": plat,
            "content_type": "teaser",
            "hook": hook[:280],
            "body": lore_snippet[:1200] if plat != "x" else "",
            "media_hint": media_type,
            "hashtags": ["#Wyrdheim", "#IndieGame", "#UE5", "#GameDev"],
            "discord_crosspost": plat == "discord",
        })
    return posts


def build_gaming_teaser_calendar(
    game: str = "wyrdheim",
    wishlist_target: str = "",
) -> dict[str, Any]:
    """Build a teaser calendar leading to wishlist/early-access."""
    return {
        "game": game,
        "wishlist_target": wishlist_target or "TBD",
        "phases": [
            {"phase": "reveal", "weeks_before": 8, "content": "Premières images, ambiance, monde"},
            {"phase": "gameplay", "weeks_before": 4, "content": "Extraits jouables, mécaniques, classes"},
            {"phase": "wishlist", "weeks_before": 2, "content": "CTA wishlist, trailer court, Discord push"},
        ],
    }