"""Telegram Bot — COO interface for ALNUA Hub."""

from __future__ import annotations

import asyncio
import atexit
import datetime as dt
import json
import logging
import os
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import httpx
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import Conflict
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from agents.coo_agent import COOAgent
from agents.dev_app_agent import DevAppAgent
from bots.base import log_bot_action
from bots.telegram_common import presence_callbacks
from config.settings import get_settings
from database.supabase_client import get_supabase
from skills.skill_gh_issues import get_open_prs, list_ready_issues
from services.facades.costs_facade import get_telegram_costs_report
from services.telegram_presence import (
    BACK_MESSAGE_ARIA,
    COFFEE_MESSAGE_ARIA,
    hub_status_line,
)

logger = logging.getLogger(__name__)

BOT_NAME = "telegram_bot"
TELEGRAM_CHUNK_SIZE = 4000
_LOCK_FILE = Path(__file__).resolve().parent.parent / ".telegram_bot.lock"

_START_MESSAGE = (
    "Salut Emilie ! Je suis **Aria Voss**, COO ALNUA.\n\n"
    "Parle-moi en langage naturel — comme un chat. Je réponds toujours, "
    "même si je ne peux pas tout exécuter.\n\n"
    "Raccourcis :\n"
    "/idee … — idée Centre R&D\n"
    "/pipeline · /prs · /costs · /agents · /status\n\n"
    "_Mails, contrats, planning → **Nadia**._"
)

_MORNING_BRIEF_JOB = "morning_brief"
_MORNING_BRIEF_TZ = ZoneInfo("Europe/Paris")
_REPO_ROOT = Path(__file__).resolve().parent.parent

_UNAUTHORIZED_REPLY = (
    "⛔ Ce bot est réservé à son propriétaire.\n"
    "Si c'est toi : envoie /start, copie ton chat ID, "
    "mets TELEGRAM_CHAT_ID=<id> dans .env, puis redémarre le bot."
)


def _hub_repo_path() -> str:
    return os.getenv("HUB_REPO_PATH", str(_REPO_ROOT))


def _authorized_chat_id() -> int | None:
    """Chat ID autorisé à piloter le bot — même source que le brief matinal."""
    raw = get_settings().telegram_chat_id.strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        logger.error("TELEGRAM_CHAT_ID invalid (expected integer): %r", raw)
        return None


def _is_authorized(update: Update) -> bool:
    """
    Toute commande sauf /start doit venir du chat configuré dans TELEGRAM_CHAT_ID.
    Tant que la variable n'est pas configurée, aucune commande sensible n'est autorisée —
    seul /start reste ouvert pour permettre de découvrir son chat ID et le configurer.
    """
    chat = update.effective_chat
    if chat is None:
        return False
    owner = _authorized_chat_id()
    return owner is not None and chat.id == owner


async def _reject_unauthorized(update: Update) -> None:
    if update.message:
        await update.message.reply_text(_UNAUTHORIZED_REPLY)
    logger.warning(
        "Unauthorized Telegram command from chat %s",
        update.effective_chat.id if update.effective_chat else "?",
    )


