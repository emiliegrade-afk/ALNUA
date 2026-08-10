"""Fast init helpers for FastAPI lifespan."""

from __future__ import annotations

from typing import Any
from zoneinfo import ZoneInfo

from api.route_common import *  # noqa: F403


def scheduler_timezone(settings: Any) -> ZoneInfo:
    try:
        return ZoneInfo(settings.scheduler_timezone)
    except Exception:
        logger.warning(
            "Invalid SCHEDULER_TIMEZONE=%r - falling back to Europe/Paris",
            settings.scheduler_timezone,
        )
        return ZoneInfo("Europe/Paris")


def init_fast(settings: Any) -> None:
    """Minimal sync init so /health responds quickly."""
    if settings.sentry_dsn:
        sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=0.1)
        logger.info("Sentry initialized")
    try:
        from services.cli_paths import ensure_coding_cli_path

        ensure_coding_cli_path()
    except Exception:
        pass
    try:
        ensure_brand_kit_dirs()
    except Exception:
        logger.exception("Could not initialize brand_kits directories")
    try:
        ensure_contract_dirs()
    except Exception:
        logger.exception("Could not initialize contract directories")
    try:
        from services.otel import setup_otel

        setup_otel()
    except Exception:
        pass
    try:
        from models.tenant import DEFAULT_TENANT_ID
        from services.personality_store import load_personality_from_db

        load_personality_from_db(DEFAULT_TENANT_ID)
    except Exception:
        pass
