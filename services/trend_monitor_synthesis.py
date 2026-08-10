"""Trend monitor — LLM synthesis."""

from __future__ import annotations

import logging
from typing import Any

from services.trend_monitor_models import TrendItem

logger = logging.getLogger(__name__)


def llm_synthesize_trends(items: list[TrendItem], topics: list[str], agent_id: str = "marketing") -> dict[str, Any]:
    """Utilise LLMClient pour générer un brief de tendances."""
    try:
        from agents.base import LLMClient, parse_json_response
        from services.input_sanitizer import sanitize_user_input
        llm = LLMClient()

        top_items_text = "\n".join([
            f"- [{item.source.upper()}] "
            f"{sanitize_user_input(item.title, max_length=300)} "
            f"(score: {item.score})"
            for item in items[:20]
        ])

        topics_str = ", ".join(topics) if topics else "général"

        system = """Tu es Camille Rousseau, responsable Marketing d'ALNUA.
Tu analyses les tendances du marché pour identifier des opportunités de contenu.
Réponds en JSON valide structuré."""

        prompt = f"""Analyse ces {len(items)} tendances actuelles pour les topics : {topics_str}

TOP TENDANCES :
{top_items_text}

Génère un brief JSON avec :
- synthesis (string): résumé en 2-3 phrases des trends dominantes
- key_signals (list[string]): 3-5 signaux clés à retenir (chacun < 15 mots)
- content_angles (list[string]): 3-5 angles de contenu exploitables pour ALNUA (posts, articles, social)
- urgency (string): "now" | "this_week" | "this_month" selon l'opportunité
- top_platform (string): meilleure plateforme pour capitaliser sur ces trends"""

        raw = llm.complete(system, prompt, agent_id=agent_id, temperature=0.3)
        return parse_json_response(raw)
    except Exception as e:
        logger.warning(f"LLM synthesis failed: {e}")
        return {
            "synthesis": "Synthèse indisponible (LLM error).",
            "key_signals": [item.title for item in items[:3]],
            "content_angles": [],
            "urgency": "this_week",
            "top_platform": "linkedin",
        }
