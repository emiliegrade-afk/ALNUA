"""Telegram Bot — COO interface for ALNUA Hub."""

from __future__ import annotations

from bots.telegram_bot_core import TelegramBot

_telegram_bot: TelegramBot | None = None


def get_telegram_bot() -> TelegramBot:
    global _telegram_bot
    if _telegram_bot is None:
        _telegram_bot = TelegramBot()
    return _telegram_bot


def run_telegram_bot() -> None:
    get_telegram_bot().run_polling()


if __name__ == "__main__":
    run_telegram_bot()
