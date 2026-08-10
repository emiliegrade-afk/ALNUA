"""Telegram secretary bot — standalone command handlers."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.error import Conflict
from telegram.ext import ContextTypes

from bots.telegram_secretary_auth import is_authorized, reject_unauthorized
from services.telegram_presence import hub_status_line

logger = logging.getLogger(__name__)


async def cmd_connect(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    if not is_authorized(update):
        await reject_unauthorized(update)
        return
    if not context.args:
        await update.message.reply_text(
            "Usage : /connect gmail\nou : /connect calendar"
        )
        return
    app = context.args[0].upper()
    if app in ("CALENDAR", "AGENDA", "GOOGLECALENDAR"):
        app = "GOOGLECALENDAR"
    elif app == "GMAIL":
        app = "GMAIL"
    else:
        app = app.upper()

    from services.secretary_composio import get_oauth_link_for_ceo

    link = get_oauth_link_for_ceo(app)
    if link.startswith("Erreur"):
        await update.message.reply_text(f"❌ {link}")
        return
    if "déjà connecté" in link or "deja connecte" in link.lower():
        await update.message.reply_text(f"✅ {link}")
        return
    await update.message.reply_text(link)


async def cmd_apps(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    if not is_authorized(update):
        await reject_unauthorized(update)
        return
    from services.secretary_composio import connection_status_text

    await update.message.reply_text(connection_status_text())


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    if not is_authorized(update):
        await reject_unauthorized(update)
        return
    await update.message.reply_text(
        f"**Nadia** — secrétaire ALNUA\n{hub_status_line()}\n\n"
        "Si le Hub est hors ligne, je peux encore discuter — "
        "mais pas relancer le pipeline ni actions lourdes.",
        parse_mode="Markdown",
    )


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    if isinstance(context.error, Conflict):
        logger.warning("409 Conflict — autre instance du bot Nadia en polling.")
        return
    logger.error("Telegram secretary handler error", exc_info=context.error)
    if isinstance(update, Update) and update.message:
        try:
            await update.message.reply_text(
                "❌ Souci technique côté Nadia — réessaie dans un instant. "
                "Si ça persiste : `Demarrer-Hub.bat` puis /status"
            )
        except Exception:
            pass
