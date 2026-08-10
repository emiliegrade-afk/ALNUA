"""LLM extraction of library entries from web research hits."""
from __future__ import annotations

import logging
from typing import Any

from services.bureau_library_constants import BUREAU_LABELS
from services.bureau_library_entries import add_entry, default_agent_for_bureau

logger = logging.getLogger(__name__)


def _extract_entries_from_research(
    query: str,
    raw_results: list[dict[str, Any]],
    requested_by: str,
) -> list[dict[str, Any]]:
    """LLM turns search hits into library entries — keep everything, tag now/later."""
    if not raw_results:
        return []

    from agents.base import parse_json_response

    results_text = "\n\n".join(
        f"Titre: {r.get('title', '')}\nURL: {r.get('url', '')}\n"
        f"Contenu: {(r.get('content') or '')[:500]}"
        for r in raw_results[:12]
    )

    bureau_list = ", ".join(f"{k}={v}" for k, v in BUREAU_LABELS.items())

    system = """Tu es l'archiviste de la bibliothèque ALNUA Hub.
À partir de résultats de recherche web, tu crées des fiches pour les bureaux de l'entreprise.

RÈGLES ABSOLUES:
- Ne jette AUCUNE information utile — tout va dans la bibliothèque.
- timing "now" = applicable tout de suite au Hub ou à un projet en cours.
- timing "later" = pas prioritaire aujourd'hui mais à conserver pour plus tard.
- Si tu hésites, mets "later" — jamais de suppression.
- summary = 2-4 phrases courtes pour l'UI / scan rapide.
- digest = synthèse riche (faits, chiffres, outils, dates, quand appliquer) — 150 à 400 mots si le contenu le permet.
- Réponds en JSON valide uniquement."""

    user = f"""Recherche demandée par Emilie (CEO): {query}

Bureaux possibles: {bureau_list}

Résultats web:
{results_text}

Réponds avec ce JSON:
{{
  "entries": [
    {{
      "bureau": "app",
      "title": "titre court",
      "summary": "2-4 phrases — ce que c'est et quand ça pourrait servir",
      "digest": "synthèse riche actionnable (150-400 mots) — faits clés, chiffres, outils, pièges",
      "timing": "now|later",
      "source_url": "url ou vide",
      "source_title": "titre source",
      "topics": ["IA", "UI"],
      "agent_id": "dev_app"
    }}
  ]
}}

Minimum 1 entrée si les résultats contiennent du contenu. Maximum 8 entrées."""

    try:
        from agents.base import LLMClient

        llm = LLMClient()
        raw = llm.complete(system, user, agent_id="coo", temperature=0.2)
        parsed = parse_json_response(raw)
        items = parsed.get("entries") if isinstance(parsed, dict) else []
        if not isinstance(items, list):
            return []
    except Exception as exc:
        logger.warning("library extract LLM failed: %s", exc)
        items = []

    saved: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        summary = str(item.get("summary") or "").strip()
        digest = str(item.get("digest") or "").strip()
        if not title and not summary and not digest:
            continue
        if not title:
            title = (summary or digest)[:80]
        if not summary and digest:
            summary = digest[:400]
        bureau = str(item.get("bureau") or "hub")
        agent_id = str(item.get("agent_id") or "")
        if not agent_id:
            agent_id = default_agent_for_bureau(bureau)
        timing = item.get("timing", "later")
        if timing not in ("now", "later"):
            timing = "later"
        saved.append(
            add_entry(
                bureau=bureau,
                title=title,
                summary=summary or title,
                digest=digest,
                timing=timing,
                source_url=str(item.get("source_url") or ""),
                source_title=str(item.get("source_title") or ""),
                topics=item.get("topics") if isinstance(item.get("topics"), list) else [],
                agent_id=agent_id,
                requested_by=requested_by,
                query=query,
            )
        )

    if not saved and raw_results:
        fallback = raw_results[0]
        saved.append(
            add_entry(
                bureau="hub",
                title=str(fallback.get("title") or query)[:300],
                summary=str(fallback.get("content") or query)[:2000],
                timing="later",
                source_url=str(fallback.get("url") or ""),
                source_title=str(fallback.get("title") or ""),
                topics=[query[:80]],
                agent_id="coo",
                requested_by=requested_by,
                query=query,
            )
        )

    return saved
