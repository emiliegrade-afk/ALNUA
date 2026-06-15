"""CreatorFlow — LLM content analysis for imported assets."""

from __future__ import annotations

import logging
from typing import Any

from agents.base import LLMClient, log_agent_action, parse_json_response
from database.supabase_client import get_supabase
from skills.skill_langfuse import trace_agent

logger = logging.getLogger(__name__)

AGENT_ID = "cf_content_analyzer"
FALLBACK_ANALYSIS: dict[str, Any] = {
    "themes": ["general"],
    "content_type": "entertainment",
    "quality_score": 0.7,
    "optimal_duration_youtube": 480,
    "optimal_duration_instagram": 60,
    "recommendations": ["Ajouter une accroche dans les 3 premières secondes"],
    "source": "fallback",
}

SYSTEM = """Tu analyses des assets créatifs pour CreatorFlow (créateurs solo).
Réponds UNIQUEMENT en JSON valide, sans markdown."""


class CfContentAnalyzer:
    def __init__(self) -> None:
        self.db = get_supabase()
        self.llm = LLMClient()

    @trace_agent(AGENT_ID)
    def analyze(self, asset: dict[str, Any]) -> dict[str, Any]:
        prompt = (
            f"Titre: {asset.get('title')}\n"
            f"Description: {asset.get('description') or 'N/A'}\n"
            f"Type: {asset.get('file_type')}\n"
            f"Durée (s): {asset.get('duration_seconds', 'N/A')}\n"
            f"MIME: {asset.get('mime_type', 'N/A')}\n\n"
            "Retourne ce JSON:\n"
            '{"themes":["..."],"content_type":"educational|entertainment|promotional",'
            '"quality_score":0.0,"optimal_duration_youtube":0,'
            '"optimal_duration_instagram":0,"recommendations":["..."]}'
        )
        try:
            if not self.llm._settings.openrouter_api_key.strip():
                return {**FALLBACK_ANALYSIS, "source": "no_api_key"}
            raw = self.llm.complete(
                SYSTEM,
                prompt,
                agent_id="content",
                temperature=0.3,
                max_tokens=800,
            )
            result = parse_json_response(raw)
            result["source"] = "llm"
            log_agent_action(
                self.db,
                AGENT_ID,
                "analyze_asset",
                asset.get("title", "")[:100],
                str(result)[:200],
            )
            return result
        except Exception as exc:
            logger.warning("cf_content_analyzer failed: %s", exc)
            return {**FALLBACK_ANALYSIS, "source": "error", "error": str(exc)[:200]}


def analyze_cf_asset(asset: dict[str, Any]) -> dict[str, Any]:
    return CfContentAnalyzer().analyze(asset)
