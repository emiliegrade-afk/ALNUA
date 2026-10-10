"""Internet research that returns sources on screen in seconds, not minutes."""

from __future__ import annotations

import json
from typing import Any

from services.input_sanitizer import sanitize_user_input
from services.live_web_search import search_fast


def web_brief(query: str) -> str:
    """Search the public web and format a Live card. Empty means empty — no invented hits."""
    topic = sanitize_user_input(query, max_length=400, redact_pii_enabled=False).strip()
    if not topic:
        return "Dis-moi ce que je dois chercher sur internet."

    hits = _search(topic)
    if not hits:
        return (
            f"Recherche internet — « {topic} »\n\n"
            "Aucune source n'est revenue en moins de 10 s "
            "(moteur bloqué ou hors ligne). Je n'invente pas de résultats."
        )

    bullets = _bullets(hits)
    headline = f"Recherche : {topic}"
    payload = {"headline": headline, "bullets": bullets}
    lines = [
        headline,
        "",
        f"```summary\n{json.dumps(payload, ensure_ascii=False)}\n```",
        "",
        "Sources :",
    ]
    for hit in hits[:6]:
        title = str(hit.get("title") or "Source")[:120]
        url = str(hit.get("url") or "")[:300]
        snippet = str(hit.get("content") or "")[:220]
        lines.append(f"• {title}")
        if snippet:
            lines.append(f"  {snippet}")
        if url:
            lines.append(f"  {url}")
    return "\n".join(lines)


def _search(topic: str) -> list[dict[str, Any]]:
    return search_fast(topic, max_results=6)


def _bullets(hits: list[dict[str, Any]]) -> list[str]:
    fallback: list[str] = []
    for hit in hits[:6]:
        title = str(hit.get("title") or "").strip()
        snippet = str(hit.get("content") or "").strip()
        if title:
            fallback.append(f"{title} — {snippet}"[:180] if snippet else title)
    return fallback[:8]
