"""Telegram Bot — Nadia Faure, secrétaire ALNUA (bot dédié, séparé du COO)."""

from __future__ import annotations

import asyncio
import datetime as dt
import logging
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from bots.base import log_bot_action
from bots.telegram_common import acquire_single_instance_lock, presence_callbacks, split_message
from bots.telegram_secretary_auth import is_authorized, reject_unauthorized
from bots.telegram_secretary_commands import cmd_apps, cmd_connect, cmd_status, on_error
from config.settings import get_settings
from database.supabase_client import get_supabase
from services.telegram_presence import BACK_MESSAGE_NADIA, COFFEE_MESSAGE_NADIA

logger = logging.getLogger(__name__)

BOT_NAME = "telegram_secretary_bot"
_LOCK_FILE = Path(__file__).resolve().parent.parent / ".telegram_secretary_bot.lock"
_MORNING_JOB = "nadia_morning_brief"
_PARIS = ZoneInfo("Europe/Paris")

_START_MESSAGE = (
    "Bonjour Emilie, c'est **Nadia** — ta secrétaire ALNUA.\n\n"
    "Parle-moi en langage naturel, comme un chat — je réponds toujours.\n"
    "• Mails & brouillons (puis « envoie le mail » pour valider)\n"
    "• Contrats & réunions · Planning & agenda\n"
    "• Academy, pipeline, rapport de nuit\n"
    "• « Demande à Aria de… » — je transmets au COO\n\n"
    "Raccourcis :\n"
    "/rapport — bilan Academy de la nuit\n"
    "/briefing ou /priorities — priorités du jour\n"
    "/status — Hub en ligne ou non\n"
    "/connect gmail — lier Gmail\n"
    "/connect calendar — lier Google Calendar\n"
    "/apps — apps connectées"
)


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

    def _run_nadia(self, instruction: str, chat_id: int | None) -> str:
        from services.assistant_router import assistant_chat

        result = assistant_chat(
            instruction,
            agent="secretary",
            telegram_chat_id=chat_id,
            session_id=self._session_id(chat_id),
            channel="telegram_secretary",
        )
        name = result.get("agent_name") or "Nadia"
        body = result.get("response") or ""
        if result.get("agent_id") == "coo":
            return f"[{name}]\n{body}"
        return body

    def _morning_message(self) -> str:
        from services.secretary_intents import build_combined_morning_message

        return build_combined_morning_message()

    async def _send_morning_brief(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = self._chat_id()
        if chat_id is None:
            logger.warning("Brief Nadia ignoré — TELEGRAM_SECRETARY_CHAT_ID manquant")
            return
        try:
            text = await asyncio.to_thread(self._morning_message)
            log_bot_action(self.db, BOT_NAME, "morning_brief", "scheduled", text[:200])
        except Exception:
            logger.exception("Brief matinal Nadia échoué")
            text = "Brief matinal indisponible — erreur de génération."
            log_bot_action(
                self.db, BOT_NAME, "morning_brief", "scheduled", text, status="error"
            )
        for chunk in split_message(text):
            await context.bot.send_message(chat_id=chat_id, text=chunk)

    async def _schedule_morning_brief(self, application: Application) -> None:
        if application.job_queue is None:
            return
        for job in application.job_queue.get_jobs_by_name(_MORNING_JOB):
            job.schedule_removal()
        # Hub scheduler owns 8h when SCHEDULER_LEADER=1 — avoid duplicate Telegram digests
        if getattr(self.settings, "scheduler_leader", True):
            logger.info(
                "Brief 8h Nadia bot désactivé (SCHEDULER_LEADER=1 — Hub envoie le digest)"
            )
            return
        if self._chat_id() is None:
            logger.warning(
                "Brief 8h Nadia désactivé — définis TELEGRAM_SECRETARY_CHAT_ID "
                "(ou envoie /start au bot et copie le chat ID)."
            )
            return
        application.job_queue.run_daily(
            self._send_morning_brief,
            time=dt.time(hour=8, minute=0, tzinfo=_PARIS),
            name=_MORNING_JOB,
        )
        logger.info("Brief Nadia planifié à 08:00 %s", _PARIS)

    def _start_reply(self, chat_id: int) -> str:
        lines = [_START_MESSAGE, "", f"Ton chat ID : `{chat_id}`"]
        configured = self._chat_id()
        if configured == chat_id:
            lines.append("\n✅ Brief automatique activé à 8h (Paris).")
        elif configured is None:
            lines.append(
                f"\nAjoute dans `.env` :\n`TELEGRAM_SECRETARY_CHAT_ID={chat_id}`"
            )
        return "\n".join(lines)

    async def _handle_start(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if not update.message or not update.effective_chat:
            return
        chat_id = update.effective_chat.id
        logger.info("Nadia bot chat ID: %s", chat_id)
        print(f"TELEGRAM_SECRETARY_CHAT_ID={chat_id}")
        await update.message.reply_text(
            self._start_reply(chat_id), parse_mode="Markdown"
        )

    async def _handle_rapport(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if not is_authorized(update):
            await reject_unauthorized(update)
            return
        await self._reply_nadia(update, "rapport de la nuit sur l'Academy")

    async def _handle_briefing(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if not is_authorized(update):
            await reject_unauthorized(update)
            return
        await self._reply_nadia(update, "briefing du jour")

    async def _handle_text(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if not update.message or not update.message.text:
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

        safe_text = sanitize_user_input(update.message.text.strip(), max_length=4000)
        if not safe_text:
            return
        await self._reply_nadia(update, safe_text)

    async def _reply_nadia(self, update: Update, text: str) -> None:
        if not update.message or not text:
            return
        chat_id = update.effective_chat.id if update.effective_chat else None

        from bots.telegram_delivery import reply_with_ack
        from services.telegram_ack import summarize_task_nadia

        def _log(inp: str, out: str, status: str) -> None:
            log_bot_action(self.db, BOT_NAME, "message_received", inp, "")
            log_bot_action(
                self.db, BOT_NAME, "secretary_response", inp, out, status=status
            )

        await reply_with_ack(
            update,
            agent_name="Nadia",
            task_summary=summarize_task_nadia(text),
            run=lambda: self._run_nadia(text, chat_id),
            on_logged=_log,
            chat_id=chat_id,
            instruction=text,
        )

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
                await self._schedule_morning_brief(app)
                await presence_init(app)

            app = (
                Application.builder()
                .token(token)
                .post_init(_post_init)
                .post_shutdown(presence_stop)
                .build()
            )
            app.add_handler(CommandHandler("start", self._handle_start))
            app.add_handler(CommandHandler("rapport", self._handle_rapport))
            app.add_handler(CommandHandler("briefing", self._handle_briefing))
            app.add_handler(CommandHandler("priorities", self._handle_briefing))
            app.add_handler(CommandHandler("status", cmd_status))
            app.add_handler(CommandHandler("connect", cmd_connect))
            app.add_handler(CommandHandler("apps", cmd_apps))
            app.add_handler(
                MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_text)
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
