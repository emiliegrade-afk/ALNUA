"""Content Robo Agent — Mira Solberg, contenu build-in-public du pôle Robotique."""

from __future__ import annotations

from typing import Any

from agents.base import log_agent_action
from agents.content_agent import ContentAgent
from config.agent_operating_spec import get_system_prompt
from skills.skill_content_robo import build_robo_story_arc, fetch_robo_milestones, gen_build_in_public_post
from skills.skill_social_scheduler import queue_post

# skill_content_robo parle en "blog" générique, la table posts_queue attend "website_blog".
_PLATFORM_ALIASES = {"blog": "website_blog"}


class ContentRoboAgent(ContentAgent):
    AGENT_NAME = "content_robo"
    SECTOR = "robo"
    SYSTEM_PROMPT = get_system_prompt("content_robo")

    def story_arc(self, project: str = "eve") -> dict[str, Any]:
        """Arc narratif build-in-public pour un projet robotique."""
        return build_robo_story_arc(project)

    def milestones(self, project: str = "eve") -> dict[str, Any]:
        """Derniers jalons hardware à transformer en contenu."""
        return fetch_robo_milestones(project)

    def draft_build_in_public(
        self,
        project_id: str,
        milestone: str,
        challenge: str = "",
        media_url: str = "",
        platforms: list[str] | None = None,
        scheduled_for: str | None = None,
    ) -> list[dict[str, Any]]:
        """Transforme un jalon hardware en posts build-in-public et les met en queue."""
        drafts = gen_build_in_public_post(milestone, challenge, media_url, platforms)
        queued: list[dict[str, Any]] = []
        for draft in drafts:
            result = queue_post(
                project_id=project_id,
                platform=_PLATFORM_ALIASES.get(draft["platform"], draft["platform"]),
                content=draft["text"],
                sector=self.SECTOR,
                author_agent=self.AGENT_NAME,
                content_type="behind_scenes",
                hashtags=draft.get("hashtags", []),
                media_urls=[draft["media_url"]] if draft.get("media_url") else [],
                scheduled_for=scheduled_for,
                db=self.db,
            )
            if result.get("ok"):
                queued.append(result["post"])
        log_agent_action(
            self.db, self.AGENT_NAME, "draft_build_in_public",
            input_summary=milestone[:200],
            output_summary=f"{len(queued)} posts mis en queue",
        )
        return queued
