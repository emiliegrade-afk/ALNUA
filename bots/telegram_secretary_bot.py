"""Telegram Bot — Nadia Faure, secrétaire ALNUA (bot dédié, séparé du COO)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

from bots.telegram_common import acquire_single_instance_lock, presence_callbacks
from bots.telegram_secretary_commands import cmd_apps, cmd_connect, cmd_status, on_error
from bots.telegram_secretary_handlers import (
    handle_briefing,
    handle_rapport,
    handle_start,
    handle_text,
    schedule_morning_brief,
)
from bots.telegram_secretary_voice import handle_voice
from config.settings import get_settings
from database.supabase_client import get_supabase
from services.telegram_presence import BACK_MESSAGE_NADIA, COFFEE_MESSAGE_NADIA

logger = logging.getLogger(__name__)

_LOCK_FILE = Path(__file__).resolve().parent.parent / ".telegram_secretary_bot.lock"


class TelegramSecretaryBot:
    """Routes Telegram messages to SecretaryAgent (Nadia)."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.db = get_supabase()
        self._application: Application | None = None
        self._started = False

    def _ensure_token(self) -> str:
        token = self.settings.telegram_secretary_bot_token.strip()
        if not token:
            raise RuntimeError("TELEGRAM_SECRETARY_BOT_TOKEN non configuré dans .env")
        return token

    def _chat_id(self) -> int | None:
        raw = self.settings.telegram_secretary_chat_id_effective
        if not raw:
            return None
        try:
            return int(raw)
        except ValueError:
            logger.error("TELEGRAM_SECRETARY_CHAT_ID invalide : %r", raw)
            return None

    def _session_id(self, chat_id: int | None) -> str:
        return f"tg:{chat_id}" if chat_id is not None else "hub"

    def build_application(self) -> Application:
        if self._application is None:
            token = self._ensure_token()
            presence_init, presence_stop = presence_callbacks(
                token=token,
                chat_id=self._chat_id(),
                back_message=BACK_MESSAGE_NADIA,
                coffee_message=COFFEE_MESSAGE_NADIA,
            )

            async def _post_init(app: Application) -> None:
                await schedule_morning_brief(self, app)
                await presence_init(app)

            app = (
                Application.builder()
                .token(token)
                .post_init(_post_init)
                .post_shutdown(presence_stop)
                .build()
            )
            app.add_handler(CommandHandler("start", lambda u, c: handle_start(self, u, c)))
            app.add_handler(CommandHandler("rapport", lambda u, c: handle_rapport(self, u, c)))
            app.add_handler(CommandHandler("briefing", lambda u, c: handle_briefing(self, u, c)))
            app.add_handler(
                CommandHandler("priorities", lambda u, c: handle_briefing(self, u, c))
            )
            app.add_handler(CommandHandler("status", cmd_status))
            app.add_handler(CommandHandler("connect", cmd_connect))
            app.add_handler(CommandHandler("apps", cmd_apps))
            app.add_handler(
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    lambda u, c: handle_text(self, u, c),
                )
            )
            app.add_handler(
                MessageHandler(
                    filters.VOICE,
                    lambda u, c: handle_voice(self, u, c),
                )
            )
            app.add_error_handler(on_error)
            self._application = app
        return self._application

    async def ensure_started(self) -> Application:
        app = self.build_application()
        if not self._started:
            await app.initialize()
            await app.start()
            self._started = True
        return app

    async def process_update(self, update_data: dict[str, Any]) -> None:
        app = await self.ensure_started()
        update = Update.de_json(update_data, app.bot)
        await app.process_update(update)

    async def shutdown(self) -> None:
        if self._application is not None and self._started:
            await self._application.stop()
            await self._application.shutdown()
            self._started = False

    def run_polling(self) -> None:
        acquire_single_instance_lock(_LOCK_FILE)
        logging.basicConfig(level=logging.INFO)
        app = self.build_application()
        logger.info("Bot Telegram Nadia — polling démarré")
        app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


_bot: TelegramSecretaryBot | None = None


def get_telegram_secretary_bot() -> TelegramSecretaryBot:
    global _bot
    if _bot is None:
        _bot = TelegramSecretaryBot()
    return _bot


def run_telegram_secretary_bot() -> None:
    get_telegram_secretary_bot().run_polling()


if __name__ == "__main__":
    run_telegram_secretary_bot()
