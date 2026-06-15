"""CreatorFlow V1 — creator DNA (brand / channel context)."""

from __future__ import annotations

from typing import Any

from database.supabase_client import SupabaseClient
from database.creatorflow_supabase_client import get_cf_supabase

_CF_DNA = "cf_creator_dna"
VALID_SCOPES = frozenset({"global", "youtube", "instagram"})


def list_cf_creator_dna(
    user_id: str,
    project_id: str | None = None,
    db: SupabaseClient | None = None,
) -> list[dict[str, Any]]:
    db = db or get_cf_supabase()
    filters: dict[str, Any] = {"user_id": user_id}
    if project_id:
        filters["project_id"] = project_id
    else:
        # Global DNA rows have null project_id
        rows = db.select(_CF_DNA, filters={"user_id": user_id}, order_by="scope", ascending=True)
        return [r for r in rows if r.get("project_id") is None]
    return db.select(_CF_DNA, filters=filters, order_by="scope", ascending=True)


def get_cf_creator_dna(
    user_id: str,
    scope: str = "global",
    project_id: str | None = None,
    db: SupabaseClient | None = None,
) -> dict[str, Any] | None:
    db = db or get_cf_supabase()
    if scope not in VALID_SCOPES:
        raise ValueError("Scope invalide")
    filters: dict[str, Any] = {"user_id": user_id, "scope": scope}
    rows = db.select(_CF_DNA, filters=filters)
    if project_id:
        match = next((r for r in rows if r.get("project_id") == project_id), None)
        if match:
            return match
    return next((r for r in rows if r.get("project_id") is None), None)


def upsert_cf_creator_dna(
    user_id: str,
    scope: str,
    *,
    project_id: str | None = None,
    voice_tone: str | None = None,
    audience: str | None = None,
    brand_promise: str | None = None,
    taboos: list[str] | None = None,
    style_refs: list[str] | None = None,
    extra: dict[str, Any] | None = None,
    db: SupabaseClient | None = None,
) -> dict[str, Any]:
    db = db or get_cf_supabase()
    if scope not in VALID_SCOPES:
        raise ValueError("Scope invalide")

    existing = get_cf_creator_dna(user_id, scope, project_id, db)
    payload = {
        "voice_tone": voice_tone,
        "audience": audience,
        "brand_promise": brand_promise,
        "taboos": taboos or [],
        "style_refs": style_refs or [],
        "extra": extra or {},
    }
    if existing:
        return db.update(_CF_DNA, existing["id"], payload)

    return db.insert(
        _CF_DNA,
        {
            "user_id": user_id,
            "project_id": project_id,
            "scope": scope,
            **payload,
        },
    )


def build_dna_context_block(user_id: str, project_id: str | None = None) -> str:
    """Plain-text DNA block for LLM prompts."""
    db = get_cf_supabase()
    parts: list[str] = []
    for scope in ("global", "youtube", "instagram"):
        row = get_cf_creator_dna(user_id, scope, project_id, db)
        if not row:
            continue
        chunk = [f"[DNA {scope}]"]
        if row.get("voice_tone"):
            chunk.append(f"Voix: {row['voice_tone']}")
        if row.get("audience"):
            chunk.append(f"Audience: {row['audience']}")
        if row.get("brand_promise"):
            chunk.append(f"Promesse: {row['brand_promise']}")
        if row.get("taboos"):
            chunk.append(f"Tabous: {', '.join(row['taboos'])}")
        if row.get("style_refs"):
            chunk.append(f"Références: {', '.join(row['style_refs'])}")
        if len(chunk) > 1:
            parts.append("\n".join(chunk))
    return "\n\n".join(parts) if parts else "Aucun Creator DNA configuré."
