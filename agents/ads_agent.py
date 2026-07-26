"""Ads Agent — Léo Morel, Paid Media ALNUA. Meta/Google/TikTok Ads with budget tracking."""

from __future__ import annotations

from typing import Any

from agents.agent_base import AgentBase
from config.agent_operating_spec import get_system_prompt


class AdsAgent(AgentBase):
    AGENT_NAME = "ads"
    SYSTEM_PROMPT = get_system_prompt("ads")

    def handle_instruction(self, instruction: str) -> dict[str, Any]:
        return {"status": "queued", "agent": self.AGENT_NAME, "instruction": instruction[:200]}

    def create_campaign(
        self,
        brief: str,
        platform: str = "meta",
        budget_usd: float = 0,
        objective: str = "awareness",
    ) -> dict[str, Any]:
        return {
            "status": "draft",
            "platform": platform,
            "budget_usd": budget_usd,
            "objective": objective,
            "brief_preview": brief[:200],
        }

    def amplify_post(
        self,
        post_id: str,
        platform: str = "meta",
        budget_usd: float = 10.0,
        audience: str = "lookalike",
    ) -> dict[str, Any]:
        return {
            "status": "amplifying",
            "post_id": post_id,
            "platform": platform,
            "budget_usd": budget_usd,
            "audience": audience,
        }

    def get_campaign_report(self, campaign_id: str) -> dict[str, Any]:
        return {
            "campaign_id": campaign_id,
            "spend": 0,
            "impressions": 0,
            "clicks": 0,
            "roas": 0,
            "note": "stub — live Meta/Google API integration pending",
        }