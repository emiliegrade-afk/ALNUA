"""CreatorFlow — Supabase Storage helpers for cf-assets bucket."""

from __future__ import annotations

import re
import uuid
from typing import Any

from database.supabase_client import SupabaseClient

CF_STORAGE_BUCKET = "cf-assets"

ALLOWED_MIMES = frozenset({
    "video/mp4",
    "video/quicktime",
    "video/webm",
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
    "audio/mpeg",
    "audio/wav",
    "audio/mp3",
    "text/plain",
    "text/markdown",
})


def infer_file_type(mime_type: str) -> str:
    if mime_type.startswith("video/"):
        return "video"
    if mime_type.startswith("image/"):
        return "image"
    if mime_type.startswith("audio/"):
        return "audio"
    return "text"


def _safe_filename(name: str) -> str:
    base = name.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    cleaned = re.sub(r"[^\w.\-]", "_", base).strip("._")
    return (cleaned or "asset")[:120]


def upload_cf_asset_file(
    db: SupabaseClient,
    user_id: str,
    content: bytes,
    filename: str,
    mime_type: str,
) -> str:
    """Upload bytes to cf-assets; returns storage path `{user_id}/{uuid}_{file}`."""
    if mime_type not in ALLOWED_MIMES:
        raise ValueError(f"Type MIME non supporté : {mime_type}")

    path = f"{user_id}/{uuid.uuid4()}_{_safe_filename(filename)}"
    db.raw.storage.from_(CF_STORAGE_BUCKET).upload(
        path,
        content,
        file_options={"content-type": mime_type, "upsert": "false"},
    )
    return path


def sign_storage_path(db: SupabaseClient, storage_path: str, *, expires_in: int = 3600) -> str:
    """Return a signed URL for a private cf-assets object."""
    if not storage_path or storage_path.startswith("http"):
        return storage_path
    result: dict[str, Any] = db.raw.storage.from_(CF_STORAGE_BUCKET).create_signed_url(
        storage_path,
        expires_in,
    )
    return result.get("signedURL") or result.get("signedUrl") or storage_path


def enrich_asset_row(db: SupabaseClient, row: dict[str, Any]) -> dict[str, Any]:
    """Attach a fresh signed URL for the asset file."""
    out = dict(row)
    path = out.get("file_url") or ""
    if path and not path.startswith("http"):
        out["file_url"] = sign_storage_path(db, path)
        out["storage_path"] = path
    return out


def download_cf_asset_bytes(db: SupabaseClient, storage_path: str) -> bytes:
    """Download raw bytes from cf-assets bucket."""
    if storage_path.startswith("http"):
        raise ValueError("Cannot download remote URL — expected storage path")
    data = db.raw.storage.from_(CF_STORAGE_BUCKET).download(storage_path)
    if isinstance(data, bytes):
        return data
    if hasattr(data, "read"):
        return data.read()
    raise ValueError("Unexpected storage download response")
