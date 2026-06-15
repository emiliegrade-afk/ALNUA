"""CreatorFlow — Composio OAuth bridge for YouTube / Instagram (Sprint 3)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from config.settings import get_settings
from database.supabase_client import SupabaseClient
from database.creatorflow_supabase_client import get_cf_supabase
from skills.skill_composio import (
    composio_execute,
    get_oauth_link,
    has_active_connection,
    list_connected_apps,
)

logger = logging.getLogger(__name__)

_CF_PLATFORMS = "cf_platform_connections"
_COMPOSIO_MANAGED_TOKEN = "composio_managed"

PLATFORM_TO_COMPOSIO: dict[str, str] = {
    "youtube": "youtube",
    "instagram": "instagram",
}


def cf_composio_user_id(supabase_user_id: str) -> str:
    """Isolate CreatorFlow OAuth sessions from internal Hub agent user_ids."""
    return f"cf_{supabase_user_id}"


def _platform_redirect_url(platform: str) -> str:
    base = get_settings().creatorflow_app_url.rstrip("/")
    return f"{base}/platforms/callback?platform={platform}"


def start_cf_platform_connect(platform: str, user_id: str) -> dict[str, Any]:
    """Return OAuth URL (Composio) for youtube | instagram."""
    if platform not in PLATFORM_TO_COMPOSIO:
        raise ValueError(f"Plateforme non supportée : {platform}")

    composio_uid = cf_composio_user_id(user_id)
    toolkit = PLATFORM_TO_COMPOSIO[platform]
    if has_active_connection(composio_uid, toolkit):
        sync_cf_platform_connection(user_id, platform)
        return {
            "platform": platform,
            "oauth_url": None,
            "already_connected": True,
            "message": f"{platform} est déjà connecté",
        }

    app_name = toolkit.upper()
    link = get_oauth_link(
        app=app_name,
        user_id=composio_uid,
        redirect_url=_platform_redirect_url(platform),
    )
    if not link.startswith("http"):
        return {
            "platform": platform,
            "oauth_url": None,
            "already_connected": "déjà connecté" in link.lower() or "[OK]" in link,
            "message": link,
        }
    return {
        "platform": platform,
        "oauth_url": link,
        "already_connected": False,
        "message": None,
    }


def _fetch_platform_username(composio_uid: str, platform: str) -> str | None:
    """Best-effort profile lookup after OAuth — failures are non-fatal."""
    try:
        if platform == "youtube":
            result = composio_execute(
                "YOUTUBE_LIST_USER_CHANNELS",
                {"part": "snippet", "mine": True, "maxResults": 1},
                user_id=composio_uid,
            )
            if result.get("success") and isinstance(result.get("data"), dict):
                items = result["data"].get("items") or []
                if items:
                    snippet = items[0].get("snippet") or {}
                    return snippet.get("title") or snippet.get("customUrl")
        elif platform == "instagram":
            result = composio_execute(
                "INSTAGRAM_GET_USER_INFO",
                {},
                user_id=composio_uid,
            )
            if result.get("success") and isinstance(result.get("data"), dict):
                data = result["data"]
                return data.get("username") or data.get("name")
    except Exception as exc:
        logger.debug("platform username lookup failed for %s: %s", platform, exc)
    return None


def sync_cf_platform_connection(
    user_id: str,
    platform: str,
    db: SupabaseClient | None = None,
) -> dict[str, Any]:
    """Upsert cf_platform_connections from Composio ACTIVE session."""
    if platform not in PLATFORM_TO_COMPOSIO:
        raise ValueError(f"Plateforme non supportée : {platform}")

    db = db or get_cf_supabase()
    composio_uid = cf_composio_user_id(user_id)
    toolkit = PLATFORM_TO_COMPOSIO[platform]
    connected = has_active_connection(composio_uid, toolkit)

    if not connected:
        existing = db.select(
            _CF_PLATFORMS,
            filters={"user_id": user_id, "platform": platform},
            limit=1,
        )
        if existing:
            db.update(_CF_PLATFORMS, existing[0]["id"], {"is_active": False})
        return {
            "platform": platform,
            "is_active": False,
            "platform_username": None,
            "connected_at": None,
        }

    username = _fetch_platform_username(composio_uid, platform)
    now = datetime.now(timezone.utc).isoformat()
    payload = {
        "user_id": user_id,
        "platform": platform,
        "access_token": _COMPOSIO_MANAGED_TOKEN,
        "refresh_token": None,
        "token_expires_at": None,
        "platform_user_id": composio_uid,
        "platform_username": username,
        "connected_at": now,
        "is_active": True,
    }

    existing = db.select(
        _CF_PLATFORMS,
        filters={"user_id": user_id, "platform": platform},
        limit=1,
    )
    if existing:
        row_id = existing[0]["id"]
        db.update(_CF_PLATFORMS, row_id, payload)
    else:
        db.insert(_CF_PLATFORMS, payload)

    return {
        "platform": platform,
        "is_active": True,
        "platform_username": username,
        "connected_at": now,
    }


def sync_all_cf_platforms(user_id: str, db: SupabaseClient | None = None) -> list[dict[str, Any]]:
    """Refresh YouTube + Instagram rows from Composio."""
    return [
        sync_cf_platform_connection(user_id, platform, db)
        for platform in ("youtube", "instagram")
    ]


def is_cf_platform_connected(
    user_id: str,
    platform: str,
    db: SupabaseClient | None = None,
) -> bool:
    """True when DB row is active OR Composio reports ACTIVE (handles stale DB)."""
    if platform not in PLATFORM_TO_COMPOSIO:
        return False
    composio_uid = cf_composio_user_id(user_id)
    if has_active_connection(composio_uid, PLATFORM_TO_COMPOSIO[platform]):
        return True
    db = db or get_cf_supabase()
    rows = db.select(
        _CF_PLATFORMS,
        filters={"user_id": user_id, "platform": platform, "is_active": True},
        limit=1,
    )
    return bool(rows)


def disconnect_cf_platform(
    user_id: str,
    platform: str,
    db: SupabaseClient | None = None,
) -> dict[str, Any]:
    """Mark platform disconnected locally (Composio session may remain until revoked)."""
    db = db or get_cf_supabase()
    rows = db.select(
        _CF_PLATFORMS,
        filters={"user_id": user_id, "platform": platform},
        limit=1,
    )
    if rows:
        db.update(_CF_PLATFORMS, rows[0]["id"], {"is_active": False})
    return {
        "platform": platform,
        "is_active": False,
        "platform_username": None,
        "connected_at": None,
    }


def list_cf_platform_status(user_id: str, db: SupabaseClient | None = None) -> list[dict[str, Any]]:
    """Return connection status for both platforms, syncing from Composio when key present."""
    db = db or get_cf_supabase()
    if get_settings().composio_api_key.strip():
        try:
            return sync_all_cf_platforms(user_id, db)
        except Exception as exc:
            logger.warning("Composio platform sync failed: %s", exc)

    rows = db.select(_CF_PLATFORMS, filters={"user_id": user_id})
    by_platform = {r["platform"]: r for r in rows}
    result: list[dict[str, Any]] = []
    for platform in ("youtube", "instagram"):
        if platform in by_platform and by_platform[platform].get("is_active"):
            row = by_platform[platform]
            result.append(
                {
                    "platform": platform,
                    "is_active": True,
                    "platform_username": row.get("platform_username"),
                    "connected_at": row.get("connected_at"),
                }
            )
        else:
            result.append(
                {
                    "platform": platform,
                    "is_active": False,
                    "platform_username": None,
                    "connected_at": None,
                }
            )
    return result
