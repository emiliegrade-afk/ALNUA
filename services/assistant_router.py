"""Route natural-language messages to Aria (COO) or Nadia (secretary)."""

from __future__ import annotations

import logging
import re
from typing import Any, Literal

logger = logging.getLogger(__name__)

AssistantAgent = Literal["coo", "secretary", "auto"]

_EXPLICIT_COO = re.compile(
    r"^(?:@(?:aria|coo)\b|aria\s*[:,]|coo\s*[:,])\s*",
    re.I,
)
_EXPLICIT_SECRETARY = re.compile(
    r"^(?:@(?:nadia|secretary|secrétaire)\b|nadia\s*[:,]|secrétaire\s*[:,])\s*",
    re.I,
)

_SECRETARY_KEYWORDS = (
    "email",
    "mail",
    "courrier",
    "contrat",
    " nda",
    "réunion",
    "reunion",
    "agenda",
    "planning",
    "calendrier",
    "compte rendu",
    "secrétaire",
    "secretaire",
    "nadia",
    "rdv",
    "rendez-vous",
    "rendez vous",
    "invitation",
    "convocation",
    "contrat de",
    "rédige un mail",
    "redige un mail",
    "rapport de la nuit",
    "briefing du jour",
)

_COO_KEYWORDS = (
    "pipeline",
    "academy",
    "académie",
    "agent-ready",
    "délègue",
    "delegue",
    "projet ",
    "priorité",
    "priorite",
    "r&d",
    "rnd",
    "investiguer",
    "idée r&d",
    "lance le",
    "ticket",
    "wyrdheim",
    "coo",
    "aria",
    "ops",
    "orchestration",
)


def strip_explicit_prefix(message: str) -> tuple[AssistantAgent | None, str]:
    """Return forced agent if @aria / @nadia prefix, else None."""
    text = message.strip()
    m = _EXPLICIT_COO.match(text)
    if m:
        return "coo", text[m.end() :].strip()
    m = _EXPLICIT_SECRETARY.match(text)
    if m:
        return "secretary", text[m.end() :].strip()
    return None, text


def resolve_assistant_agent(message: str, preferred: AssistantAgent = "auto") -> str:
    """
    Pick coo or secretary.
    preferred='coo'|'secretary' forces; 'auto' uses prefix then keywords; default coo.
    """
    forced, cleaned = strip_explicit_prefix(message)
    if forced:
        return forced
    if preferred in ("coo", "secretary"):
        return preferred

    lower = cleaned.lower()
    sec_score = sum(1 for kw in _SECRETARY_KEYWORDS if kw in lower)
    coo_score = sum(1 for kw in _COO_KEYWORDS if kw in lower)

    if sec_score > coo_score and sec_score > 0:
        return "secretary"
    if coo_score > sec_score and coo_score > 0:
        return "coo"
    # Short admin-ish messages → Nadia; ops-ish default Aria
    if sec_score == coo_score and sec_score > 0:
        return "secretary"
    return "coo"


def assistant_chat(
    message: str,
    *,
    agent: AssistantAgent = "auto",
    project: str | None = None,
    telegram_chat_id: int | None = None,
    session_id: str | None = None,
    channel: str = "hub",
) -> dict[str, Any]:
    """
    Single entry for Hub UI + Telegram NL.
    Returns {agent_id, agent_name, response, issue_created?, ...}
    """
    forced, cleaned = strip_explicit_prefix(message)
    text = cleaned or message.strip()
    if not text:
        return {
            "agent_id": "coo",
            "agent_name": "Aria Voss",
            "response": "Message vide — dis-moi ce dont tu as besoin.",
            "issue_created": False,
        }

    target = resolve_assistant_agent(text, agent if not forced else forced)
    sid = session_id or (f"tg:{telegram_chat_id}" if telegram_chat_id else "hub")

    if target == "secretary":
        from agents.secretary_agent import SecretaryAgent

        response = SecretaryAgent().handle_instruction(text, session_id=sid)
        return {
            "agent_id": "secretary",
            "agent_name": "Nadia Faure",
            "response": response,
            "issue_created": False,
        }

    from agents.coo_agent import COOAgent

    result = COOAgent().process_message(text, project)
    return {
        "agent_id": "coo",
        "agent_name": "Aria Voss",
        "response": result.get("response", ""),
        "issue_created": bool(result.get("issue_created")),
        "issue_number": result.get("issue_number"),
        "issue_url": result.get("issue_url"),
        "repo": result.get("repo"),
    }


async def assistant_chat_async(
    message: str,
    *,
    agent: AssistantAgent = "auto",
    project: str | None = None,
    telegram_chat_id: int | None = None,
    session_id: str | None = None,
    channel: str = "hub",
) -> dict[str, Any]:
    """Async entry — runs agent handlers in thread pool to avoid blocking the event loop."""
    import asyncio

    return await asyncio.to_thread(
        assistant_chat,
        message,
        agent=agent,
        project=project,
        telegram_chat_id=telegram_chat_id,
        session_id=session_id,
        channel=channel,
    )
