"""Publisher Bot — publishes approved posts from posts_queue."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from bots.base import log_bot_action
from database.supabase_client import SupabaseClient, get_supabase

logger = logging.getLogger(__name__)

BOT_NAME = "publisher_bot"


class PublisherBot:
    """Checks posts_queue for approved posts due for publication."""

    def __init__(self, db: SupabaseClient | None = None) -> None:
        self.db = db or get_supabase()
        self.scheduler = BackgroundScheduler()

    def get_due_posts(self) -> list[dict[str, Any]]:
        now = datetime.now(timezone.utc).isoformat()
        all_approved = self.db.select("posts_queue", filters={"status": "approved"})
        due = []
        for post in all_approved:
            scheduled = post.get("scheduled_at", "")
            if scheduled and scheduled <= now:
                due.append(post)
        return due

    def publish_post(self, post: dict[str, Any]) -> bool:
        """Publish a single post to the configured platform."""
        platform = (post.get("platform") or "").lower()
        text = post.get("text_content") or ""
        logger.info("Publishing to %s: %s", platform, text[:80])

        if platform == "discord":
            from skills.skill_discord_wyrdheim import discord_is_configured, post_to_discord

            if not discord_is_configured():
                raise RuntimeError("Discord non configuré (DISCORD_BOT_TOKEN)")
            channel = post.get("channel") or "général"
            result = post_to_discord(channel, text, embed=False)
            if not result.get("success"):
                raise RuntimeError(result.get("error", "Échec post Discord"))

        elif platform in ("twitter", "x", "linkedin", "instagram"):
            try:
                from skills.skill_composio import composio_execute

                action_map = {
                    "twitter": "TWITTER_CREATION_OF_A_POST",
                    "x": "TWITTER_CREATION_OF_A_POST",
                    "linkedin": "LINKEDIN_CREATE_LINKED_IN_POST",
                }
                action = action_map.get(platform)
                if action:
                    composio_execute(
                        action,
                        {"text": text},
                        agent_name="marketing_agent",
                        user_id="alnua_marketing",
                    )
                else:
                    logger.info("Platform %s — logged only (no Composio action)", platform)
            except Exception as exc:
                logger.warning("Composio publish failed for %s: %s", platform, exc)
                raise

        self.db.update(
            "posts_queue",
            post["id"],
            {
                "status": "published",
                "published_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        return True

    def run_cycle(self) -> dict[str, Any]:
        due = self.get_due_posts()
        published = 0
        failed = 0
        for post in due:
            try:
                if self.publish_post(post):
                    published += 1
            except Exception as exc:
                logger.exception("Failed to publish post %s", post["id"])
                self.db.update("posts_queue", post["id"], {"status": "failed"})
                failed += 1

        summary = f"published={published}, failed={failed}, checked={len(due)}"
        log_bot_action(
            self.db,
            BOT_NAME,
            "run_cycle",
            input_summary=f"{len(due)} due posts",
            output_summary=summary,
            project_id=due[0]["project_id"] if due else None,
        )
        return {"published": published, "failed": failed, "checked": len(due)}

    def start_scheduler(self, cron: str = "*/15 * * * *") -> None:
        """Run every 15 minutes by default."""
        minute, hour, day, month, dow = cron.split()
        self.scheduler.add_job(
            self.run_cycle,
            CronTrigger(minute=minute, hour=hour, day=day, month=month, day_of_week=dow),
            id="publisher_cycle",
            replace_existing=True,
        )
        self.scheduler.start()
        logger.info("PublisherBot scheduler started (%s)", cron)

    def stop_scheduler(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    bot = PublisherBot()
    bot.start_scheduler()
    try:
        import time
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        bot.stop_scheduler()
