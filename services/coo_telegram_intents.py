"""Natural-language intents for COO / Telegram — idea inbox + R&D investigations."""

from __future__ import annotations

import logging
import threading
from typing import Any

from services.coo_telegram_patterns import (
    clean_extracted,
    detect_idea_capture,
    detect_rnd_investigation,
    extract_idea_text,
    extract_investigation_query,
)

logger = logging.getLogger(__name__)

__all__ = [
    "capture_idea",
    "detect_idea_capture",
    "detect_rnd_investigation",
    "extract_idea_text",
    "extract_investigation_query",
    "launch_rnd_investigation",
    "_format_investigation_report",
]


def capture_idea(instruction: str, source: str = "Emilie via COO") -> dict[str, Any]:
    """Save an idea to the R&D inbox and return the created record."""
    from agents.rnd_center import inject_idea

    body = extract_idea_text(instruction) or instruction.strip()
    if not body:
        raise ValueError("Idée vide")
    return inject_idea(body, source=source)


def _format_investigation_report(query: str, report: dict[str, Any]) -> str:
    summary = (report.get("executive_summary") or "").strip()
    actions = report.get("recommended_actions") or []
    findings = report.get("key_findings") or []
    confidence = report.get("rounds_history", [{}])
    conf = confidence[0].get("confidence", "medium") if confidence else "medium"

    lines = [
        f"📋 Brief R&D — {query[:80]}",
        f"Confiance globale : {conf}",
        "",
    ]
    if summary:
        lines.append(summary)
    else:
        lines.append("Synthèse indisponible.")

    if findings:
        lines.append("")
        lines.append("Points clés :")
        for item in findings[:5]:
            if isinstance(item, dict):
                finding = item.get("finding", "")
                src = item.get("source", "")
                lines.append(f"• {finding}" + (f" ({src})" if src else ""))
            else:
                lines.append(f"• {item}")

    if actions:
        lines.append("")
        lines.append("Actions recommandées :")
        for action in actions[:3]:
            lines.append(f"→ {action}")

    return "\n".join(lines)[:3900]


def _notify(chat_id: int | None, message: str) -> bool:
    from skills.skill_telegram_notify import notify_telegram

    return notify_telegram(message, chat_id=chat_id)


def _run_investigation_worker(query: str, chat_id: int | None = None) -> None:
    """Background job: web search + quick research + Telegram notify."""
    logger.info("coo_telegram_intents: investigation start — %s", query[:80])
    try:
        from services.deep_research import quick_research
        from skills.skill_web_research import _search

        web_hits = _search(query, max_results=5)
        context_parts = [
            f"- {hit.get('title', '')}: {(hit.get('content') or '')[:250]}"
            for hit in web_hits
            if hit.get("title") or hit.get("content")
        ]
        context = "Résultats web récents:\n" + "\n".join(context_parts) if context_parts else ""

        report = quick_research(
            query=query,
            context=context,
            agent_id="rnd_agent",
        )
        message = _format_investigation_report(query, report)
        try:
            from database.supabase_client import get_supabase

            get_supabase().insert(
                "agent_logs",
                {
                    "agent_name": "rnd_agent",
                    "action": "rnd_investigation",
                    "input_summary": query[:200],
                    "output_summary": message[:2000],
                    "status": "success",
                },
            )
        except Exception:
            logger.debug("rnd_investigation: success log skipped", exc_info=True)
        if not _notify(chat_id, message):
            logger.warning("coo_telegram_intents: investigation done but Telegram notify failed")
    except Exception as exc:
        logger.exception("coo_telegram_intents: investigation failed for %r", query)
        _notify(chat_id, f"❌ Investigation R&D échouée pour « {query[:60]} » : {exc}")


def launch_rnd_investigation(query: str, chat_id: int | None = None) -> str:
    """
    Start async R&D investigation via hypothesis tree (Arbor-lite).
    Returns immediate acknowledgment for Telegram.
    """
    topic = clean_extracted(query)
    if len(topic) < 4:
        return (
            "❌ Sujet trop vague — précise ce que le R&D doit investiguer "
            "(ex: « VPN russe trending »)."
        )

    try:
        from services.rnd_hypothesis_tree import start_investigation

        result = start_investigation(topic, requested_by="telegram", chat_id=chat_id)
        ack = (
            f"🌳 **Arbre R&D lancé** (Arbor-lite)\n"
            f"Sujet : {topic[:120]}\n"
            f"Alex explore la racine + 3 branches — bilans au fil de l'eau (~3-8 min).\n"
            f"{result.get('message', '')}"
        )
        log_summary = result.get("message", "Arbre en cours…")
    except Exception as exc:
        logger.warning("hypothesis tree failed, fallback single investigation: %s", exc)
        ack = (
            f"✅ Investigation R&D lancée\n"
            f"Sujet : {topic[:120]}\n"
            f"Alex (R&D) prépare le brief — réponse dans ~1-3 min."
        )
        log_summary = "Investigation en cours…"
        threading.Thread(
            target=_run_investigation_worker,
            args=(topic, chat_id),
            daemon=False,
            name=f"rnd-investigation-{topic[:24]}",
        ).start()
        return ack

    try:
        from database.supabase_client import get_supabase

        get_supabase().insert(
            "agent_logs",
            {
                "agent_name": "rnd_agent",
                "action": "rnd_hypothesis_tree",
                "input_summary": topic[:200],
                "output_summary": log_summary[:200],
                "status": "pending",
            },
        )
    except Exception:
        logger.debug("rnd_investigation: pending log skipped", exc_info=True)

    return ack
