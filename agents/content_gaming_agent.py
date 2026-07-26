"""Content Gaming Agent — Kael Vex, contenu réseaux + devlogs Discord du pôle Gaming."""

from __future__ import annotations

from typing import Any

from agents.base import log_agent_action
from agents.content_agent import ContentAgent
from config.agent_operating_spec import get_system_prompt
from skills.skill_content_gaming import build_gaming_teaser_calendar, fetch_gaming_milestones, gen_hype_post
from skills.skill_social_scheduler import queue_post


class ContentGamingAgent(ContentAgent):
    AGENT_NAME = "content_gaming"
    SECTOR = "gaming"
    SYSTEM_PROMPT = get_system_prompt("content_gaming")

    def teaser_calendar(self, game: str = "wyrdheim", wishlist_target: str = "") -> dict[str, Any]:
        """Calendrier de teasers menant au wishlist/early-access."""
        return build_gaming_teaser_calendar(game, wishlist_target)

    def milestones(self, project: str = "wyrdheim") -> dict[str, Any]:
        """Derniers jalons UE5/Godot à transformer en contenu."""
        return fetch_gaming_milestones(project)

    def draft_hype_posts(
        self,
        project_id: str,
        hook: str,
        lore_snippet: str = "",
        media_type: str = "screenshot",
        platforms: list[str] | None = None,
        scheduled_for: str | None = None,
        post_devlog_now: bool = False,
    ) -> list[dict[str, Any]]:
        """Génère des posts hype multi-plateforme, met en queue, poste le devlog Discord si demandé."""
        drafts = gen_hype_post(hook, lore_snippet, media_type, platforms)
        queued: list[dict[str, Any]] = []
        for draft in drafts:
            content = draft["hook"] if not draft.get("body") else f"{draft['hook']}\n\n{draft['body']}"
            channel = "dev-log" if draft.get("discord_crosspost") else ""
            result = queue_post(
                project_id=project_id,
                platform=draft["platform"],
                content=content,
                sector=self.SECTOR,
                author_agent=self.AGENT_NAME,
                content_type=draft.get("content_type", "teaser"),
                hashtags=draft.get("hashtags", []),
                layout={
                    "hook": draft.get("hook", ""),
                    "body": draft.get("body", ""),
                    "media_hint": draft.get("media_hint", ""),
                },
                channel=channel,
                scheduled_for=scheduled_for,
                needs_review=not post_devlog_now,
                db=self.db,
            )
            if not result.get("ok"):
                continue
            queued.append(result["post"])
            if post_devlog_now and draft.get("discord_crosspost"):
                self.post_devlog_to_discord(content)

        log_agent_action(
            self.db, self.AGENT_NAME, "draft_hype_posts",
            input_summary=hook[:200],
            output_summary=f"{len(queued)} posts mis en queue",
        )
        return queued

    def post_devlog_to_discord(self, content: str, channel: str = "dev-log") -> dict[str, Any]:
        """Poste directement une MAJ/devlog sur le serveur Discord Wyrdheim."""
        from skills.skill_discord_wyrdheim import post_to_discord

        return post_to_discord(channel, content, embed=True)
