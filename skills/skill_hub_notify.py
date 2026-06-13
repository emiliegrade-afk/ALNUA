"""Notifications Hub — Telegram + Discord dev-log."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def notify_hub(message: str) -> dict[str, Any]:
    """
    Envoie un résumé d'orchestration sur les canaux configurés.
    Dégradé silencieux si un canal manque.
    """
    result: dict[str, Any] = {"telegram": False, "discord": False}

    try:
        from skills.skill_telegram_notify import notify_telegram

        result["telegram"] = notify_telegram(message)
    except Exception as exc:
        logger.debug("notify_hub telegram: %s", exc)

    try:
        from skills.skill_discord_wyrdheim import discord_is_configured, post_to_discord

        if discord_is_configured():
            resp = post_to_discord("dev-log", message[:1900])
            result["discord"] = bool(resp.get("success"))
    except Exception as exc:
        logger.debug("notify_hub discord: %s", exc)

    return result
