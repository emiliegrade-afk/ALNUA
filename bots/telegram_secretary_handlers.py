"""Nadia Telegram handlers — split from telegram_secretary_bot (Vague 5)."""

from __future__ import annotations

import asyncio
import datetime as dt
import logging
from typing import TYPE_CHECKING, Any
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import ContextTypes

from bots.base import log_bot_action
from bots.telegram_common import split_message
from bots.telegram_secretary_auth import is_authorized, reject_unauthorized

if TYPE_CHECKING:
    from bots.telegram_secretary_bot import TelegramSecretaryBot

logger = logging.getLogger(__name__)

BOT_NAME = "telegram_secretary_bot"
_MORNING_JOB = "nadia_morning_brief"
_PARIS = ZoneInfo("Europe/Paris")

_START_MESSAGE = (
    "Bonjour Emilie, c'est **Nadia** — ta secrétaire ALNUA.\n\n"
    "Parle-moi en langage naturel — texte ou **vocal** Telegram.\n"
    "• Mails & brouillons (puis « envoie le mail » pour valider)\n"
    "• Contrats & réunions · Planning & agenda\n"
    "• Academy, pipeline, rapport de nuit\n"
    "• Météo (« quel temps à Paris ») · recherches\n"
    "• « Demande à Aria de… » — je transmets au COO\n\n"
    "Raccourcis :\n"
    "/rapport — bilan Academy de la nuit\n"
    "/briefing ou /priorities — priorités du jour\n"
    "/status — Hub en ligne ou non\n"
    "/connect gmail — lier Gmail\n"
    "/connect calendar — lier Google Calendar\n"
    "/apps — apps connectées"
)


def run_nadia(bot: TelegramSecretaryBot, instruction: str, chat_id: int | None) -> str:
    from services.assistant_router import assistant_chat

    result = assistant_chat(
        instruction,
        agent="secretary",
        telegram_chat_id=chat_id,
        session_id=bot._session_id(chat_id),
        channel="telegram_secretary",
    )
    name = result.get("agent_name") or "Nadia"
    body = result.get("response") or ""
    if result.get("agent_id") == "coo":
        return f"[{name}]\n{body}"
    return body


def morning_message() -> str:
    from services.secretary_intents import build_combined_morning_message

    return build_combined_morning_message()


async def send_morning_brief(
    bot: TelegramSecretaryBot, context: ContextTypes.DEFAULT_TYPE
) -> None:
    chat_id = bot._chat_id()
    if chat_id is None:
        logger.warning("Brief Nadia ignoré — TELEGRAM_SECRETARY_CHAT_ID manquant")
        return
    try:
        text = await asyncio.to_thread(morning_message)
        log_bot_action(bot.db, BOT_NAME, "morning_brief", "scheduled", text[:200])
    except Exception:
        logger.exception("Brief matinal Nadia échoué")
        text = "Brief matinal indisponible — erreur de génération."
        log_bot_action(
            bot.db, BOT_NAME, "morning_brief", "scheduled", text, status="error"
        )
    for chunk in split_message(text):
        await context.bot.send_message(chat_id=chat_id, text=chunk)
    try:
        from services.telegram_voice import send_overlay_voice_via_bot

        await send_overlay_voice_via_bot(context.bot, chat_id, text)
    except Exception:
        logger.warning("Brief Nadia overlay vocal ignoré", exc_info=True)


async def schedule_morning_brief(bot: TelegramSecretaryBot, application: Any) -> None:
    if application.job_queue is None:
        return
    for job in application.job_queue.get_jobs_by_name(_MORNING_JOB):
        job.schedule_removal()
    if getattr(bot.settings, "scheduler_leader", True):
        logger.info(
            "Brief 8h Nadia bot désactivé (SCHEDULER_LEADER=1 — Hub envoie le digest)"
        )
        return
    if bot._chat_id() is None:
        logger.warning(
            "Brief 8h Nadia désactivé — définis TELEGRAM_SECRETARY_CHAT_ID "
            "(ou envoie /start au bot et copie le chat ID)."
        )
        return
    async def _job(ctx: ContextTypes.DEFAULT_TYPE) -> None:
        await send_morning_brief(bot, ctx)

    application.job_queue.run_daily(
        _job,
        time=dt.time(hour=8, minute=0, tzinfo=_PARIS),
        name=_MORNING_JOB,
    )
    logger.info("Brief Nadia planifié à 08:00 %s", _PARIS)


def start_reply(bot: TelegramSecretaryBot, chat_id: int) -> str:
    lines = [_START_MESSAGE, "", f"Ton chat ID : `{chat_id}`"]
    configured = bot._chat_id()
    if configured == chat_id:
        lines.append("\n✅ Brief automatique activé à 8h (Paris).")
    elif configured is None:
        lines.append(
            f"\nAjoute dans `.env` :\n`TELEGRAM_SECRETARY_CHAT_ID={chat_id}`"
        )
    return "\n".join(lines)


async def handle_start(
    bot: TelegramSecretaryBot, update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    if not update.message or not update.effective_chat:
        return
    chat_id = update.effective_chat.id
    logger.info("Nadia bot chat ID: %s", chat_id)
    print(f"TELEGRAM_SECRETARY_CHAT_ID={chat_id}")
    await update.message.reply_text(start_reply(bot, chat_id), parse_mode="Markdown")


async def reply_nadia(bot: TelegramSecretaryBot, update: Update, text: str) -> None:
    if not update.message or not text:
        return
    chat_id = update.effective_chat.id if update.effective_chat else None

    from bots.telegram_delivery import reply_with_ack
    from services.telegram_ack import summarize_task_nadia

    def _log(inp: str, out: str, status: str) -> None:
        log_bot_action(bot.db, BOT_NAME, "message_received", inp, "")
        log_bot_action(
            bot.db, BOT_NAME, "secretary_response", inp, out, status=status
        )

    await reply_with_ack(
        update,
        agent_name="Nadia",
        task_summary=summarize_task_nadia(text),
        run=lambda: run_nadia(bot, text, chat_id),
        on_logged=_log,
        chat_id=chat_id,
        instruction=text,
        voice_agent_id="secretary",
    )


async def handle_rapport(
    bot: TelegramSecretaryBot, update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    if not is_authorized(update):
        await reject_unauthorized(update)
        return
    await reply_nadia(bot, update, "rapport de la nuit sur l'Academy")


async def handle_briefing(
    bot: TelegramSecretaryBot, update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    if not is_authorized(update):
        await reject_unauthorized(update)
        return
    await reply_nadia(bot, update, "briefing du jour")


async def handle_text(
    bot: TelegramSecretaryBot, update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    if not update.message or not update.message.text:
        return
    if not is_authorized(update):
        await reject_unauthorized(update)
        return
    chat_id = update.effective_chat.id if update.effective_chat else 0
    from services.rate_limiter import TELEGRAM_LIMIT, telegram_limiter

    if not telegram_limiter.is_allowed(f"tg:{chat_id}", TELEGRAM_LIMIT):
        await update.message.reply_text(
            "⏳ Trop de messages — attends 1 minute avant de réessayer."
        )
        return
    from services.input_sanitizer import sanitize_user_input

    safe_text = sanitize_user_input(update.message.text.strip(), max_length=4000)
    if not safe_text:
        return
    await reply_nadia(bot, update, safe_text)
