"""CreatorFlow V3 — idea → asset → calendar pipeline."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from database.creatorflow_supabase_client import get_cf_supabase
from database.supabase_client import SupabaseClient
from services.creatorflow_brainstorm import list_idea_artifacts
from services.creatorflow_ideas import get_cf_idea, update_cf_idea
from services.creatorflow_projects import resolve_cf_project_id

_CF_CALENDAR = "cf_calendar_entries"
_CF_ASSETS = "cf_assets"


def _default_schedule_time() -> str:
    # Next day 18:00 UTC — simple default slot
    t = datetime.now(timezone.utc) + timedelta(days=1)
    t = t.replace(hour=18, minute=0, second=0, microsecond=0)
    return t.isoformat()


def _platform_from_idea(idea: dict[str, Any], override: str | None) -> str:
    if override in ("youtube", "instagram"):
        return override
    target = idea.get("platform_target")
    if target == "instagram":
        return "instagram"
    return "youtube"


def _caption_from_script(idea_id: str, user_id: str, db: SupabaseClient) -> str | None:
    scripts = list_idea_artifacts(idea_id, user_id, "script", db)
    if not scripts:
        return None
    content = scripts[0].get("content") or {}
    parts: list[str] = []
    if content.get("hook"):
        parts.append(str(content["hook"]))
    for sec in content.get("sections") or []:
        if isinstance(sec, dict) and sec.get("script"):
            parts.append(str(sec["script"]))
    if content.get("cta"):
        parts.append(str(content["cta"]))
    return "\n\n".join(parts)[:4000] if parts else None


def get_idea_pipeline(
    idea_id: str,
    user_id: str,
    db: SupabaseClient | None = None,
) -> dict[str, Any]:
    db = db or get_cf_supabase()
    idea = get_cf_idea(idea_id, user_id, db)
    if not idea:
        raise ValueError("Idée introuvable")

    asset = None
    calendar_entry = None
    if idea.get("linked_asset_id"):
        rows = db.select(_CF_ASSETS, filters={"id": idea["linked_asset_id"], "user_id": user_id}, limit=1)
        asset = rows[0] if rows else None
    if idea.get("linked_calendar_entry_id"):
        rows = db.select(
            _CF_CALENDAR,
            filters={"id": idea["linked_calendar_entry_id"], "user_id": user_id},
            limit=1,
        )
        calendar_entry = rows[0] if rows else None

    steps = {
        "think": idea.get("status") in ("spark", "developing", "ready_to_shoot", "in_production", "published"),
        "script": bool(list_idea_artifacts(idea_id, user_id, "script", db)),
        "asset": asset is not None,
        "scheduled": calendar_entry is not None,
        "exported": calendar_entry is not None and calendar_entry.get("status") == "exported",
    }

    return {
        "idea": idea,
        "asset": asset,
        "calendar_entry": calendar_entry,
        "steps": steps,
    }


def schedule_idea_to_calendar(
    idea_id: str,
    user_id: str,
    *,
    platform: str | None = None,
    scheduled_at: str | None = None,
    title: str | None = None,
    caption: str | None = None,
    db: SupabaseClient | None = None,
) -> dict[str, Any]:
    db = db or get_cf_supabase()
    idea = get_cf_idea(idea_id, user_id, db)
    if not idea:
        raise ValueError("Idée introuvable")

    resolved_platform = _platform_from_idea(idea, platform)
    slot_title = title or idea.get("title") or idea.get("content", "")[:120]
    slot_caption = caption or _caption_from_script(idea_id, user_id, db) or idea.get("content", "")[:2000]
    slot_time = scheduled_at or _default_schedule_time()
    project_id = resolve_cf_project_id(user_id, idea.get("project_id"), db)
    asset_id = idea.get("linked_asset_id")

    entry = db.insert(
        _CF_CALENDAR,
        {
            "user_id": user_id,
            "project_id": project_id,
            "asset_id": asset_id,
            "platform": resolved_platform,
            "scheduled_at": slot_time,
            "title": slot_title.strip(),
            "caption": slot_caption,
            "hashtags": [],
            "ai_suggested": False,
            "status": "scheduled",
        },
    )

    update_cf_idea(
        idea_id,
        user_id,
        {
            "linked_calendar_entry_id": entry["id"],
            "status": "in_production",
        },
        db,
    )

    return {"calendar_entry": entry, "idea_id": idea_id}


def link_asset_to_idea(
    idea_id: str,
    user_id: str,
    asset_id: str,
    db: SupabaseClient | None = None,
) -> dict[str, Any]:
    db = db or get_cf_supabase()
    idea = get_cf_idea(idea_id, user_id, db)
    if not idea:
        raise ValueError("Idée introuvable")
    rows = db.select(_CF_ASSETS, filters={"id": asset_id, "user_id": user_id}, limit=1)
    if not rows:
        raise ValueError("Asset introuvable")
    updated = update_cf_idea(
        idea_id,
        user_id,
        {"linked_asset_id": asset_id, "status": "in_production"},
        db,
    )
    return {"idea": updated, "asset": rows[0]}
