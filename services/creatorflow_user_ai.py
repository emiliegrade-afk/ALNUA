"""CreatorFlow V1 — user BYOK AI settings."""

from __future__ import annotations

from typing import Any

from database.supabase_client import SupabaseClient
from database.creatorflow_supabase_client import get_cf_supabase
from services.creatorflow_secrets import encrypt_user_secret, mask_api_key

_CF_AI = "cf_user_ai_settings"


def get_cf_ai_settings(user_id: str, db: SupabaseClient | None = None) -> dict[str, Any]:
    db = db or get_cf_supabase()
    rows = db.select(_CF_AI, filters={"user_id": user_id}, limit=1)
    if not rows:
        return {
            "user_id": user_id,
            "provider": "openrouter",
            "use_own_key": False,
            "default_model": None,
            "api_key_masked": None,
            "has_key": False,
        }
    row = rows[0]
    has_key = bool(row.get("api_key_encrypted"))
    masked = mask_api_key("sk-placeholder") if has_key else None
    if has_key and row.get("use_own_key"):
        try:
            from services.creatorflow_secrets import decrypt_user_secret

            masked = mask_api_key(decrypt_user_secret(user_id, row["api_key_encrypted"]))
        except Exception:
            masked = "••••"
    return {
        "user_id": user_id,
        "provider": row.get("provider") or "openrouter",
        "use_own_key": bool(row.get("use_own_key")),
        "default_model": row.get("default_model"),
        "api_key_masked": masked,
        "has_key": has_key,
    }


def upsert_cf_ai_settings(
    user_id: str,
    *,
    api_key: str | None = None,
    use_own_key: bool | None = None,
    default_model: str | None = None,
    db: SupabaseClient | None = None,
) -> dict[str, Any]:
    db = db or get_cf_supabase()
    rows = db.select(_CF_AI, filters={"user_id": user_id}, limit=1)
    payload: dict[str, Any] = {}
    if api_key is not None and api_key.strip():
        payload["api_key_encrypted"] = encrypt_user_secret(user_id, api_key.strip())
    if use_own_key is not None:
        payload["use_own_key"] = use_own_key
    if default_model is not None:
        payload["default_model"] = default_model.strip() or None

    if rows:
        if payload:
            db.update(_CF_AI, user_id, payload, id_column="user_id")
    else:
        db.insert(
            _CF_AI,
            {
                "user_id": user_id,
                "provider": "openrouter",
                "use_own_key": use_own_key if use_own_key is not None else False,
                "default_model": default_model,
                "api_key_encrypted": payload.get("api_key_encrypted"),
            },
        )
    return get_cf_ai_settings(user_id, db)


def delete_cf_ai_settings(user_id: str, db: SupabaseClient | None = None) -> None:
    db = db or get_cf_supabase()
    rows = db.select(_CF_AI, filters={"user_id": user_id}, limit=1)
    if rows:
        db.delete(_CF_AI, user_id, id_column="user_id")