def _telegram_notify(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    """Build a notify callback that posts Markdown to the given chat."""

    def notify(msg: str) -> None:
        asyncio.create_task(
            context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
        )

    return notify


async def pipeline_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /pipeline — liste les issues prêtes et permet d'en lancer une
    /pipeline #42 — lance directement l'issue #42
    """
    if not update.message or not update.effective_chat:
        return
    if not _is_authorized(update):
        await _reject_unauthorized(update)
        return

    args = context.args
    chat_id = update.effective_chat.id

    if args and args[0].startswith("#"):
        issue_num = int(args[0][1:])
        repo_slug = args[1] if len(args) > 1 else None
        await update.message.reply_text(
            f"🔧 *Pipeline lancé*\nIssue #{issue_num} en cours de traitement...",
            parse_mode="Markdown",
        )
        agent = DevAppAgent(telegram_notify_fn=_telegram_notify(context, chat_id))
        context.application.create_task(
            asyncio.to_thread(agent.process_issue_by_number, issue_num, repo_slug)
        )
        return

    try:
        issues = list_ready_issues()
    except Exception as exc:
        await update.message.reply_text(f"❌ Erreur : {exc}")
        return

    if not issues:
        await update.message.reply_text(
            "✅ Aucune issue en attente.\n"
            "Pour créer une tâche, ouvre une issue GitHub avec le label `agent-ready`.",
            parse_mode="Markdown",
        )
        return

    keyboard = []
    for issue in issues[:8]:
        repo_name = issue.get("_repo_name", "Hub")
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"[{repo_name}] #{issue['number']} — {issue['title'][:32]}",
                    callback_data=json.dumps(
                        {
                            "action": "run_issue",
                            "number": issue["number"],
                            "repo": issue.get("_repo_slug"),
                        }
                    ),
                )
            ]
        )
    keyboard.append(
        [InlineKeyboardButton("❌ Annuler", callback_data='{"action":"cancel"}')]
    )

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"🔧 *{len(issues)} issue(s) prête(s)*\nChoisis laquelle lancer :",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )


async def idee_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /idee App vanlife offline — enregistre une idée dans le Centre R&D.
    Répondre à un message avec /idee reprend son texte.
    """
    if not update.message:
        return
    if not _is_authorized(update):
        await _reject_unauthorized(update)
        return

    idea_text = " ".join(context.args or []).strip()
    if not idea_text and update.message.reply_to_message and update.message.reply_to_message.text:
        idea_text = update.message.reply_to_message.text.strip()

    if not idea_text:
        await update.message.reply_text(
            "Usage : /idee App vanlife offline first\n"
            "Ou réponds /idee à un message pour le capturer.",
        )
        return

    try:
        from agents.rnd_center import inject_idea

        result = inject_idea(idea_text, source="Telegram")
        title = result.get("title", idea_text[:80])
        await update.message.reply_text(
            f"💡 Idée enregistrée : {title[:120]}\n"
            f"Centre R&D → Propositions (Hub /rd).",
        )
        log_bot_action(
            get_supabase(), BOT_NAME, "idee_capture", idea_text[:200], title[:200]
        )
    except Exception as exc:
        logger.exception("idee_command failed")
        await update.message.reply_text(f"❌ Erreur : {exc}")


async def prs_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/prs — liste les PRs ouvertes (tous repos) avec boutons actions."""
    if not update.message:
        return
    if not _is_authorized(update):
        await _reject_unauthorized(update)
        return

    if not os.getenv("GITHUB_TOKEN"):
        await update.message.reply_text("❌ GITHUB_TOKEN non configuré.")
        return

    try:
        prs = get_open_prs()

        if not prs:
            await update.message.reply_text("✅ Aucune PR ouverte.")
            return

        for pr in prs[:12]:
            number = pr["number"]
            title = pr["title"]
            repo_name = pr.get("repo_name", "Hub")
            auto_tag = "🤖 Auto" if pr.get("auto") else "👤"

            keyboard = [
                [
                    InlineKeyboardButton("🔍 Voir PR", url=pr["html_url"]),
                    InlineKeyboardButton(
                        "🧪 Lancer tests",
                        callback_data=json.dumps(
                            {
                                "action": "run_tests",
                                "pr": number,
                                "branch": pr["branch"],
                                "repo_path": pr.get("repo_path"),
                                "github_repo": pr.get("github_repo"),
                            }
                        ),
                    ),
                ]
            ]

            await update.message.reply_text(
                f"{auto_tag} *[{repo_name}] PR #{number}*\n{title}\n`{pr['branch']}`",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown",
            )

    except Exception as e:
        await update.message.reply_text(f"❌ Erreur : {e}")


async def costs_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/costs — rapport coûts LLM avec boutons jour/mois."""
    if not update.message:
        return
    if not _is_authorized(update):
        await _reject_unauthorized(update)
        return

    keyboard = [
        [
            InlineKeyboardButton(
                "📅 Aujourd'hui",
                callback_data='{"action":"costs","period":"day"}',
            ),
            InlineKeyboardButton(
                "📆 Ce mois",
                callback_data='{"action":"costs","period":"month"}',
            ),
        ]
    ]
    report = get_telegram_costs_report("day")
    await update.message.reply_text(
        report,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


_AGENTS_STATUS_TEXT = """🏢 *ALNUA — État des agents*

🟢 **COO Agent** — Actif
🟢 **Dev App Agent** — Actif
⚪ **R&D Agent** — En veille
⚪ **Computer Vision** — En veille
⚪ **Game Director** — En veille
⚪ **Dev Gaming** — En veille
⚪ **Art Director** — En veille
⚪ **Hardware** — En veille
⚪ **Embedded Dev** — En veille
⚪ **QA/Sécurité** — En veille
⚪ **Marketing** — En veille
⚪ **Admin** — Désactivé (on demand)"""


async def cmd_connect(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/connect <APP> — génère le lien OAuth Composio pour connecter une app."""
    if not update.message:
        return
    if not _is_authorized(update):
        await _reject_unauthorized(update)
        return
    if not context.args:
        await update.message.reply_text("Usage: /connect <APP>\nEx: /connect gmail")
        return
    app = context.args[0].upper()
    from skills.skill_composio import get_oauth_link
    from services.secretary_composio import composio_user_id

    link = get_oauth_link(app=app, user_id=composio_user_id())
    if link.startswith("Erreur:"):
        await update.message.reply_text(f"❌ {link}")
        return
    if "déjà connecté" in link:
        await update.message.reply_text(f"✅ {link}")
        return
    await update.message.reply_text(
        f"🔗 Connecte {app} :\n{link}\n\nOuvre ce lien dans ton navigateur."
    )


async def cmd_apps(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/apps — liste les apps Composio connectées pour le COO."""
    if not update.message:
        return
    if not _is_authorized(update):
        await _reject_unauthorized(update)
        return
    from skills.skill_composio import list_connected_apps
    from services.secretary_composio import composio_user_id

    apps = list_connected_apps(user_id=composio_user_id())
    if not apps:
        await update.message.reply_text(
            "Aucune app connectée. Utilise /connect <APP>"
        )
        return
    text = "📱 Apps connectées :\n" + "\n".join(
        f"• {a['app']} — {a['status']}" for a in apps
    )
    await update.message.reply_text(text)


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    if not _is_authorized(update):
        await _reject_unauthorized(update)
        return
    await update.message.reply_text(
        f"**Aria** — COO ALNUA\n{hub_status_line()}\n\n"
        "Mode chat actif : je réponds toujours. "
        "Si le Hub est 🔴, pas de pipeline / relance agents tant qu'il n'est pas relancé.",
        parse_mode="Markdown",
    )


async def agents_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/agents — état de tous les agents ALNUA."""
    keyboard = [
        [InlineKeyboardButton("🔄 Rafraîchir", callback_data='{"action":"refresh_agents"}')]
    ]
    message = update.message or (
        update.callback_query.message if update.callback_query else None
    )
    if not message:
        return
    if not _is_authorized(update):
        await _reject_unauthorized(update)
        return
    await message.reply_text(
        _AGENTS_STATUS_TEXT,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gère tous les clics sur les boutons inline."""
    query = update.callback_query
    if not query:
        return

    await query.answer()

    if not _is_authorized(update):
        logger.warning(
            "Unauthorized Telegram button callback from chat %s",
            update.effective_chat.id if update.effective_chat else "?",
        )
        await query.edit_message_text(_UNAUTHORIZED_REPLY)
        return

    try:
        data = json.loads(query.data or "{}")
    except json.JSONDecodeError:
        return

    action = data.get("action")
    chat_id = query.message.chat_id if query.message else None

    if action == "cancel":
        await query.edit_message_text("❌ Annulé.")

    elif action == "run_issue":
        issue_num = data["number"]
        repo_slug = data.get("repo")
        await query.edit_message_text(
            f"🔧 *Pipeline démarré*\nIssue #{issue_num} en cours de traitement...\n"
            f"Je te notifie quand c'est prêt.",
            parse_mode="Markdown",
        )
        if chat_id is not None:
            agent = DevAppAgent(telegram_notify_fn=_telegram_notify(context, chat_id))
            context.application.create_task(
                asyncio.to_thread(
                    agent.process_issue_by_number, issue_num, repo_slug
                )
            )

    elif action == "run_tests":
        branch = data.get("branch")
        pr_num = data.get("pr")
        repo_path = data.get("repo_path") or _hub_repo_path()
        github_repo = data.get("github_repo")
        await query.edit_message_text(
            f"🧪 *Tests QA lancés*\nBranche : `{branch}`\nPR #{pr_num}\n"
            f"Résultats dans quelques minutes...",
            parse_mode="Markdown",
        )
        if chat_id is not None:
            from skills.skill_playwright import run_and_report

            context.application.create_task(
                asyncio.to_thread(
                    run_and_report,
                    repo_path,
                    branch,
                    pr_num,
                    _telegram_notify(context, chat_id),
                    github_repo=github_repo,
                )
            )

    elif action == "costs":
        period = data.get("period", "day")
        report = get_telegram_costs_report(period)
        keyboard = [
            [
                InlineKeyboardButton(
                    "📅 Aujourd'hui",
                    callback_data='{"action":"costs","period":"day"}',
                ),
                InlineKeyboardButton(
                    "📆 Ce mois",
                    callback_data='{"action":"costs","period":"month"}',
                ),
            ]
        ]
        await query.edit_message_text(
            report,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    elif action == "refresh_agents":
        keyboard = [
            [
                InlineKeyboardButton(
                    "🔄 Rafraîchir",
                    callback_data='{"action":"refresh_agents"}',
                )
            ]
        ]
        await query.edit_message_text(
            _AGENTS_STATUS_TEXT,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )


def _split_message(text: str, chunk_size: int = TELEGRAM_CHUNK_SIZE) -> list[str]:
    if len(text) <= chunk_size:
        return [text]
    return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]


def _pid_is_running(pid: int) -> bool:
    """Check whether a process is alive (Windows-safe)."""
    if pid <= 0:
        return False
    if os.name == "nt":
        import ctypes

        handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
        if handle:
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _acquire_single_instance_lock() -> None:
    """Prevent two polling processes from fighting over getUpdates."""
    if _LOCK_FILE.exists():
        try:
            old_pid = int(_LOCK_FILE.read_text().strip())
        except ValueError:
            _LOCK_FILE.unlink(missing_ok=True)
        else:
            if _pid_is_running(old_pid):
                raise RuntimeError(
                    f"Telegram bot already running (PID {old_pid}). "
                    "Stop it before starting a new instance."
                )
            _LOCK_FILE.unlink(missing_ok=True)

    _LOCK_FILE.write_text(str(os.getpid()), encoding="utf-8")
    atexit.register(lambda: _LOCK_FILE.unlink(missing_ok=True))


async def _on_error(
    update: object, context: ContextTypes.DEFAULT_TYPE
) -> None:
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
        agent = COOAgent(self.db)
        return agent.handle_instruction(instruction, telegram_chat_id=chat_id)

    def _run_morning_briefing(self) -> str:
        agent = COOAgent(self.db)
        return agent.run_daily_briefing()

    def _morning_brief_chat_id(self) -> int | None:
        raw = self.settings.telegram_chat_id.strip()
        if not raw:
            return None
        try:
            return int(raw)
        except ValueError:
            logger.error("TELEGRAM_CHAT_ID invalid (expected integer): %r", raw)
            return None

    async def _send_morning_brief(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = self._morning_brief_chat_id()
        if chat_id is None:
            logger.warning("Morning brief skipped — TELEGRAM_CHAT_ID is not configured")
            return

        logger.info("Sending morning brief to chat %s", chat_id)
        try:
            briefing = await asyncio.to_thread(self._run_morning_briefing)
            log_bot_action(
                self.db, BOT_NAME, "morning_brief", "scheduled", briefing[:200]
            )
        except Exception:
            logger.exception("Morning brief generation failed")
            briefing = "Brief matinal indisponible — erreur lors de la génération."
            log_bot_action(
                self.db,
                BOT_NAME,
                "morning_brief",
                "scheduled",
                briefing,
                status="error",
            )

        for chunk in _split_message(briefing):
            await context.bot.send_message(chat_id=chat_id, text=chunk)

    async def _schedule_morning_brief(self, application: Application) -> None:
        if self.settings.telegram_secretary_bot_token.strip():
            logger.info(
                "Brief 8h COO désactivé — bot Nadia dédié (TELEGRAM_SECRETARY_BOT_TOKEN)"
            )
            return
        if application.job_queue is None:
            logger.warning("Job queue unavailable — morning brief not scheduled")
            return

        for job in application.job_queue.get_jobs_by_name(_MORNING_BRIEF_JOB):
            job.schedule_removal()

        if self._morning_brief_chat_id() is None:
            logger.warning(
                "TELEGRAM_CHAT_ID not set — morning brief disabled. "
                "Send /start to the bot and copy the chat ID from the console."
            )
            return

        application.job_queue.run_daily(
            self._send_morning_brief,
            time=dt.time(hour=8, minute=0, tzinfo=_MORNING_BRIEF_TZ),
            name=_MORNING_BRIEF_JOB,
        )
        logger.info("Morning brief scheduled daily at 08:00 %s", _MORNING_BRIEF_TZ)

    def _start_reply(self, chat_id: int) -> str:
        configured = self._morning_brief_chat_id()
        lines = [
            _START_MESSAGE,
            "",
            f"Ton chat ID : {chat_id}",
        ]

        if configured == chat_id:
            lines.append("")
            lines.append("Brief matinal activé — envoi automatique à 8h (Europe/Paris).")
        elif configured is not None:
            lines.append("")
            lines.append(
                "Le brief matinal pointe vers un autre chat. "
                f"Mets TELEGRAM_CHAT_ID={chat_id} dans .env, puis redémarre le bot."
            )
        else:
            lines.append("")
            lines.append("Pour activer le brief matinal à 8h, ajoute dans .env :")
            lines.append(f"TELEGRAM_CHAT_ID={chat_id}")
            lines.append("Puis redémarre le bot (Ctrl+C dans le terminal, relance).")
        return "\n".join(lines)

    async def _handle_start(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if not update.message or not update.effective_chat:
            return

        chat_id = update.effective_chat.id
        logger.info("Telegram chat ID: %s", chat_id)
        print(f"TELEGRAM_CHAT_ID={chat_id}")

        await update.message.reply_text(self._start_reply(chat_id))

    async def _handle_text(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if not update.message or not update.message.text:
            return

        text = update.message.text.strip()
        if not text:
            return

        if not _is_authorized(update):
            await _reject_unauthorized(update)
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

        chat_id = update.effective_chat.id if update.effective_chat else None

        from bots.telegram_delivery import reply_with_ack
        from services.telegram_ack import summarize_task_aria

        def _log(inp: str, out: str, status: str) -> None:
            log_bot_action(self.db, BOT_NAME, "message_received", inp, "")
            log_bot_action(self.db, BOT_NAME, "coo_response", inp, out, status=status)

        await reply_with_ack(
            update,
            agent_name="Aria",
            task_summary=summarize_task_aria(text),
            run=lambda: self._run_coo(text, chat_id),
            on_logged=_log,
            chat_id=chat_id,
            instruction=text,
        )

    def build_application(self) -> Application:
        if self._application is None:
            token = self._ensure_token()
            presence_init, presence_stop = presence_callbacks(
                token=token,
                chat_id=self._morning_brief_chat_id(),
                back_message=BACK_MESSAGE_ARIA,
                coffee_message=COFFEE_MESSAGE_ARIA,
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
            app.add_error_handler(_on_error)
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
        _acquire_single_instance_lock()
        logging.basicConfig(level=logging.INFO)
        app = self.build_application()
        logger.info("Telegram bot starting in polling mode")
        app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


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
