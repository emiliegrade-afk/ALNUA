"""Reviews Bot — ingests app store / play store reviews into feedback."""

from __future__ import annotations

import logging
from typing import Any

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from agents.base import LLMClient
from bots.base import log_bot_action
from database.supabase_client import SupabaseClient, get_supabase

logger = logging.getLogger(__name__)

BOT_NAME = "reviews_bot"

SENTIMENT_PROMPT = """Analyse ce review et réponds UNIQUEMENT par un mot :
positive, negative, neutral, ou mixed.

Review : {content}"""


class ReviewsBot:
    def __init__(self, db: SupabaseClient | None = None, llm: LLMClient | None = None) -> None:
        self.db = db or get_supabase()
        self.llm = llm or LLMClient()
        self.scheduler = BackgroundScheduler()

    def classify_sentiment(self, content: str) -> str:
        try:
            result = self.llm.complete(
                "Tu es un classificateur de sentiment. Réponds en un seul mot.",
                SENTIMENT_PROMPT.format(content=content),
                temperature=0.0,
                max_tokens=10,
            )
            sentiment = result.strip().lower()
            if sentiment in ("positive", "negative", "neutral", "mixed"):
                return sentiment
        except Exception:
            logger.warning("Sentiment classification failed, defaulting to neutral")
        return "neutral"

    def ingest_review(
        self,
        project_id: str,
        source: str,
        content: str,
        author: str | None = None,
        rating: int | None = None,
    ) -> dict[str, Any]:
        sentiment = self.classify_sentiment(content)
        row = self.db.insert(
            "feedback",
            {
                "project_id": project_id,
                "source": source,
                "author": author,
                "content": content,
                "sentiment": sentiment,
                "rating": rating,
                "status": "new",
            },
        )
        return row

    def fetch_app_store_reviews(self, project_id: str) -> list[dict[str, Any]]:
        """Placeholder for App Store Connect API integration."""
        logger.info("fetch_app_store_reviews for project %s (stub)", project_id)
        return []

    def fetch_google_play_reviews(self, project_id: str) -> list[dict[str, Any]]:
        """Placeholder for Google Play Developer API integration."""
        logger.info("fetch_google_play_reviews for project %s (stub)", project_id)
        return []

    def run_cycle(self) -> dict[str, Any]:
        app_projects = self.db.select("projects", filters={"branch": "app"})
        ingested = 0
        for project in app_projects:
            for review in self.fetch_app_store_reviews(project["id"]):
                self.ingest_review(
                    project["id"],
                    "app_store",
                    review["content"],
                    review.get("author"),
                    review.get("rating"),
                )
                ingested += 1
            for review in self.fetch_google_play_reviews(project["id"]):
                self.ingest_review(
                    project["id"],
                    "google_play",
                    review["content"],
                    review.get("author"),
                    review.get("rating"),
                )
                ingested += 1

        summary = f"ingested={ingested}"
        log_bot_action(self.db, BOT_NAME, "run_cycle", "app projects scan", summary)
        return {"ingested": ingested}

    def start_scheduler(self) -> None:
        self.scheduler.add_job(
            self.run_cycle,
            CronTrigger(hour=8, minute=0),
            id="reviews_daily",
            replace_existing=True,
        )
        self.scheduler.start()
        logger.info("ReviewsBot scheduler started (daily 08:00)")
