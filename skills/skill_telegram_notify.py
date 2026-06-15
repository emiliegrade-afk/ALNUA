"""Envoi de notifications Telegram depuis le Hub (sans démarrer le bot polling)."""

from __future__ import annotations

import logging

import httpx

from config.settings import get_settings

logger = logging.getLogger(__name__)

_TELEGRAM_MAX = 4096


def notify_telegram(message: str, chat_id: int | None = None) -> bool:
    """
    Envoie un message à chat_id ou TELEGRAM_CHAT_ID (fallback).
    Retourne False si non configuré ou en cas d'échec (dégradé silencieux).
    """
    settings = get_settings()
    token = settings.telegram_bot_token.strip()
    if not token:
        logger.debug("Telegram notify ignoré — token manquant")
        return False

    target = chat_id
    if target is None:
        chat_raw = settings.telegram_chat_id.strip()
        if not chat_raw:
            logger.debug("Telegram notify ignoré — chat_id manquant")
            return False
        try:
            target = int(chat_raw)
        except ValueError:
            logger.warning("TELEGRAM_CHAT_ID invalide : %r", chat_raw)
            return False

    text = message.strip()
    if not text:
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        with httpx.Client(timeout=15.0) as client:
            for i in range(0, len(text), _TELEGRAM_MAX):
                chunk = text[i : i + _TELEGRAM_MAX]
                resp = client.post(
                    url,
                    json={"chat_id": target, "text": chunk},
                )
                resp.raise_for_status()
        return True
    except Exception as exc:
        logger.warning("notify_telegram failed: %s", exc)
        return False
