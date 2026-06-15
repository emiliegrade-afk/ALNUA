"""Load source images for Studio post-prod tools."""

from __future__ import annotations

from io import BytesIO
from typing import Any

import httpx
from PIL import Image

from database.supabase_client import SupabaseClient
from services.creatorflow_storage import download_cf_asset_bytes

_CF_ASSETS = "cf_assets"
_HTTP_TIMEOUT = 60.0


def resolve_source_storage_path(
    params: dict[str, Any],
    user_id: str,
    db: SupabaseClient,
) -> str:
    """Return storage path or http(s) URL for the source image."""
    asset_id = params.get("source_asset_id") or params.get("reference_asset_id")
    if asset_id:
        rows = db.select(
            _CF_ASSETS,
            filters={"id": str(asset_id), "user_id": user_id},
            limit=1,
        )
        if rows:
            path = str(rows[0].get("file_url") or "").strip()
            if path:
                return path

    for key in ("source_image", "prompt_image", "promptImage"):
        raw = params.get(key)
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
    return ""


def load_image_from_params(
    params: dict[str, Any],
    user_id: str,
    db: SupabaseClient,
) -> Image.Image:
    path = resolve_source_storage_path(params, user_id, db)
    if not path:
        raise ValueError("Image source requise — choisissez un visuel ou la dernière création")
    raw = _load_bytes(path, db)
    img = Image.open(BytesIO(raw))
    return img.convert("RGBA")


def _load_bytes(path: str, db: SupabaseClient) -> bytes:
    if path.startswith("http://") or path.startswith("https://"):
        with httpx.Client(timeout=_HTTP_TIMEOUT, follow_redirects=True) as client:
            res = client.get(path)
            res.raise_for_status()
            return res.content
    return download_cf_asset_bytes(db, path)


def image_to_png_bytes(image: Image.Image) -> bytes:
    buf = BytesIO()
    rgba = image.convert("RGBA")
    rgba.save(buf, format="PNG")
    return buf.getvalue()
