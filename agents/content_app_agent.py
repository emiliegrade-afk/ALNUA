"""Content App Agent — Esmée Diallo, contenu réseaux du pôle App (Naïa, Eve Journey's, futures apps)."""

from __future__ import annotations

from typing import Any

from agents.base import log_agent_action
from agents.content_agent import ContentAgent
from config.agent_operating_spec import get_system_prompt
from skills.skill_content_app import build_app_editorial_calendar, fetch_dev_activity, gen_content_from_dev_log
from skills.skill_social_scheduler import queue_post

# skill_content_app parle en "blog" générique, la table posts_queue attend "website_blog".
_PLATFORM_ALIASES = {"blog": "website_blog"}


class ContentAppAgent(ContentAgent):
    AGENT_NAME = "content_app"
    SECTOR = "app"
    SYSTEM_PROMPT = get_system_prompt("content_app")

    def editorial_calendar(self, apps: list[str] | None = None) -> dict[str, Any]:
        """Calendrier éditorial hebdo pour le pôle App."""
        return build_app_editorial_calendar(apps)

    def dev_activity(self, repo: str = "ALNUA", days: int = 7) -> dict[str, Any]:
        """Activité dev récente (commits/PR/releases) à transformer en contenu."""
        return fetch_dev_activity(repo, days)

    def draft_from_dev_log(
        self,
        project_id: str,
        dev_log: str,
        platforms: list[str] | None = None,
        scheduled_for: str | None = None,
    ) -> list[dict[str, Any]]:
        """Transforme un dev log en drafts multi-plateforme et les met en queue (pending_approval)."""
        drafts = gen_content_from_dev_log(dev_log, platforms)
        queued: list[dict[str, Any]] = []
        for draft in drafts:
            result = queue_post(
                project_id=project_id,
                platform=_PLATFORM_ALIASES.get(draft["platform"], draft["platform"]),
                content=draft["text"],
                sector=self.SECTOR,
                author_agent=self.AGENT_NAME,
                content_type=draft.get("content_type", "behind_scenes"),
                hashtags=draft.get("hashtags", []),
                layout={"media_hint": draft.get("media_hint", "")},
                scheduled_for=scheduled_for,
                db=self.db,
            )
            if result.get("ok"):
                queued.append(result["post"])
        log_agent_action(
            self.db, self.AGENT_NAME, "draft_from_dev_log",
            input_summary=dev_log[:200],
            output_summary=f"{len(queued)} posts mis en queue",
        )
        return queued
