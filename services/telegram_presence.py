"""Telegram presence — Hub online/offline, café messages, capability hints."""

from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)

BACK_MESSAGE_ARIA = (
    "💼 **Aria est de retour.**\n"
    "Tu peux me parler en langage naturel — Academy, R&D, pipeline, idées…\n"
    "_Si je ne réponds pas, le Hub est peut-être arrêté : lance `Demarrer-Hub.bat`._"
)

BACK_MESSAGE_NADIA = (
    "💼 **Nadia est de retour.**\n"
    "Mails, planning, contrats, recherche, Academy — dis-moi ce dont tu as besoin.\n"
    "_Si je ne réponds pas, le Hub est peut-être arrêté : lance `Demarrer-Hub.bat`._"
)

COFFEE_MESSAGE_ARIA = (
    "☕ **Aria part boire un café.**\n"
    "Le Hub ou les bots sont arrêtés — relance `Demarrer-Hub.bat` quand tu veux me retrouver."
)

COFFEE_MESSAGE_NADIA = (
    "☕ **Nadia part boire un café.**\n"
    "Le Hub ou les bots sont arrêtés — relance `Demarrer-Hub.bat` quand tu veux me retrouver."
)

HUB_DOWN_NOTE = (
    "☕ _Le Hub API est en pause (je réponds en mode chat limité : "
    "pas de relance pipeline, ni actions lourdes tant que le serveur n'est pas relancé)._"
)

CANNOT_DO_ARIA = (
    "Je ne peux pas faire ça tout de suite. En revanche je peux :\n"
    "• te donner l'état Academy / relancer Théo (`relance les agents`)\n"
    "• lancer une recherche ou une investigation R&D\n"
    "• enregistrer une idée R&D · lancer un cycle R&D\n"
    "• répondre à tes questions ops en langage naturel\n\n"
    "Pour mails, contrats et agenda → **Nadia**."
)

CANNOT_DO_NADIA = (
    "Je ne peux pas faire ça tout de suite. En revanche je peux :\n"
    "• rédiger ou trier tes mails (puis « envoie le mail »)\n"
    "• ton planning / réunions / contrats\n"
    "• recherche web → bibliothèque\n"
    "• rapport de nuit Academy · briefing du jour\n"
    "• transmettre à **Aria** (`demande à Aria de…`)\n\n"
    "Pour pipeline, R&D et ops lourdes → **Aria**."
)


def hub_online(*, force_refresh: bool = False) -> bool:
    try:
        from services.hub_resolve import resolve_hub_api_url

        base = resolve_hub_api_url(force_refresh=force_refresh)
        with httpx.Client(timeout=3.0) as client:
            resp = client.get(f"{base}/orchestration/pipeline-status")
            return resp.status_code == 200
    except Exception:
        return False


def hub_status_line() -> str:
    if hub_online():
        return "🟢 Hub API en ligne"
    return "🔴 Hub API hors ligne — relance `Demarrer-Hub.bat`"


def hub_down_prefix() -> str:
    if hub_online():
        return ""
    return HUB_DOWN_NOTE + "\n\n"


def send_telegram_text(token: str, chat_id: int, text: str) -> bool:
    if not token.strip() or not chat_id:
        return False
    url = f"https://api.telegram.org/bot{token.strip()}/sendMessage"
    try:
        with httpx.Client(timeout=15.0) as client:
            for chunk in _split_chunks(text):
                resp = client.post(
                    url,
                    json={"chat_id": chat_id, "text": chunk, "parse_mode": "Markdown"},
                )
                if resp.status_code != 200:
                    client.post(url, json={"chat_id": chat_id, "text": chunk})
        return True
    except Exception as exc:
        logger.warning("telegram presence send failed: %s", exc)
        return False


def _split_chunks(text: str, size: int = 4000) -> list[str]:
    if len(text) <= size:
        return [text]
    return [text[i : i + size] for i in range(0, len(text), size)]


async def notify_presence(
    *,
    token: str,
    chat_id: int | None,
    message: str,
) -> None:
    if chat_id is None:
        return
    import asyncio

    await asyncio.to_thread(send_telegram_text, token, chat_id, message)
