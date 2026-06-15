"""CreatorFlow — multi-project workspace helpers (P1)."""

from __future__ import annotations

import re
import uuid
from typing import Any

from database.supabase_client import SupabaseClient
from database.creatorflow_supabase_client import get_cf_supabase

_CF_PROJECTS = "cf_projects"


def slugify_project_name(name: str) -> str:
    base = re.sub(r"[^\w\s-]", "", name.lower().strip())
    base = re.sub(r"[\s_-]+", "-", base).strip("-")
    return (base or "projet")[:60]


def ensure_default_cf_project(user_id: str, db: SupabaseClient | None = None) -> dict[str, Any]:
    """Return the user's default project, creating one if missing."""
    db = db or get_cf_supabase()
    rows = db.select(
        _CF_PROJECTS,
        filters={"user_id": user_id},
        order_by="created_at",
        ascending=True,
    )
    default = next((r for r in rows if r.get("is_default")), None)
    if default:
        return default
    if rows:
        return rows[0]

    slug = slugify_project_name("Mon projet")
    return db.insert(
        _CF_PROJECTS,
        {
            "user_id": user_id,
            "name": "Mon projet",
            "slug": slug,
            "description": "Projet par défaut CreatorFlow",
            "is_default": True,
        },
    )


def list_cf_projects(user_id: str, db: SupabaseClient | None = None) -> list[dict[str, Any]]:
    db = db or get_cf_supabase()
    ensure_default_cf_project(user_id, db)
    return db.select(
        _CF_PROJECTS,
        filters={"user_id": user_id},
        order_by="created_at",
        ascending=True,
    )


def get_cf_project(project_id: str, user_id: str, db: SupabaseClient | None = None) -> dict[str, Any] | None:
    db = db or get_cf_supabase()
    rows = db.select(
        _CF_PROJECTS,
        filters={"id": project_id, "user_id": user_id},
        limit=1,
    )
    return rows[0] if rows else None


def resolve_cf_project_id(
    user_id: str,
    project_id: str | None,
    db: SupabaseClient | None = None,
) -> str:
    """Validate project_id or fall back to default project."""
    db = db or get_cf_supabase()
    if project_id:
        project = get_cf_project(project_id, user_id, db)
        if not project:
            raise ValueError("Projet introuvable")
        return project["id"]
    return ensure_default_cf_project(user_id, db)["id"]


def create_cf_project(
    user_id: str,
    name: str,
    description: str | None = None,
    db: SupabaseClient | None = None,
) -> dict[str, Any]:
    db = db or get_cf_supabase()
    base_slug = slugify_project_name(name)
    slug = base_slug
    existing = {r["slug"] for r in list_cf_projects(user_id, db)}
    if slug in existing:
        slug = f"{base_slug}-{uuid.uuid4().hex[:6]}"
    return db.insert(
        _CF_PROJECTS,
        {
            "user_id": user_id,
            "name": name.strip()[:120],
            "slug": slug,
            "description": description,
            "is_default": False,
        },
    )
