"""Nadia Telegram — voice-note intake (Lot 1). Keep handlers file slim."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from telegram import Update
from telegram.ext import ContextTypes

from bots.telegram_secretary_auth import is_authorized, reject_unauthorized
from bots.telegram_secretary_handlers import reply_nadia

if TYPE_CHECKING:
    from bots.telegram_secretary_bot import TelegramSecretaryBot

logger = logging.getLogger(__name__)

_STT_TIMEOUT_S = 45.0


async def handle_voice(
    bot: TelegramSecretaryBot,
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
        logger.warning("Nadia STT timeout/error", exc_info=True)
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
    await reply_nadia(bot, update, safe_text)
