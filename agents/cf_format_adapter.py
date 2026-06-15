"""CreatorFlow — adapt calendar content for platform constraints."""

from __future__ import annotations

import logging
from typing import Any

from agents.base import LLMClient, log_agent_action, parse_json_response
from database.supabase_client import get_supabase
from skills.skill_langfuse import trace_agent

logger = logging.getLogger(__name__)

AGENT_ID = "cf_format_adapter"

PLATFORM_SPECS: dict[str, dict[str, Any]] = {
    "youtube": {
        "max_title_length": 100,
        "max_description_length": 5000,
        "aspect_ratio": "16:9",
    },
    "instagram": {
        "max_description_length": 2200,
        "max_hashtags": 30,
        "aspect_ratio": "1:1 ou 9:16",
        "max_duration_seconds": 90,
    },
}

SYSTEM = """Tu adaptes du contenu créateur pour une plateforme sociale.
Réponds UNIQUEMENT en JSON valide, sans markdown."""


class CfFormatAdapter:
    def __init__(self) -> None:
        self.db = get_supabase()
        self.llm = LLMClient()

    @trace_agent(AGENT_ID)
    def adapt(self, calendar_entry: dict[str, Any], platform: str) -> dict[str, Any]:
        specs = PLATFORM_SPECS.get(platform, {})
        prompt = (
            f"Plateforme: {platform}\n"
            f"Titre: {calendar_entry.get('title')}\n"
            f"Caption: {calendar_entry.get('caption') or ''}\n"
            f"Hashtags: {calendar_entry.get('hashtags') or []}\n"
            f"Contraintes: {specs}\n\n"
            "JSON:\n"
            '{"adapted_title":"...","adapted_caption":"...",'
            '"adapted_hashtags":["..."],"format_notes":"..."}'
        )
        fallback = {
            "adapted_title": (calendar_entry.get("title") or "")[:100],
            "adapted_caption": (calendar_entry.get("caption") or "")[:2200],
            "adapted_hashtags": list(calendar_entry.get("hashtags") or [])[:30],
            "format_notes": "Passthrough fallback",
            "source": "fallback",
        }
        try:
            if not self.llm._settings.openrouter_api_key.strip():
                return fallback
            raw = self.llm.complete(
                SYSTEM,
                prompt,
                agent_id="content",
                temperature=0.3,
                max_tokens=1000,
            )
            result = parse_json_response(raw)
            result["source"] = "llm"
            log_agent_action(
                self.db,
                AGENT_ID,
                "adapt_for_platform",
                calendar_entry.get("title", "")[:80],
                str(result.get("adapted_title", ""))[:120],
            )
            return result
        except Exception as exc:
            logger.warning("cf_format_adapter failed: %s", exc)
            fallback["error"] = str(exc)[:200]
            return fallback


def adapt_cf_for_platform(calendar_entry: dict[str, Any], platform: str) -> dict[str, Any]:
    return CfFormatAdapter().adapt(calendar_entry, platform)
