"""
skill_lore_database.py — Base de données lore Wyrdheim + Naïa World dans Supabase

Table Supabase : lore_entries (voir migration 20260611130000_phase3_agents.sql)
"""

from __future__ import annotations

from typing import Any

from database.supabase_client import get_supabase


def search_lore(query: str, project: str | None = None, limit: int = 5) -> list[dict[str, Any]]:
    """Recherche full-text dans le lore."""
    sb = get_supabase()
    q = sb.table("lore_entries").select("*")
    if project:
        q = q.eq("project", project)
    q = q.ilike("title", f"%{query}%").limit(limit)
    result = q.execute()
    if not result.data:
        result = (
            sb.table("lore_entries")
            .select("*")
            .ilike("content", f"%{query}%")
            .limit(limit)
            .execute()
        )
    return result.data or []


def add_lore_entry(entry: dict[str, Any]) -> dict[str, Any]:
    """Ajoute une entrée lore."""
    sb = get_supabase()
    response = sb.table("lore_entries").insert(entry).execute()
    if not response.data:
        raise RuntimeError("Insert lore_entries returned no data")
    return response.data[0]


def update_lore_entry(entry_id: str, updates: dict[str, Any]) -> dict[str, Any]:
    """Met à jour une entrée lore existante."""
    sb = get_supabase()
    updates["updated_at"] = "now()"
    response = sb.table("lore_entries").update(updates).eq("id", entry_id).execute()
    if not response.data:
        raise RuntimeError(f"Update lore_entries id={entry_id} returned no data")
    return response.data[0]
