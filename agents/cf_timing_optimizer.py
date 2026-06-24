"""CreatorFlow — LLM optimal publishing time suggestions."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from agents.base import LLMClient, log_agent_action, parse_json_response
from config.agent_operating_spec import get_system_prompt
from database.supabase_client import SupabaseClient, get_supabase
from skills.skill_langfuse import trace_agent

logger = logging.getLogger(__name__)

AGENT_ID = "cf_timing_optimizer"

SYSTEM = get_system_prompt("cf_timing_optimizer")

_MOCK_HOURS = (18, 12, 9, 20, 17)
_MOCK_REASONS = (
    "Pic d'engagement historique en soirée",
    "Fenêtre lunch — forte portée mobile",
    "Publication matinale — visibilité algorithmique",
    "Prime time week-end",
    "Créneau habituel de ta niche",
)


def _mock_suggestions(platform: str) -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc)
    out: list[dict[str, Any]] = []
    for i, hour in enumerate(_MOCK_HOURS):
        day = now + timedelta(days=i + 1)
        slot = day.replace(hour=hour, minute=0, second=0, microsecond=0)
        out.append(
            {
                "platform": platform,
                "suggested_at": slot.isoformat(),
                "score": round(max(0.55, 0.95 - i * 0.08), 2),
                "reason": _MOCK_REASONS[i % len(_MOCK_REASONS)],
                "source": "mock",
            }
        )
    return out


def _parse_suggestions(raw: str, platform: str) -> list[dict[str, Any]]:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = lines[1:] if lines[0].startswith("```") else lines
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines)
    data = json.loads(cleaned)
    if isinstance(data, dict) and "suggestions" in data:
        data = data["suggestions"]
    if not isinstance(data, list):
        raise ValueError("Expected JSON array")
    normalized: list[dict[str, Any]] = []
    for item in data[:5]:
        normalized.append(
            {
                "platform": item.get("platform", platform),
                "suggested_at": item["suggested_at"],
                "score": float(item.get("score", 0.8)),
                "reason": str(item.get("reason", ""))[:500],
                "source": "llm",
            }
        )
    return normalized


class CfTimingOptimizer:
    def __init__(self, db: SupabaseClient | None = None) -> None:
        self.db = db or get_supabase()
        self.llm = LLMClient()

    @trace_agent(AGENT_ID)
    def get_suggestions(self, user_id: str, platform: str) -> list[dict[str, Any]]:
        history = self.db.select(
            "cf_exports",
            filters={"user_id": user_id, "platform": platform, "status": "success"},
            order_by="created_at",
            ascending=False,
            limit=20,
        )
        history_str = json.dumps(
            [{"created_at": r.get("created_at")} for r in history],
            ensure_ascii=False,
        ) or "[]"
        week_start = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")

        prompt = (
            f"Plateforme: {platform}\nHistorique exports réussis: {history_str}\n"
            f"Semaine cible à partir du {week_start}.\n\n"
            "Retourne un JSON array de 5 créneaux:\n"
            '[{"platform":"' + platform + '","suggested_at":"ISO8601","score":0.9,"reason":"..."}]'
        )
        try:
            if not self.llm._settings.openrouter_api_key.strip():
                return _mock_suggestions(platform)
            raw = self.llm.complete(
                SYSTEM,
                prompt,
                agent_id="content",
                temperature=0.4,
                max_tokens=1200,
            )
            result = _parse_suggestions(raw, platform)
            log_agent_action(
                self.db,
                AGENT_ID,
                "timing_suggestions",
                f"{platform} user={user_id[:8]}",
                f"{len(result)} slots",
            )
            return result
        except Exception as exc:
            logger.warning("cf_timing_optimizer failed: %s", exc)
            fallback = _mock_suggestions(platform)
            for item in fallback:
                item["source"] = "fallback"
            return fallback


def get_cf_timing_suggestions(
    user_id: str,
    platform: str,
    db: SupabaseClient | None = None,
) -> list[dict[str, Any]]:
    return CfTimingOptimizer(db).get_suggestions(user_id, platform)
