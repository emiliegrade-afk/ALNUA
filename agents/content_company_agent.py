"""Content Company Agent — Anouk Gerard, voix de marque ALNUA + review cross-secteur."""

from __future__ import annotations

from typing import Any

from agents.base import log_agent_action
from agents.content_agent import ContentAgent
from config.agent_operating_spec import get_system_prompt
from skills.skill_content_company import BRAND_VOICE_GUIDE, gen_corporate_announcement, review_post_for_brand_voice
from skills.skill_social_scheduler import queue_post


class ContentCompanyAgent(ContentAgent):
    AGENT_NAME = "content_company"
    SECTOR = "company"
    SYSTEM_PROMPT = get_system_prompt("content_company")

    def brand_voice_guide(self) -> dict[str, str]:
        """Guide de voix de marque ALNUA (référence pour tous les secteurs)."""
        return dict(BRAND_VOICE_GUIDE)

    def review_brand_voice(self, post_text: str, sector: str = "") -> dict[str, Any]:
        """Review de cohérence de ton — à passer avant approbation d'un post d'un autre secteur."""
        return review_post_for_brand_voice(post_text, sector)

    def draft_corporate_announcement(
        self,
        project_id: str,
        topic: str,
        milestone_type: str = "milestone",
        scheduled_for: str | None = None,
    ) -> dict[str, Any]:
        """Rédige une annonce corporate (milestone/hiring/funding/partnership) et la met en queue."""
        draft = gen_corporate_announcement(topic, milestone_type)
        result = queue_post(
            project_id=project_id,
            platform=draft["platform"],
            content=draft["draft"],
            sector=self.SECTOR,
            author_agent=self.AGENT_NAME,
            content_type=draft.get("content_type", "announcement"),
            scheduled_for=scheduled_for,
            db=self.db,
        )
        log_agent_action(
            self.db, self.AGENT_NAME, "draft_corporate_announcement",
            input_summary=topic[:200],
            output_summary="queued" if result.get("ok") else result.get("error", ""),
        )
        return result
