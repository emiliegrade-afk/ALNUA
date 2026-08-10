"""FastAPI lifespan — fast /health first, heavy jobs deferred."""

from __future__ import annotations

from contextlib import asynccontextmanager

from api.lifespan_background import shutdown_briefing_scheduler, start_background_services
from api.lifespan_init import init_fast
from api.route_common import *  # noqa: F403


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    init_fast(settings)

    bg_task = asyncio.create_task(start_background_services(settings))

    yield

    bg_task.cancel()
    try:
        await bg_task
    except asyncio.CancelledError:
        pass

    try:
        from agents.bug_watchdog import stop_watchdog

        stop_watchdog()
    except Exception:
        logger.exception("BugWatchdog shutdown failed")

    if settings.telegram_bot_token:
        try:
            await get_telegram_bot().shutdown()
        except Exception:
            logger.exception("Telegram COO bot shutdown failed")

    if settings.telegram_secretary_bot_token:
        try:
            from bots.telegram_secretary_bot import get_telegram_secretary_bot

            await get_telegram_secretary_bot().shutdown()
        except Exception:
            logger.exception("Telegram Nadia bot shutdown failed")

    shutdown_briefing_scheduler()
