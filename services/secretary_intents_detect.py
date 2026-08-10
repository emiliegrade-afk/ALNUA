"""Intent detection and extraction for secretary natural-language routing."""

from __future__ import annotations

import re

from services.secretary_intents_constants import (
    ACADEMY_MARKERS,
    ARIA_DELEGATION_MARKERS,
    BRIEFING_MARKERS,
    CALENDAR_MARKERS,
    CONNECT_MARKERS,
    CONTRACT_MARKERS,
    EMAIL_MARKERS,
    INBOX_MARKERS,
    MEETING_MARKERS,
    NIGHT_REPORT_MARKERS,
    RESEARCH_MARKERS,
    SEND_CONFIRM_MARKERS,
    WAKE_OPS_MARKERS,
)


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def detect_night_report(text: str) -> bool:
    n = _norm(text)
    return any(m in n for m in NIGHT_REPORT_MARKERS)


def detect_briefing(text: str) -> bool:
    n = _norm(text)
    return any(m in n for m in BRIEFING_MARKERS)


def detect_email_intent(text: str) -> bool:
    return any(m in _norm(text) for m in EMAIL_MARKERS)


def detect_contract_intent(text: str) -> bool:
    return any(m in _norm(text) for m in CONTRACT_MARKERS)


def detect_meeting_intent(text: str) -> bool:
    return any(m in _norm(text) for m in MEETING_MARKERS)


def detect_connect_intent(text: str) -> bool:
    return any(m in _norm(text) for m in CONNECT_MARKERS)


def detect_inbox_intent(text: str) -> bool:
    return any(m in _norm(text) for m in INBOX_MARKERS)


def detect_send_confirm(text: str) -> bool:
    return any(m in _norm(text) for m in SEND_CONFIRM_MARKERS)


def detect_calendar_intent(text: str) -> bool:
    n = _norm(text)
    return any(m in n for m in CALENDAR_MARKERS)


def detect_academy_intent(text: str) -> bool:
    return any(m in _norm(text) for m in ACADEMY_MARKERS)


def detect_wake_ops(text: str) -> bool:
    return any(m in _norm(text) for m in WAKE_OPS_MARKERS)


def detect_aria_delegation(text: str) -> bool:
    return any(m in _norm(text) for m in ARIA_DELEGATION_MARKERS)


def detect_research_intent(text: str) -> bool:
    n = _norm(text)
    if "rapport biblioth" in n:
        return True
    return any(m in n for m in RESEARCH_MARKERS)


def extract_research_query(text: str) -> str:
    """Pull research topic from natural language."""
    raw = text.strip()
    patterns = (
        r"recherche(?:r)?\s+(?:sur\s+)?(.+)$",
        r"cherche\s+(?:sur\s+)?(.+)$",
        r"investigue(?:r)?\s+(?:sur\s+)?(.+)$",
        r"tendances\s+(.+)$",
        r"nouveautés?\s+(.+)$",
        r"nouveautes?\s+(.+)$",
    )
    for pattern in patterns:
        match = re.search(pattern, raw, flags=re.I)
        if match:
            topic = match.group(1).strip(" :.-")
            if len(topic) >= 3:
                return topic
    if "rapport biblioth" in _norm(raw):
        return "__report__"
    return raw[:400]


def extract_aria_delegation_message(text: str) -> str:
    """Strip relay phrasing so COO gets the actionable instruction."""
    n = text.strip()
    patterns = (
        r"^(?:demande|dis|passe|transmets|fais dire)\s+(?:à|a)\s+aria\s+(?:de\s+)?",
        r"^aria\s+(?:doit|peut)\s+",
        r"^(?:parle|via)\s+(?:à|a)\s+aria\s+(?:pour\s+)?",
    )
    for pattern in patterns:
        n = re.sub(pattern, "", n, flags=re.I).strip()
    return n or text.strip()
