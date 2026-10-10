"""Secretary — résumé et graphique structurés pour le cockpit Live."""
from __future__ import annotations

import json
import logging
from typing import Any

from agents.base import parse_json_response
from skills.skill_agent_learning import inject_learning_context

logger = logging.getLogger(__name__)

CHART_KEYS = ("graphique", "graphe", "courbe", "histogramme", "chart")
SUMMARY_KEYS = ("résumé", "resume", "synthèse", "synthese")


def wants_chart(instruction: str) -> bool:
    lower = instruction.lower()
    return any(key in lower for key in CHART_KEYS)


def wants_summary(instruction: str) -> bool:
    lower = instruction.lower()
    if wants_chart(lower):
        return False
    return any(key in lower for key in SUMMARY_KEYS)


class SecretaryHandlersBriefMixin:
    """Requires ``SecretaryInstructionMixin._finish_instruction`` and ``AgentBase``."""

    def _handle_chart(self, instruction: str) -> str:
        prompt = inject_learning_context(
            f"""Emilie veut un graphique à partir de :
{instruction}

Réponds UNIQUEMENT en JSON :
{{"title":"titre court","points":[{{"label":"...","value":0}}]}}
Au moins 3 points. value = nombre. Pas de texte autour.""",
            self.AGENT_NAME,
            instruction[:80],
        )
        data = self._brief_json(prompt)
        title = str(data.get("title") or "Graphique")
        points = _clean_points(data.get("points"))
        if len(points) < 2:
            out = "Je n'ai pas assez de chiffres pour tracer un graphique. Donne-moi les valeurs."
            self._finish_instruction(instruction, out)
            return out
        payload = {"title": title, "points": points}
        out = f"{title}\n\n```chart\n{json.dumps(payload, ensure_ascii=False)}\n```"
        self._finish_instruction(instruction, out[:200])
        return out

    def _handle_summary(self, instruction: str) -> str:
        prompt = inject_learning_context(
            f"""Emilie veut un résumé clair de :
{instruction}

Réponds UNIQUEMENT en JSON :
{{"headline":"une phrase","bullets":["fait 1","fait 2","fait 3"]}}
3 à 6 puces concrètes. Pas de texte autour.""",
            self.AGENT_NAME,
            instruction[:80],
        )
        data = self._brief_json(prompt)
        headline = str(data.get("headline") or "Résumé").strip()
        bullets = [
            str(item).strip()
            for item in (data.get("bullets") or [])
            if str(item).strip()
        ]
        if not bullets:
            out = headline or "Je n'ai pas pu construire le résumé."
            self._finish_instruction(instruction, out)
            return out
        payload = {"headline": headline, "bullets": bullets[:8]}
        out = f"{headline}\n\n```summary\n{json.dumps(payload, ensure_ascii=False)}\n```"
        self._finish_instruction(instruction, out[:200])
        return out

    def _brief_json(self, prompt: str) -> dict[str, Any]:
        try:
            raw = self._complete(prompt, temperature=0.3)
            parsed = parse_json_response(raw)
            return parsed if isinstance(parsed, dict) else {}
        except Exception as exc:
            logger.warning("brief json failed: %s", exc)
            return {}


def _clean_points(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    points: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label") or "").strip()
        try:
            value = float(item.get("value"))
        except (TypeError, ValueError):
            continue
        if not label:
            continue
        points.append({"label": label[:40], "value": value})
    return points[:12]
