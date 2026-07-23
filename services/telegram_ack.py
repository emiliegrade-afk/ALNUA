"""Human-readable Telegram ack labels — recherche, pas veille."""

from __future__ import annotations

import re


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def summarize_task_nadia(instruction: str) -> str:
    from services.secretary_intents import (
        detect_academy_intent,
        detect_aria_delegation,
        detect_briefing,
        detect_calendar_intent,
        detect_connect_intent,
        detect_contract_intent,
        detect_email_intent,
        detect_inbox_intent,
        detect_meeting_intent,
        detect_night_report,
        detect_research_intent,
        detect_send_confirm,
        detect_wake_ops,
        extract_research_query,
    )

    if detect_send_confirm(instruction):
        return "envoi du mail"
    if detect_research_intent(instruction):
        q = extract_research_query(instruction)
        if q == "__report__":
            return "rapport bibliothèque"
        return f"recherche — {q[:60]}" if q else "recherche bibliothèque"
    if detect_wake_ops(instruction):
        return "relance pipeline Academy"
    if detect_aria_delegation(instruction):
        return "transmission à Aria"
    if detect_academy_intent(instruction):
        return "statut Academy"
    if detect_night_report(instruction):
        return "rapport de la nuit"
    if detect_briefing(instruction):
        return "briefing du jour"
    if detect_connect_intent(instruction):
        return "connexion app (Gmail/Calendar)"
    if detect_inbox_intent(instruction):
        return "tri de tes mails"
    if detect_calendar_intent(instruction):
        return "ton agenda"
    if detect_email_intent(instruction):
        return "rédaction d'un email"
    if detect_contract_intent(instruction):
        return "rédaction d'un contrat"
    if detect_meeting_intent(instruction):
        return "réunion / compte rendu"
    short = instruction.strip()[:50]
    return short + ("…" if len(instruction.strip()) > 50 else "")


def summarize_task_aria(instruction: str) -> str:
    from agents.coo_agent import (
        RND_KEYWORDS,
        _detect_research_intent,
        _extract_research_topic,
        detect_coding_intent,
    )

    msg = _norm(instruction)
    is_research, _agent = _detect_research_intent(instruction)
    if is_research:
        topic = _extract_research_topic(instruction, None)
        return f"recherche — {topic[:60]}" if topic else "recherche bibliothèque"
    if detect_coding_intent(instruction):
        return "tâche de codage / pipeline"
    if any(k in msg for k in ("relance", "relancer", "réveille", "wake", "pipeline academy")):
        return "relance agents / pipeline"
    if any(k in msg for k in RND_KEYWORDS):
        return "cycle ou rapport R&D"
    if "academy" in msg or "académie" in msg:
        return "statut Academy"
    short = instruction.strip()[:50]
    return short + ("…" if len(instruction.strip()) > 50 else "")


def format_received_ack(agent_name: str, task: str) -> str:
    safe_task = task.replace("_", " ").strip() or "ta demande"
    return f"✅ Reçu — {agent_name} :\n{safe_task}"


def format_done_reply(body: str, *, ok: bool = True) -> str:
    text = body.strip()
    if text.startswith("✅") or text.startswith("❌"):
        return text
    header = "✅ **C'est fait**" if ok else "❌ **Échec**"
    return f"{header}\n\n{text}"
