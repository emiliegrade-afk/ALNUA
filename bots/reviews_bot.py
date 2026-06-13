"""Reviews Bot — ingests app store / play store reviews into feedback."""

from __future__ import annotations

import logging
import os
import re
from typing import Any

import httpx
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

# Env mapping: APP_STORE_ID_<SLUG>, GOOGLE_PLAY_PACKAGE_<SLUG> (slug uppercase)
_STORE_ID_PATTERN = re.compile(r"^APP_STORE_ID_(.+)$", re.I)
_PLAY_PACKAGE_PATTERN = re.compile(r"^GOOGLE_PLAY_PACKAGE_(.+)$", re.I)


def _store_ids_for_project(project: dict[str, Any]) -> tuple[str | None, str | None]:
    """Resolve App Store ID and Google Play package from env using project slug/name."""
    slug = (project.get("slug") or project.get("name") or "").lower()
    slug_key = re.sub(r"[^a-z0-9]+", "_", slug).upper().strip("_")

    app_id = os.getenv(f"APP_STORE_ID_{slug_key}", "").strip()
    play_pkg = os.getenv(f"GOOGLE_PLAY_PACKAGE_{slug_key}", "").strip()

    # Fallback: generic Naïa defaults
    if not app_id:
        app_id = os.getenv("APP_STORE_ID_NAIA", "").strip()
    if not play_pkg:
        play_pkg = os.getenv("GOOGLE_PLAY_PACKAGE_NAIA", "").strip()

    return app_id or None, play_pkg or None


class ReviewsBot:
    def __init__(self, db: SupabaseClient | None = None, llm: LLMClient | None = None) -> None:
        self.db = db or get_supabase()
        self.llm = llm or LLMClient()
        self.scheduler = BackgroundScheduler()
        self._seen: set[str] = set()

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
        external_id: str | None = None,
    ) -> dict[str, Any]:
        dedupe_key = f"{project_id}:{source}:{external_id or content[:80]}"
        if dedupe_key in self._seen:
            return {}
        self._seen.add(dedupe_key)

        # Skip if identical content already in DB (last 7 days)
        existing = self.db.select(
            "feedback",
            filters={"project_id": project_id, "source": source},
            limit=50,
        )
        for row in existing:
            if row.get("content") == content:
                return row

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

    def fetch_app_store_reviews(self, app_id: str, country: str = "fr") -> list[dict[str, Any]]:
        """Fetch recent reviews via Apple's public RSS JSON feed."""
        url = (
            f"https://itunes.apple.com/{country}/rss/customerreviews/"
            f"id={app_id}/sortBy=mostRecent/json"
        )
        try:
            with httpx.Client(timeout=30.0, follow_redirects=True) as client:
                res = client.get(url)
                res.raise_for_status()
                data = res.json()
        except Exception as exc:
            logger.warning("App Store RSS fetch failed for %s: %s", app_id, exc)
            return []

        entries = (
            data.get("feed", {}).get("entry") or []
        )
        if isinstance(entries, dict):
            entries = [entries]

        reviews: list[dict[str, Any]] = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            content = entry.get("content", {})
            if isinstance(content, dict):
                text = content.get("label", "")
            else:
                text = str(content)
            if not text or text.startswith("Im:"):
                continue
            author = entry.get("author", {}).get("name", {}).get("label")
            rating_raw = entry.get("im:rating", {}).get("label")
            rating = int(rating_raw) if rating_raw and str(rating_raw).isdigit() else None
            ext_id = entry.get("id", {}).get("label")
            reviews.append(
                {
                    "content": text.strip(),
                    "author": author,
                    "rating": rating,
                    "external_id": ext_id,
                }
            )
        return reviews[:50]

    def fetch_google_play_reviews(self, package_name: str) -> list[dict[str, Any]]:
        """Fetch reviews via google-play-scraper if installed, else HTML fallback."""
        try:
            from google_play_scraper import Sort, reviews as gp_reviews

            result, _continuation = gp_reviews(
                package_name,
                lang="fr",
                country="fr",
                sort=Sort.NEWEST,
                count=30,
            )
            return [
                {
                    "content": r.get("content", ""),
                    "author": r.get("userName"),
                    "rating": r.get("score"),
                    "external_id": r.get("reviewId"),
                }
                for r in result
                if r.get("content")
            ]
        except ImportError:
            logger.info("google-play-scraper not installed — skipping Play Store for %s", package_name)
            return []
        except Exception as exc:
            logger.warning("Google Play fetch failed for %s: %s", package_name, exc)
            return []

    def sync_project(self, project_id: str) -> int:
        projects = self.db.select("projects", filters={"id": project_id})
        if not projects:
            return 0
        return self._sync_one(projects[0])

    def _sync_one(self, project: dict[str, Any]) -> int:
        ingested = 0
        app_id, play_pkg = _store_ids_for_project(project)
        pid = project["id"]

        if app_id:
            for review in self.fetch_app_store_reviews(app_id):
                row = self.ingest_review(
                    pid,
                    "app_store",
                    review["content"],
                    review.get("author"),
                    review.get("rating"),
                    review.get("external_id"),
                )
                if row:
                    ingested += 1

        if play_pkg:
            for review in self.fetch_google_play_reviews(play_pkg):
                row = self.ingest_review(
                    pid,
                    "google_play",
                    review["content"],
                    review.get("author"),
                    review.get("rating"),
                    review.get("external_id"),
                )
                if row:
                    ingested += 1

        return ingested

    def run_cycle(self) -> dict[str, Any]:
        app_projects = self.db.select("projects", filters={"branch": "app"})
        ingested = 0
        for project in app_projects:
            ingested += self._sync_one(project)

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
