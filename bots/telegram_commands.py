"""Telegram slash-command handlers for the COO bot."""

from __future__ import annotations

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from bots.telegram_auth import is_authorized, reject_unauthorized
from bots.telegram_commands_dev import (
    BOT_NAME,
    idee_command,
    pipeline_command,
    prs_command,
    telegram_notify,
)
from services.facades.costs_facade import get_telegram_costs_report
from services.telegram_presence import hub_status_line

logger = logging.getLogger(__name__)

AGENTS_STATUS_TEXT = """🏢 *ALNUA — État des agents*

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


async def costs_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/costs — rapport coûts LLM avec boutons jour/mois."""
    if not update.message:
        return
    if not is_authorized(update):
        await reject_unauthorized(update)
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


async def cmd_connect(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/connect <APP> — génère le lien OAuth Composio pour connecter une app."""
    if not update.message:
        return
    if not is_authorized(update):
        await reject_unauthorized(update)
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
    if not is_authorized(update):
        await reject_unauthorized(update)
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
    if not is_authorized(update):
        await reject_unauthorized(update)
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
    if not is_authorized(update):
        await reject_unauthorized(update)
        return
    await message.reply_text(
        AGENTS_STATUS_TEXT,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


__all__ = [
    "AGENTS_STATUS_TEXT",
    "BOT_NAME",
    "agents_command",
    "cmd_apps",
    "cmd_connect",
    "cmd_status",
    "costs_command",
    "idee_command",
    "pipeline_command",
    "prs_command",
    "telegram_notify",
]
