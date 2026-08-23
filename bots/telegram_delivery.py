"""Two-step Telegram replies: instant ack, then result — always answers."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable

from telegram import Update

from bots.telegram_common import split_message
from services.telegram_ack import format_done_reply, format_received_ack
from services.telegram_chat_memory import append_turn
from services.telegram_presence import hub_down_prefix, hub_online

logger = logging.getLogger(__name__)

_HANDLER_TIMEOUT_S = 90.0


async def reply_with_ack(
    update: Update,
    *,
    agent_name: str,
    task_summary: str,
    run: Callable[[], str],
    on_logged: Callable[[str, str, str], None] | None = None,
    chat_id: int | None = None,
    instruction: str = "",
    voice_agent_id: str | None = None,
) -> None:
    """
    1. Confirm message received immediately (plain text — no silent fail).
    2. Run handler in a thread with timeout.
    3. Always send a final reply (success, limitation, or error).
    """
    if not update.message:
        return

    instruction_preview = (instruction or task_summary)[:200]
    ack = format_received_ack(agent_name, task_summary)

    try:
        await update.message.reply_text(ack)
    except Exception:
        await update.message.reply_text(
            f"Reçu — {agent_name} s'en occupe : {task_summary[:120]}"
        )

    try:
        await update.message.chat.send_action("typing")
    except Exception:
        pass

    status = "ok"
    facts_for_voice = ""
    try:
        response = await asyncio.wait_for(
            asyncio.to_thread(run),
            timeout=_HANDLER_TIMEOUT_S,
        )
        body = (response or "").strip()
        if not body:
            body = (
                "Je n'ai pas de réponse précise pour ça. "
                "Reformule ou dis-moi une action concrète — je te dirai si je peux la faire."
            )
        prefix = hub_down_prefix()
        if prefix and not hub_online(force_refresh=True):
            body = prefix + body
        ok = not body.lstrip().startswith("❌")
        facts_for_voice = body if ok else ""
        response = format_done_reply(body, ok=ok)
    except asyncio.TimeoutError:
        logger.warning("%s Telegram handler timeout", agent_name)
        status = "error"
        response = format_done_reply(
            "⏱️ Ça a pris trop de temps (Hub lent ou arrêté).\n"
            "Relance `Demarrer-Hub.bat` puis réessaie — ou formule une demande plus simple.",
            ok=False,
        )
    except Exception as exc:
        logger.exception("%s Telegram handler error", agent_name)
        status = "error"
        if not hub_online(force_refresh=True):
            response = format_done_reply(
                "☕ Le Hub semble arrêté — je ne peux pas traiter cette demande.\n"
                "Lance `Demarrer-Hub.bat` puis renvoie ton message.",
                ok=False,
            )
        else:
            response = format_done_reply(
                f"Une erreur est survenue ({type(exc).__name__}). Réessaie dans un instant.",
                ok=False,
            )

    if on_logged:
        try:
            on_logged(instruction_preview, response[:200], status)
        except Exception:
            logger.warning("telegram delivery log callback failed", exc_info=True)

    plain_response = response
    for chunk in split_message(plain_response):
        try:
            await update.message.reply_text(chunk, parse_mode="Markdown")
        except Exception:
            await update.message.reply_text(chunk)

    if chat_id is not None and instruction:
        append_turn(chat_id, "user", instruction)
        append_turn(chat_id, "assistant", plain_response[:800])

    if voice_agent_id and status == "ok" and facts_for_voice:
        try:
            from services.telegram_voice import maybe_send_voice_reply

            await maybe_send_voice_reply(
                update, facts_for_voice, agent_id=voice_agent_id
            )
        except Exception:
            logger.warning("telegram voice overlay skipped", exc_info=True)
