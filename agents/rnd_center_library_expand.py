"""R&D Center — library concept expansion via LLM."""

from __future__ import annotations

import json
import logging
import re

from agents.rnd_center_llm import _llm
from config.agent_operating_spec import get_system_prompt

logger = logging.getLogger("rnd_center")


def expand_library_concept(
    title: str,
    summary: str,
    *,
    topics: list[str] | None = None,
    source_url: str = "",
    query: str = "",
    bureau: str = "rd",
    vision: str = "",
) -> dict:
    """Enrichit une fiche bibliothèque en concept R&D structuré (comme le cycle autonome)."""
    topics_text = ", ".join(topics or []) or "non précisé"
    system = get_system_prompt("rnd_library_expand")

    user = f"""VISION ALNUA :
{vision[:800] or "CEO solopreneure — portfolio apps, gaming, robotique, agents IA autonomes."}

FICHE BIBLIOTHÈQUE :
- Bureau : {bureau}
- Titre : {title}
- Résumé : {summary[:2500]}
- Sujets : {topics_text}
- Recherche d'origine : {query[:300]}
- Source : {source_url[:500]}

Développe ce concept en proposition R&D actionnable (pas une simple reprise du résumé)."""

    base = {
        "title": title[:200],
        "domain": "autre",
        "description": summary[:4000] or title,
        "why_now": "",
        "effort": "M",
    }
    try:
        raw = _llm(system, user, max_tokens=2000)
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            parsed = json.loads(match.group())
            if isinstance(parsed, dict):
                base.update(
                    {
                        "title": str(parsed.get("title") or title)[:200],
                        "domain": str(parsed.get("domain") or "autre"),
                        "description": str(parsed.get("description") or summary)[:4000],
                        "why_now": str(parsed.get("why_now") or "")[:2000],
                        "effort": str(parsed.get("effort") or "M")[:4],
                    }
                )
                insights = str(parsed.get("library_insights") or "").strip()
                if insights:
                    base["description"] = f"{base['description']}\n\n**Apport bibliothèque :** {insights}"
    except Exception as exc:
        logger.warning("rnd_center: expand_library_concept failed: %s", exc)

    return base
