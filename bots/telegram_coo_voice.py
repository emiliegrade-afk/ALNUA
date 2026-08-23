"""Aria Telegram — voice-note intake (Lot 4). COO bot stays separate from Nadia."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from telegram import Update
from telegram.ext import ContextTypes

from bots.base import log_bot_action
from bots.telegram_auth import is_authorized, reject_unauthorized
from bots.telegram_commands import BOT_NAME

if TYPE_CHECKING:
    from bots.telegram_bot_core import TelegramBot

logger = logging.getLogger(__name__)

_STT_TIMEOUT_S = 45.0


async def reply_aria(bot: TelegramBot, update: Update, text: str) -> None:
    if not update.message or not text:
        return
    chat_id = update.effective_chat.id if update.effective_chat else None

    from bots.telegram_delivery import reply_with_ack
    from services.telegram_ack import summarize_task_aria

    def _log(inp: str, out: str, status: str) -> None:
        log_bot_action(bot.db, BOT_NAME, "message_received", inp, "")
        log_bot_action(bot.db, BOT_NAME, "coo_response", inp, out, status=status)

    await reply_with_ack(
        update,
        agent_name="Aria",
        task_summary=summarize_task_aria(text),
        run=lambda: bot._run_coo(text, chat_id),
        on_logged=_log,
        chat_id=chat_id,
        instruction=text,
        voice_agent_id="coo",
    )


async def handle_voice(
    bot: TelegramBot,
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if not update.message:
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

    from services.telegram_voice import download_telegram_voice, transcribe_voice_file

    voice = update.message.voice
    if voice is None:
        await update.message.reply_text("Vocal introuvable — réessaie ou écris-moi.")
        return
    if (voice.file_size or 0) > 2_000_000:
        await update.message.reply_text("Vocal trop long — envoie un message plus court.")
        return

    try:
        await update.message.chat.send_action("typing")
    except Exception:
        pass

    path = await download_telegram_voice(update, context)
    if path is None:
        await update.message.reply_text(
            "Je n'ai pas pu récupérer le vocal — réessaie ou écris-moi."
        )
        return
    try:
        raw = await asyncio.wait_for(
            asyncio.to_thread(transcribe_voice_file, path),
            timeout=_STT_TIMEOUT_S,
        )
    except Exception:
        logger.warning("Aria STT timeout/error", exc_info=True)
        raw = ""
    finally:
        try:
            path.unlink(missing_ok=True)
        except Exception:
            pass

    if not (raw or "").strip():
        await update.message.reply_text(
            "Je n'ai pas compris le vocal. Réessaie un peu plus près, ou écris-moi."
        )
        return

    from services.input_sanitizer import sanitize_user_input

    safe_text = sanitize_user_input(raw.strip(), max_length=4000)
    if not safe_text:
        return
    await reply_aria(bot, update, safe_text)
