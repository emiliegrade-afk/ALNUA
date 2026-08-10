"""Telegram COO bot — morning brief scheduling."""

from __future__ import annotations

import asyncio
import datetime as dt
import logging
from zoneinfo import ZoneInfo

from telegram.ext import Application, ContextTypes

from bots.telegram_auth import authorized_chat_id
from bots.telegram_commands import BOT_NAME
from bots.telegram_common import split_message
from bots.base import log_bot_action

logger = logging.getLogger(__name__)

MORNING_BRIEF_JOB = "morning_brief"
MORNING_BRIEF_TZ = ZoneInfo("Europe/Paris")


async def send_morning_brief(
    context: ContextTypes.DEFAULT_TYPE,
    *,
    run_briefing,
    db,
) -> None:
    chat_id = authorized_chat_id()
    if chat_id is None:
        logger.warning("Morning brief skipped — TELEGRAM_CHAT_ID is not configured")
        return

    logger.info("Sending morning brief to chat %s", chat_id)
    try:
        briefing = await asyncio.to_thread(run_briefing)
        log_bot_action(
            db, BOT_NAME, "morning_brief", "scheduled", briefing[:200]
        )
    except Exception:
        logger.exception("Morning brief generation failed")
        briefing = "Brief matinal indisponible — erreur lors de la génération."
        log_bot_action(
            db,
            BOT_NAME,
            "morning_brief",
            "scheduled",
            briefing,
            status="error",
        )

    for chunk in split_message(briefing):
        await context.bot.send_message(chat_id=chat_id, text=chunk)


async def schedule_morning_brief(
    application: Application,
    *,
    secretary_token: str,
    run_briefing,
    db,
) -> None:
    if secretary_token.strip():
        logger.info(
            "Brief 8h COO désactivé — bot Nadia dédié (TELEGRAM_SECRETARY_BOT_TOKEN)"
        )
        return
    if application.job_queue is None:
        logger.warning("Job queue unavailable — morning brief not scheduled")
        return

    for job in application.job_queue.get_jobs_by_name(MORNING_BRIEF_JOB):
        job.schedule_removal()

    if authorized_chat_id() is None:
        logger.warning(
            "TELEGRAM_CHAT_ID not set — morning brief disabled. "
            "Send /start to the bot and copy the chat ID from the console."
        )
        return

    async def _callback(context: ContextTypes.DEFAULT_TYPE) -> None:
        await send_morning_brief(context, run_briefing=run_briefing, db=db)

    application.job_queue.run_daily(
        _callback,
        time=dt.time(hour=8, minute=0, tzinfo=MORNING_BRIEF_TZ),
        name=MORNING_BRIEF_JOB,
    )
    logger.info("Morning brief scheduled daily at 08:00 %s", MORNING_BRIEF_TZ)


def start_reply(chat_id: int, *, start_message: str) -> str:
    configured = authorized_chat_id()
    lines = [
        start_message,
        "",
        f"Ton chat ID : {chat_id}",
    ]

    if configured == chat_id:
        lines.append("")
        lines.append("Brief matinal activé — envoi automatique à 8h (Europe/Paris).")
    elif configured is not None:
        lines.append("")
        lines.append(
            "Le brief matinal pointe vers un autre chat. "
            f"Mets TELEGRAM_CHAT_ID={chat_id} dans .env, puis redémarre le bot."
        )
    else:
        lines.append("")
        lines.append("Pour activer le brief matinal à 8h, ajoute dans .env :")
        lines.append(f"TELEGRAM_CHAT_ID={chat_id}")
        lines.append("Puis redémarre le bot (Ctrl+C dans le terminal, relance).")
    return "\n".join(lines)
