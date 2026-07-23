"""Analytics Bot — syncs metrics from external sources into analytics table."""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

import httpx
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from bots.base import log_bot_action
from database.supabase_client import SupabaseClient, get_supabase

logger = logging.getLogger(__name__)

BOT_NAME = "analytics_bot"


class AnalyticsBot:
    def __init__(self, db: SupabaseClient | None = None) -> None:
        self.db = db or get_supabase()
        self.scheduler = BackgroundScheduler()

    def record_metric(
        self,
        project_id: str,
        metric_name: str,
        value: float,
        source: str,
        metric_date: date | None = None,
    ) -> dict[str, Any]:
        return self.db.insert(
            "analytics",
            {
                "project_id": project_id,
                "date": (metric_date or date.today()).isoformat(),
                "metric_name": metric_name,
                "value": value,
                "source": source,
            },
        )

    def fetch_plausible_stats(self, site_id: str) -> dict[str, float]:
        """Fetch visitor stats from Plausible API (requires PLAUSIBLE_API_KEY env)."""
        import os
        api_key = os.getenv("PLAUSIBLE_API_KEY", "")
        if not api_key:
            logger.debug("PLAUSIBLE_API_KEY not set, skipping")
            return {}
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(
                    "https://plausible.io/api/v1/stats/aggregate",
                    params={
                        "site_id": site_id,
                        "period": "day",
                        "metrics": "visitors,pageviews",
                    },
                    headers={"Authorization": f"Bearer {api_key}"},
                )
                response.raise_for_status()
                data = response.json()
            results = data.get("results", {})
            return {
                "web_visitors": float(results.get("visitors", {}).get("value", 0)),
            }
        except Exception as exc:
            logger.warning("Plausible fetch failed: %s", exc)
            return {}

    def run_cycle(self) -> dict[str, Any]:
        projects = self.db.select("projects")
        recorded = 0
        for project in projects:
            stats = self.fetch_plausible_stats(project["name"].lower().replace(" ", "-"))
            for metric_name, value in stats.items():
                if value > 0:
                    self.record_metric(project["id"], metric_name, value, "plausible")
                    recorded += 1

        summary = f"recorded={recorded}"
        log_bot_action(self.db, BOT_NAME, "run_cycle", f"{len(projects)} projects", summary)
        return {"recorded": recorded}

    def start_scheduler(self) -> None:
        self.scheduler.add_job(
            self.run_cycle,
            CronTrigger(hour=6, minute=0),
            id="analytics_daily",
            replace_existing=True,
        )
        self.scheduler.start()
        logger.info("AnalyticsBot scheduler started (daily 06:00)")
