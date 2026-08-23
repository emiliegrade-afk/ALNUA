"""TelegramBot class — COO agent routing and application lifecycle."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from telegram import Update
from telegram.error import Conflict
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from bots.telegram_auth import is_authorized, reject_unauthorized
from bots.telegram_bot_morning import schedule_morning_brief, start_reply
from bots.telegram_callbacks import button_callback
from bots.telegram_commands import (
    agents_command,
    cmd_apps,
    cmd_connect,
    cmd_status,
    costs_command,
    idee_command,
    pipeline_command,
    prs_command,
)
from bots.telegram_common import acquire_single_instance_lock, presence_callbacks
from bots.telegram_coo_voice import handle_voice, reply_aria
from config.settings import get_settings
from database.supabase_client import get_supabase
from services.telegram_presence import BACK_MESSAGE_ARIA, COFFEE_MESSAGE_ARIA

logger = logging.getLogger(__name__)

_LOCK_FILE = Path(__file__).resolve().parent.parent / ".telegram_bot.lock"

START_MESSAGE = (
    "Salut Emilie ! Je suis **Aria Voss**, COO ALNUA.\n\n"
    "Parle-moi en langage naturel — texte ou **vocal** Telegram. "
    "Je réponds toujours ; je ne parle à voix haute que s'il y a une alerte, "
    "une action ou une décision.\n\n"
    "Raccourcis :\n"
    "/idee … — idée Centre R&D\n"
    "/pipeline · /prs · /costs · /agents · /status\n\n"
    "_Mails, contrats, planning → **Nadia**._"
)


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    if isinstance(context.error, Conflict):
        logger.warning(
            "409 Conflict: another bot instance is polling. "
            "Stop duplicate processes (task manager or Ctrl+C)."
        )
        return
    logger.error("Telegram handler error", exc_info=context.error)
    if isinstance(update, Update) and update.message:
        try:
            await update.message.reply_text(
                "❌ Souci technique côté Aria — réessaie dans un instant. "
                "Si ça persiste : `Demarrer-Hub.bat` puis /status"
            )
        except Exception:
            pass


class TelegramBot:
    """Routes Telegram messages to the COO agent and replies in the same chat."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.db = get_supabase()
        self._application: Application | None = None
        self._started = False

    def _ensure_token(self) -> str:
        token = self.settings.telegram_bot_token
        if not token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")
        return token

    def _run_coo(self, instruction: str, chat_id: int | None = None) -> str:
        from services.assistant_router import assistant_chat

        result = assistant_chat(
            instruction,
            agent="auto",
            telegram_chat_id=chat_id,
            channel="telegram_coo",
        )
        name = result.get("agent_name") or "Aria"
        body = result.get("response") or ""
        if result.get("agent_id") == "secretary":
            return f"[{name}]\n{body}"
        return body

    def _run_morning_briefing(self) -> str:
        from services.secretary_intents import build_morning_brief_for_secretary

        return build_morning_brief_for_secretary()

    async def _handle_start(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if not update.message or not update.effective_chat:
            return

        chat_id = update.effective_chat.id
        logger.info("Telegram chat ID: %s", chat_id)
        print(f"TELEGRAM_CHAT_ID={chat_id}")

        await update.message.reply_text(start_reply(chat_id, start_message=START_MESSAGE))

    async def _handle_text(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if not update.message or not update.message.text:
            return

        text = update.message.text.strip()
        if not text:
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
        from services.input_sanitizer import sanitize_user_input

        text = sanitize_user_input(text, max_length=4000)
        if not text:
            return

        await reply_aria(self, update, text)

    async def _handle_voice(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        await handle_voice(self, update, context)

    def build_application(self) -> Application:
        if self._application is None:
            token = self._ensure_token()
            from bots.telegram_auth import authorized_chat_id

            presence_init, presence_stop = presence_callbacks(
                token=token,
                chat_id=authorized_chat_id(),
                back_message=BACK_MESSAGE_ARIA,
                coffee_message=COFFEE_MESSAGE_ARIA,
            )

            async def _post_init(app: Application) -> None:
                await schedule_morning_brief(
                    app,
                    secretary_token=self.settings.telegram_secretary_bot_token,
                    run_briefing=self._run_morning_briefing,
                    db=self.db,
                )
                await presence_init(app)

            app = (
                Application.builder()
                .token(token)
                .post_init(_post_init)
                .post_shutdown(presence_stop)
                .build()
            )
            app.add_handler(CommandHandler("start", self._handle_start))
            app.add_handler(CommandHandler("idee", idee_command))
            app.add_handler(CommandHandler("pipeline", pipeline_command))
            app.add_handler(CommandHandler("prs", prs_command))
            app.add_handler(CommandHandler("costs", costs_command))
            app.add_handler(CommandHandler("agents", agents_command))
            app.add_handler(CommandHandler("status", cmd_status))
            app.add_handler(CommandHandler("connect", cmd_connect))
            app.add_handler(CommandHandler("apps", cmd_apps))
            app.add_handler(CallbackQueryHandler(button_callback))
            app.add_handler(
                MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_text)
            )
            app.add_handler(
                MessageHandler(filters.VOICE, self._handle_voice)
            )
            app.add_error_handler(on_error)
            self._application = app
        return self._application

    async def ensure_started(self) -> Application:
        """Initialize PTB application for webhook mode (FastAPI)."""
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
        logger.info("Telegram bot starting in polling mode")
        app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
