"""Telegram notifications for fix_pipeline outcomes."""
from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


async def _notify(message: str) -> None:
    try:
        from api.telegram_bot import get_telegram_bot

        bot = get_telegram_bot()
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        if chat_id:
            await bot.bot.send_message(chat_id=int(chat_id), text=message)
    except Exception as exc:
        logger.warning("Telegram notification failed: %s", exc)
