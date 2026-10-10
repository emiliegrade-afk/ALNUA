"""Ads Agent — Léo Morel, Paid Media ALNUA (Meta/Google/TikTok Ads, budget & ROAS)."""

from __future__ import annotations

from typing import Any

from agents.agent_base import AgentBase
from agents.base import log_agent_action, run_with_learning
from config.agent_operating_spec import get_system_prompt
from skills.skill_ads import (
    amplify_organic_post,
    campaign_roi_report,
    check_budget_alert,
    draft_campaign,
)


class AdsAgent(AgentBase):
    AGENT_NAME = "ads"

    SYSTEM_PROMPT = get_system_prompt("ads")

    def create_campaign(
        self,
        brief: str,
        platform: str = "meta",
        budget_usd: float = 50.0,
        objective: str = "awareness",
        audience: str = "lookalike",
        project_id: str | None = None,
        name: str | None = None,
    ) -> dict[str, Any]:
        """Structure une campagne payante (A/B creative variants) et la persiste
        réellement dans `campaigns` — avant Phase 33 (ROADMAP.md) ce dict était
        volatile, aucune campagne n'existait après l'appel."""
        from services.permission_guard import require_capability

        require_capability(
            self.AGENT_NAME,
            "ads:spend",
            resource=f"platform:{platform}",
            meta={"budget_usd": budget_usd, "objective": objective},
        )
        result = draft_campaign(
            brief, platform=platform, budget_usd=budget_usd, objective=objective, audience=audience,
        )
        if not result.get("ok", True):
            log_agent_action(
                self.db, self.AGENT_NAME, "create_campaign",
                input_summary=f"{platform} | {objective} | ${budget_usd}",
                output_summary=str(result.get("error", ""))[:200],
                status="error",
            )
            return result

        campaign = self.db.insert("campaigns", {
            "name": name or brief[:80],
            "objective": objective,
            "platform": platform,
            "status": "draft",
            "budget_allocated_usd": budget_usd,
            "project_id": project_id,
            "audience": audience,
            "brief": brief,
            "created_by_agent_id": self.AGENT_NAME,
        })
        log_agent_action(
            self.db, self.AGENT_NAME, "create_campaign",
            input_summary=f"{platform} | {objective} | ${budget_usd}",
            output_summary=f"campaign {campaign['id']} created",
            status="success",
        )
        return {**result, "campaign": campaign}

    def amplify_post(
        self,
        post_id: str,
        platform: str = "meta",
        budget_usd: float = 10.0,
        audience: str = "lookalike",
    ) -> dict[str, Any]:
        """Booste un post organique existant (posts_queue) avec du budget payant."""
        from services.permission_guard import require_capability

        require_capability(
            self.AGENT_NAME,
            "ads:spend",
            resource=f"post:{post_id}",
            meta={"budget_usd": budget_usd, "platform": platform},
        )
        result = amplify_organic_post(post_id, platform=platform, budget_usd=budget_usd, audience=audience)
        log_agent_action(
            self.db, self.AGENT_NAME, "amplify_post",
            input_summary=f"{post_id} | {platform} | ${budget_usd}",
            output_summary=result.get("action", ""),
            status="success",
        )
        return result

    def get_campaign_report(self, campaign_id: str) -> dict[str, Any]:
        """Dépense réelle (transactions) et stats saisies. Pas de chiffres de régie."""
        return campaign_roi_report(campaign_id)

    def check_budget(self, monthly_budget: float, spent: float) -> dict[str, Any]:
        """Alerte de dépassement budgétaire (ok/warning/critical)."""
        return check_budget_alert(monthly_budget, spent)

    def handle_instruction(self, instruction: str) -> str:
        """Point d'entrée générique : stratégie pub, arbitrages budget, brief de campagne."""
        from skills.skill_agent_learning import get_learning_context, record_task_learning

        memory_block = get_learning_context(self.AGENT_NAME, instruction)
        prompt = f"{instruction}{memory_block}"
        result = run_with_learning(
            self.AGENT_NAME, instruction[:120],
            self.llm.complete,
            self.SYSTEM_PROMPT, prompt,
            agent_id=self.AGENT_NAME, temperature=0.4, max_tokens=4096,
        )
        try:
            record_task_learning(agent_id=self.AGENT_NAME, task=instruction, outcome=result)
        except Exception:
            pass
        log_agent_action(
            self.db, self.AGENT_NAME, "handle_instruction",
            input_summary=instruction[:200],
            output_summary=f"{result[:150]}...",
        )
        return result
