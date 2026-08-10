"""Telegram secretary bot — owner chat authorization."""

from __future__ import annotations

import logging

from telegram import Update

from config.settings import get_settings

logger = logging.getLogger(__name__)

_UNAUTHORIZED_REPLY = (
    "⛔ Ce bot est réservé à son propriétaire.\n"
    "Si c'est toi : envoie /start, copie ton chat ID, "
    "mets TELEGRAM_SECRETARY_CHAT_ID=<id> dans .env, puis redémarre le bot."
)


def authorized_chat_id() -> int | None:
    raw = get_settings().telegram_secretary_chat_id_effective
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        logger.error("TELEGRAM_SECRETARY_CHAT_ID invalide : %r", raw)
        return None


def is_authorized(update: Update) -> bool:
    chat = update.effective_chat
    if chat is None:
        return False
    owner = authorized_chat_id()
    return owner is not None and chat.id == owner


async def reject_unauthorized(update: Update) -> None:
    if update.message:
        await update.message.reply_text(_UNAUTHORIZED_REPLY)
    logger.warning(
        "Unauthorized Telegram (Nadia) command from chat %s",
        update.effective_chat.id if update.effective_chat else "?",
    )
