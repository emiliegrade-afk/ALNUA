"""Telegram bot authorization helpers."""

from __future__ import annotations

import logging

from telegram import Update

from config.settings import get_settings

logger = logging.getLogger(__name__)

UNAUTHORIZED_REPLY = (
    "⛔ Ce bot est réservé à son propriétaire.\n"
    "Si c'est toi : envoie /start, copie ton chat ID, "
    "mets TELEGRAM_CHAT_ID=<id> dans .env, puis redémarre le bot."
)


def authorized_chat_id() -> int | None:
    """Chat ID autorisé à piloter le bot — même source que le brief matinal."""
    raw = get_settings().telegram_chat_id.strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        logger.error("TELEGRAM_CHAT_ID invalid (expected integer): %r", raw)
        return None


def is_authorized(update: Update) -> bool:
    """
    Toute commande sauf /start doit venir du chat configuré dans TELEGRAM_CHAT_ID.
    Tant que la variable n'est pas configurée, aucune commande sensible n'est autorisée —
    seul /start reste ouvert pour permettre de découvrir son chat ID et le configurer.
    """
    chat = update.effective_chat
    if chat is None:
        return False
    owner = authorized_chat_id()
    return owner is not None and chat.id == owner


async def reject_unauthorized(update: Update) -> None:
    if update.message:
        await update.message.reply_text(UNAUTHORIZED_REPLY)
    logger.warning(
        "Unauthorized Telegram command from chat %s",
        update.effective_chat.id if update.effective_chat else "?",
    )
