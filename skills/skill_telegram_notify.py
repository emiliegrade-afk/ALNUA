"""Envoi de notifications Telegram depuis le Hub (sans démarrer le bot polling)."""

from __future__ import annotations

import logging

import httpx

from config.settings import get_settings

logger = logging.getLogger(__name__)

_TELEGRAM_MAX = 4096


def notify_telegram(message: str, chat_id: int | None = None) -> bool:
    """
    Envoie un message via le bot COO (TELEGRAM_BOT_TOKEN).
    Retourne False si non configuré ou en cas d'échec (dégradé silencieux).
    """
    settings = get_settings()
    token = settings.telegram_bot_token.strip()
    return _send_telegram(token, message, chat_id, settings.telegram_chat_id.strip())


def notify_telegram_secretary(message: str, chat_id: int | None = None) -> bool:
    """
    Envoie un message via le bot Nadia (TELEGRAM_SECRETARY_BOT_TOKEN).
    Fallback sur le bot COO si le token secrétaire n'est pas défini.
    """
    settings = get_settings()
    token = settings.telegram_secretary_bot_token.strip() or settings.telegram_bot_token.strip()
    default_chat = settings.telegram_secretary_chat_id_effective
    return _send_telegram(token, message, chat_id, default_chat)


def _send_telegram(
    token: str,
    message: str,
    chat_id: int | None,
    default_chat_raw: str,
) -> bool:
    if not token:
        logger.debug("Telegram notify ignoré — token manquant")
        return False

    target = chat_id
    if target is None:
        chat_raw = default_chat_raw
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
