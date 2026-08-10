"""Telegram inline-keyboard callback handlers for the COO bot."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from agents.dev_app_agent import DevAppAgent
from bots.telegram_auth import UNAUTHORIZED_REPLY, is_authorized
from bots.telegram_commands import AGENTS_STATUS_TEXT, telegram_notify
from services.facades.costs_facade import get_telegram_costs_report

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parent.parent


def hub_repo_path() -> str:
    return os.getenv("HUB_REPO_PATH", str(_REPO_ROOT))


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gère tous les clics sur les boutons inline."""
    query = update.callback_query
    if not query:
        return

    await query.answer()

    if not is_authorized(update):
        logger.warning(
            "Unauthorized Telegram button callback from chat %s",
            update.effective_chat.id if update.effective_chat else "?",
        )
        await query.edit_message_text(UNAUTHORIZED_REPLY)
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
            agent = DevAppAgent(telegram_notify_fn=telegram_notify(context, chat_id))
            context.application.create_task(
                asyncio.to_thread(
                    agent.process_issue_by_number, issue_num, repo_slug
                )
            )

    elif action == "run_tests":
        branch = data.get("branch")
        pr_num = data.get("pr")
        repo_path = data.get("repo_path") or hub_repo_path()
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
                    telegram_notify(context, chat_id),
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
            AGENTS_STATUS_TEXT,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
