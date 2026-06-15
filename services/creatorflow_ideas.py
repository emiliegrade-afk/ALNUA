"""CreatorFlow V1 — idea inbox CRUD."""

from __future__ import annotations

from typing import Any

from database.supabase_client import SupabaseClient
from database.creatorflow_supabase_client import get_cf_supabase
from services.creatorflow_projects import resolve_cf_project_id

_CF_IDEAS = "cf_ideas"

VALID_STATUSES = frozenset(
    {"spark", "developing", "ready_to_shoot", "in_production", "published", "archived"}
)


def list_cf_ideas(
    user_id: str,
    project_id: str | None = None,
    status: str | None = None,
    db: SupabaseClient | None = None,
) -> list[dict[str, Any]]:
    db = db or get_cf_supabase()
    filters: dict[str, Any] = {"user_id": user_id}
    if project_id:
        filters["project_id"] = project_id
    if status:
        filters["status"] = status
    return db.select(
        _CF_IDEAS,
        filters=filters,
        order_by="updated_at",
        ascending=False,
    )


def get_cf_idea(idea_id: str, user_id: str, db: SupabaseClient | None = None) -> dict[str, Any] | None:
    db = db or get_cf_supabase()
    rows = db.select(_CF_IDEAS, filters={"id": idea_id, "user_id": user_id}, limit=1)
    return rows[0] if rows else None


def create_cf_idea(
    user_id: str,
    content: str,
    *,
    title: str | None = None,
    project_id: str | None = None,
    tags: list[str] | None = None,
    platform_target: str | None = None,
    source_url: str | None = None,
    notes: str | None = None,
    db: SupabaseClient | None = None,
) -> dict[str, Any]:
    db = db or get_cf_supabase()
    resolved_project = resolve_cf_project_id(user_id, project_id, db)
    auto_title = (title or content.strip()[:80] or "Idée").strip()
    return db.insert(
        _CF_IDEAS,
        {
            "user_id": user_id,
            "project_id": resolved_project,
            "title": auto_title,
            "content": content.strip(),
            "status": "spark",
            "tags": tags or [],
            "platform_target": platform_target,
            "source_url": source_url,
            "notes": notes,
        },
    )


def update_cf_idea(
    idea_id: str,
    user_id: str,
    patch: dict[str, Any],
    db: SupabaseClient | None = None,
) -> dict[str, Any] | None:
    db = db or get_cf_supabase()
    existing = get_cf_idea(idea_id, user_id, db)
    if not existing:
        return None
    allowed = {"title", "content", "status", "tags", "platform_target", "source_url", "notes", "project_id", "linked_asset_id", "linked_calendar_entry_id"}
    payload = {k: v for k, v in patch.items() if k in allowed and v is not None}
    if "status" in payload and payload["status"] not in VALID_STATUSES:
        raise ValueError("Statut invalide")
    if not payload:
        return existing
    return db.update(_CF_IDEAS, idea_id, payload)


def delete_cf_idea(idea_id: str, user_id: str, db: SupabaseClient | None = None) -> bool:
    db = db or get_cf_supabase()
    existing = get_cf_idea(idea_id, user_id, db)
    if not existing:
        return False
    db.delete(_CF_IDEAS, idea_id)
    return True
