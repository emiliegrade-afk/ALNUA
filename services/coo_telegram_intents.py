"""Natural-language intents for COO / Telegram — idea inbox + R&D investigations."""

from __future__ import annotations

import logging
import re
import threading
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Idea capture
# ---------------------------------------------------------------------------

IDEA_CAPTURE_PREFIXES = (
    "note cette idée",
    "note l'idée",
    "note l idee",
    "note cette idee",
    "boîte à idées",
    "boite a idees",
    "boîte a idees",
    "garde cette idée",
    "garde cette idee",
    "idée en vrac",
    "idee en vrac",
    "idée:",
    "idee:",
    "#idee",
    "#idée",
)

IDEA_CAPTURE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^j['']?ai une idée(?: pour)?\s*[:.]?\s*(.+)$", re.I | re.S),
    re.compile(r"^nouvelle idée\s*[:.]?\s*(.+)$", re.I | re.S),
    re.compile(r"^explore l['']idée (?:de |d[''])?(.+)$", re.I | re.S),
    re.compile(r"^idée r&d\s*[:.]?\s*(.+)$", re.I | re.S),
)

INVESTIGATION_MARKERS = (
    "investiguer",
    "investigue",
    "investigation",
    "demande au r&d",
    "demande au rnd",
    "demande à r&d",
    "demande a r&d",
    "le r&d doit",
    "le rnd doit",
    "alex doit",
    "rnd doit",
    "r&d doit",
    "analyse le marché",
    "analyse la tendance",
    "analyse les tendances",
    "faisabilité",
    "faisabilite",
    "retour sur investissement",
    "roi ",
    " rentabilité",
    "rentabilite",
)

INVESTIGATION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"(?:demande(?:r)?\s+(?:au\s+)?r&?d\s+(?:d['']?)?(?:investiguer|analyser|regarder|étudier|etudier)\s+(?:sur\s+)?)(.+)$",
        re.I | re.S,
    ),
    re.compile(
        r"(?:r&?d\s+(?:doit|peut)\s+(?:investiguer|analyser|regarder)\s+(?:sur\s+)?)(.+)$",
        re.I | re.S,
    ),
    re.compile(
        r"(?:investiguer|investigue|analyser|analyse|étudier|etudier)\s+(?:sur\s+)?(?:le\s+|la\s+|les\s+|l[''])?(.+)$",
        re.I | re.S,
    ),
    re.compile(r"(?:tendance|trending)\s*[:.]?\s*(.+)$", re.I | re.S),
    re.compile(
        r"(?:quel(?:le)?s?\s+)?(?:est\s+)?(?:la\s+)?faisabilit[eé]\s+(?:du |de la |de l['']|des )?(.+?)(?:\?|$)",
        re.I | re.S,
    ),
    re.compile(
        r"(?:retour sur investissement|roi)\s+(?:du |de la |de l['']|pour )?(.+?)(?:\?|$)",
        re.I | re.S,
    ),
)


def _clean_extracted(text: str) -> str:
    cleaned = text.strip().strip("«»\"'.,;:!?")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned


def extract_idea_text(instruction: str) -> str | None:
    """Extract idea body from a natural-language capture message."""
    raw = instruction.strip()
    if not raw:
        return None

    lower = raw.lower()
    for prefix in IDEA_CAPTURE_PREFIXES:
        if lower.startswith(prefix):
            body = raw[len(prefix) :].strip(" :.-")
            return _clean_extracted(body) if body else None

    for pattern in IDEA_CAPTURE_PATTERNS:
        match = pattern.match(raw)
        if match:
            body = _clean_extracted(match.group(1))
            if body:
                return body

    return None


def detect_idea_capture(instruction: str) -> bool:
    """True when the message should be saved to the R&D idea inbox."""
    if extract_idea_text(instruction):
        return True
    lower = instruction.lower().strip()
    return any(lower.startswith(p) for p in IDEA_CAPTURE_PREFIXES)


def extract_investigation_query(instruction: str) -> str | None:
    """Extract research topic from an R&D investigation request."""
    raw = instruction.strip()
    if not raw:
        return None

    lower = raw.lower()
    if not any(marker in lower for marker in INVESTIGATION_MARKERS):
        # Also accept explicit R&D delegation phrasing
        if not re.search(r"\b(r&?d|rnd)\b", lower, re.I):
            return None
        if not re.search(r"\b(investig|analys|trend|tendance|marché|marche|étud|etud)\b", lower, re.I):
            return None

    for pattern in INVESTIGATION_PATTERNS:
        match = pattern.search(raw)
        if match:
            topic = _clean_extracted(match.group(1))
            if len(topic) >= 4:
                return topic

    # Fallback: strip leading delegation boilerplate
    fallback = re.sub(
        r"^(?:demande(?:r)?\s+(?:au\s+)?r&?d\s+(?:d['']?)?(?:investiguer|analyser)\s+(?:sur\s+)?)",
        "",
        raw,
        flags=re.I,
    ).strip()
    fallback = _clean_extracted(fallback)
    if len(fallback) >= 4 and fallback.lower() != lower:
        return fallback

    return None


def detect_rnd_investigation(instruction: str) -> bool:
    return extract_investigation_query(instruction) is not None


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
    Start async R&D investigation. Returns immediate COO acknowledgment for Telegram.
    """
    topic = _clean_extracted(query)
    if len(topic) < 4:
        return (
            "❌ Sujet trop vague — précise ce que le R&D doit investiguer "
            "(ex: « VPN russe trending »)."
        )

    ack = (
        f"✅ Investigation R&D lancée\n"
        f"Sujet : {topic[:120]}\n"
        f"Alex (R&D) prépare le brief — réponse dans ~1-3 min."
    )

    try:
        from database.supabase_client import get_supabase

        get_supabase().insert(
            "agent_logs",
            {
                "agent_name": "rnd_agent",
                "action": "rnd_investigation",
                "input_summary": topic[:200],
                "output_summary": "Investigation en cours…",
                "status": "pending",
            },
        )
    except Exception:
        logger.debug("rnd_investigation: pending log skipped", exc_info=True)

    # Non-daemon: survive until notify completes (uvicorn reload may still kill it).
    threading.Thread(
        target=_run_investigation_worker,
        args=(topic, chat_id),
        daemon=False,
        name=f"rnd-investigation-{topic[:24]}",
    ).start()

    return ack
