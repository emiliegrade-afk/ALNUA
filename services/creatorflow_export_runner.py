"""CreatorFlow — background export runner (mock + real publish Sprint 3)."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any

from agents.cf_format_adapter import adapt_cf_for_platform
from config.settings import get_settings
from database.supabase_client import SupabaseClient
from database.creatorflow_supabase_client import get_cf_supabase
from services.creatorflow_platforms import is_cf_platform_connected
from services.creatorflow_publishers import publish_cf_to_platform
from services.creatorflow_storage import download_cf_asset_bytes
from services.event_bus import emit

logger = logging.getLogger(__name__)

CF_EXPORT_DAILY_LIMIT = 100
_MAX_RETRIES = 3
_RETRY_BACKOFF_SEC = 2.0


def count_user_exports_today(db: SupabaseClient, user_id: str) -> int:
    """Count cf_exports created today (UTC) for rate limiting."""
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    rows = db.select("cf_exports", filters={"user_id": user_id}, order_by="created_at", ascending=False)
    count = 0
    for row in rows:
        created = row.get("created_at") or ""
        try:
            ts = datetime.fromisoformat(created.replace("Z", "+00:00"))
        except ValueError:
            continue
        if ts >= today_start:
            count += 1
        else:
            break
    return count


def _mock_publish(platform: str, export_id: str) -> dict[str, str]:
    post_id = f"mock_{platform}_{export_id[:8]}"
    return {
        "platform_post_id": post_id,
        "platform_post_url": f"https://{platform}.com/post/{post_id}",
        "publish_mode": "mock",
    }


def _should_use_real_publish(user_id: str, platform: str, db: SupabaseClient) -> bool:
    mode = get_settings().cf_export_mode.strip().lower()
    if mode == "mock":
        return False
    if mode == "real":
        return is_cf_platform_connected(user_id, platform, db)
    # auto: real when Composio connected + key present
    if not get_settings().composio_api_key.strip():
        return False
    return is_cf_platform_connected(user_id, platform, db)


def _resolve_asset_for_entry(
    db: SupabaseClient,
    user_id: str,
    entry: dict[str, Any],
) -> dict[str, Any] | None:
    asset_id = entry.get("asset_id")
    if not asset_id:
        return None
    rows = db.select(
        "cf_assets",
        filters={"id": asset_id, "user_id": user_id},
        limit=1,
    )
    return rows[0] if rows else None


def _run_publish_with_retries(
    *,
    platform: str,
    user_id: str,
    entry: dict[str, Any],
    asset: dict[str, Any],
    adapted: dict[str, Any],
    export_id: str,
    db: SupabaseClient,
) -> dict[str, Any]:
    """Real publish with exponential backoff; falls back to mock if asset missing."""
    storage_path = asset.get("file_url") or ""
    if storage_path.startswith("http"):
        raise RuntimeError("Asset storage path missing — re-upload the file")

    last_error: Exception | None = None
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            media_bytes = download_cf_asset_bytes(db, storage_path)
            result = publish_cf_to_platform(
                platform,
                user_id,
                entry,
                asset,
                adapted,
                media_bytes,
            )
            result["publish_mode"] = "real"
            return result
        except Exception as exc:
            last_error = exc
            logger.warning(
                "cf export %s publish attempt %s/%s failed: %s",
                export_id,
                attempt,
                _MAX_RETRIES,
                exc,
            )
            if attempt < _MAX_RETRIES:
                time.sleep(_RETRY_BACKOFF_SEC * attempt)

    raise RuntimeError(str(last_error) if last_error else "Publish failed after retries")


def run_cf_export(export_id: str, user_id: str, db: SupabaseClient | None = None) -> None:
    """Process export: format_adapter → real or mock publish → update rows."""
    db = db or get_cf_supabase()
    entry_id: str | None = None
    try:
        rows = db.select("cf_exports", filters={"id": export_id, "user_id": user_id}, limit=1)
        if not rows:
            logger.warning("cf export %s not found", export_id)
            return
        export_row = rows[0]
        platform = export_row["platform"]
        entry_id = export_row["calendar_entry_id"]

        db.update(
            "cf_exports",
            export_id,
            {
                "status": "processing",
                "started_at": datetime.now(timezone.utc).isoformat(),
            },
        )

        entries = db.select(
            "cf_calendar_entries",
            filters={"id": entry_id, "user_id": user_id},
            limit=1,
        )
        if not entries:
            raise RuntimeError("Entrée calendrier introuvable")
        entry = entries[0]

        adapted = adapt_cf_for_platform(entry, platform)
        use_real = _should_use_real_publish(user_id, platform, db)
        asset = _resolve_asset_for_entry(db, user_id, entry)

        if use_real and asset:
            publish_result = _run_publish_with_retries(
                platform=platform,
                user_id=user_id,
                entry=entry,
                asset=asset,
                adapted=adapted,
                export_id=export_id,
                db=db,
            )
        elif use_real and not asset:
            raise RuntimeError(
                "Export réel impossible : associe un asset à l'entrée calendrier"
            )
        else:
            time.sleep(0.5)
            publish_result = _mock_publish(platform, export_id)

        completed = datetime.now(timezone.utc).isoformat()
        merged_meta = {**adapted, **publish_result}
        db.update(
            "cf_exports",
            export_id,
            {
                "status": "success",
                "platform_post_id": publish_result["platform_post_id"],
                "platform_post_url": publish_result["platform_post_url"],
                "adapted_metadata": merged_meta,
                "completed_at": completed,
            },
        )
        db.update("cf_calendar_entries", entry_id, {"status": "exported"})
        logger.info(
            "cf export %s success (%s) → %s",
            export_id,
            publish_result.get("publish_mode", "mock"),
            publish_result["platform_post_url"],
        )
    except Exception as exc:
        logger.exception("cf export %s failed", export_id)
        try:
            db.update(
                "cf_exports",
                export_id,
                {
                    "status": "failed",
                    "error_message": str(exc)[:2000],
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            if entry_id:
                db.update("cf_calendar_entries", entry_id, {"status": "failed"})
        except Exception:
            pass
        try:
            emit(
                "cf_export_failed",
                {
                    "export_id": export_id,
                    "user_id": user_id,
                    "error": str(exc)[:500],
                },
                source_agent="creatorflow",
            )
        except Exception:
            pass


def analyze_and_persist_asset(asset_id: str, user_id: str, db: SupabaseClient | None = None) -> None:
    """Background: LLM analysis → cf_assets.ai_analysis + status analyzed."""
    from agents.cf_content_analyzer import analyze_cf_asset

    db = db or get_cf_supabase()
    try:
        rows = db.select("cf_assets", filters={"id": asset_id, "user_id": user_id}, limit=1)
        if not rows:
            return
        analysis = analyze_cf_asset(rows[0])
        db.update(
            "cf_assets",
            asset_id,
            {"ai_analysis": analysis, "status": "analyzed"},
        )
    except Exception as exc:
        logger.warning("analyze_and_persist_asset %s: %s", asset_id, exc)
