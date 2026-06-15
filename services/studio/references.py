"""Resolve Studio job media references (storage paths → signed URLs for providers)."""

from __future__ import annotations

from typing import Any

from database.supabase_client import SupabaseClient
from services.creatorflow_storage import sign_storage_path

_CF_ASSETS = "cf_assets"


def resolve_studio_job_params(
    params: dict[str, Any] | None,
    user_id: str,
    db: SupabaseClient,
) -> dict[str, Any]:
    """Turn reference_asset_id / storage paths into provider-ready prompt_image URLs."""
    merged = dict(params or {})
    asset_id = merged.get("reference_asset_id")
    if asset_id:
        rows = db.select(
            _CF_ASSETS,
            filters={"id": str(asset_id), "user_id": user_id},
            limit=1,
        )
        if rows:
            path = str(rows[0].get("file_url") or "").strip()
            if path:
                merged["prompt_image"] = _to_provider_url(db, path)
        merged.pop("reference_asset_id", None)

    source_asset_id = merged.get("source_asset_id")
    if source_asset_id:
        rows = db.select(
            _CF_ASSETS,
            filters={"id": str(source_asset_id), "user_id": user_id},
            limit=1,
        )
        if rows:
            path = str(rows[0].get("file_url") or "").strip()
            if path:
                merged["source_image"] = path
        merged.pop("source_asset_id", None)
    else:
        raw_source = merged.get("source_image")
        if isinstance(raw_source, str) and raw_source.strip() and not raw_source.startswith("http"):
            merged["source_image"] = raw_source.strip()

    for key in ("prompt_image", "promptImage"):
        raw = merged.get(key)
        if isinstance(raw, str) and raw.strip():
            merged["prompt_image"] = _to_provider_url(db, raw.strip())
            merged.pop("promptImage", None)
            break
    return merged


def _to_provider_url(db: SupabaseClient, path: str) -> str:
    if path.startswith("http://") or path.startswith("https://") or path.startswith("data:"):
        return path
    return sign_storage_path(db, path)
