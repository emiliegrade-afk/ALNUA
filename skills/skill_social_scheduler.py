"""
skill_social_scheduler.py — Typefully-like social media scheduler for ALNUA.

Agents: content_app, content_gaming, content_robo, content_company, ads
Queue posts (persistant, table posts_queue), review avant publication,
vue calendrier transverse par secteur. Le publisher_bot lit cette même table.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# Doit rester synchro avec la CHECK constraint posts_queue_platform_check (schema.sql +
# supabase/migrations/20260726120000_posts_queue_studio_typefully.sql).
CALENDAR_PLATFORMS = frozenset({
    "instagram", "tiktok", "x", "youtube", "linkedin", "website_blog", "discord",
})

SECTORS = frozenset({"app", "gaming", "robo", "company"})


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _client(db: Any | None = None) -> Any:
    if db is not None:
        return db
    from database.supabase_client import get_supabase

    return get_supabase()


def queue_post(
    project_id: str,
    platform: str,
    content: str,
    *,
    sector: str = "",
    author_agent: str = "",
    content_type: str = "announcement",
    hashtags: list[str] | None = None,
    layout: dict[str, Any] | None = None,
    media_urls: list[str] | None = None,
    channel: str = "",
    scheduled_for: str | None = None,
    needs_review: bool = True,
    status: str | None = None,
    db: Any | None = None,
) -> dict[str, Any]:
    """Ajoute un post à la queue persistante (table posts_queue).

    `status`, quand fourni, prime sur `needs_review` (utile pour le Composer qui expose
    draft/pending_approval/approved directement plutôt qu'un simple booléen).
    """
    if platform not in CALENDAR_PLATFORMS:
        return {"ok": False, "error": f"invalid_platform: {platform}", "valid": sorted(CALENDAR_PLATFORMS)}
    if sector and sector not in SECTORS:
        return {"ok": False, "error": f"invalid_sector: {sector}", "valid": sorted(SECTORS)}
    if not content.strip():
        return {"ok": False, "error": "empty_content"}

    resolved_status = status or ("pending_approval" if needs_review else "approved")

    client = _client(db)
    row = client.insert(
        "posts_queue",
        {
            "project_id": project_id,
            "sector": sector or None,
            "author_agent_id": author_agent or None,
            "platform": platform,
            "content_type": content_type,
            "text_content": content,
            "layout": layout,
            "media_urls": media_urls or [],
            "channel": channel or None,
            "hashtags": hashtags or [],
            "scheduled_at": scheduled_for or _utc_now(),
            "status": resolved_status,
        },
    )
    return {"ok": True, "post": row}


def get_queued_posts(
    status: str = "pending_approval",
    sector: str = "",
    author_agent: str = "",
    project_id: str = "",
    limit: int = 20,
    db: Any | None = None,
) -> dict[str, Any]:
    """Récupère les posts en queue, filtrés par statut/secteur/agent/projet."""
    client = _client(db)
    filters: dict[str, Any] = {}
    if status:
        filters["status"] = status
    if sector:
        filters["sector"] = sector
    if author_agent:
        filters["author_agent_id"] = author_agent
    if project_id:
        filters["project_id"] = project_id
    rows = client.select("posts_queue", filters=filters, order_by="scheduled_at", limit=limit)
    return {"posts": rows, "total": len(rows), "filter_status": status, "sector": sector or "all"}


def get_calendar(
    date_from: str,
    date_to: str,
    sector: str = "",
    db: Any | None = None,
) -> dict[str, Any]:
    """Vue calendrier : posts planifiés entre deux dates (YYYY-MM-DD), groupés par jour."""
    client = _client(db)
    query = (
        client.table("posts_queue")
        .select("*")
        .gte("scheduled_at", f"{date_from}T00:00:00")
        .lte("scheduled_at", f"{date_to}T23:59:59")
        .order("scheduled_at", desc=False)
    )
    if sector:
        query = query.eq("sector", sector)
    rows = query.execute().data or []

    by_day: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        day = str(row.get("scheduled_at") or "")[:10]
        by_day.setdefault(day, []).append(row)

    return {"from": date_from, "to": date_to, "sector": sector or "all", "days": by_day, "total": len(rows)}


def approve_post(post_id: str, reviewer: str = "ceo", db: Any | None = None) -> dict[str, Any]:
    """Approuve un post — passe en statut 'approved', repris par le publisher_bot au bon horaire."""
    client = _client(db)
    row = client.update("posts_queue", post_id, {"status": "approved"})
    return {"ok": True, "post_id": post_id, "status": "approved", "reviewed_by": reviewer, "post": row}


def reject_post(post_id: str, reason: str = "", reviewer: str = "ceo", db: Any | None = None) -> dict[str, Any]:
    """Rejette un post — reste tracé dans posts_queue (status='rejected'), jamais publié."""
    client = _client(db)
    row = client.update("posts_queue", post_id, {"status": "rejected"})
    logger.info("Post %s rejeté par %s : %s", post_id, reviewer, reason[:200])
    return {"ok": True, "post_id": post_id, "status": "rejected", "reviewed_by": reviewer, "post": row}


def track_post_analytics(post_id: str, platform: str) -> dict[str, Any]:
    """Stub assumé : aucune clé API d'analytics plateforme configurée à ce jour (Meta/X/TikTok...).

    Intentionnellement non branché — à câbler quand une clé API sera fournie.
    """
    return {
        "post_id": post_id,
        "platform": platform,
        "impressions": None,
        "likes": None,
        "comments": None,
        "shares": None,
        "clicks": None,
        "fetched_at": _utc_now(),
        "note": "analytics plateforme non configurées — aucune clé API disponible",
    }
