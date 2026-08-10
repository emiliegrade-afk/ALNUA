"""Telegram dev workflow commands — pipeline, ideas, PRs."""

from __future__ import annotations

import asyncio
import json
import logging
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from agents.dev_app_agent import DevAppAgent
from bots.base import log_bot_action
from bots.telegram_auth import is_authorized, reject_unauthorized
from database.supabase_client import get_supabase
from skills.skill_gh_issues import get_open_prs, list_ready_issues

logger = logging.getLogger(__name__)

BOT_NAME = "telegram_bot"


def telegram_notify(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
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
    if not is_authorized(update):
        await reject_unauthorized(update)
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
        agent = DevAppAgent(telegram_notify_fn=telegram_notify(context, chat_id))
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
    if not is_authorized(update):
        await reject_unauthorized(update)
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
    if not is_authorized(update):
        await reject_unauthorized(update)
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
