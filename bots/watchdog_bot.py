"""Watchdog Bot — monitors system health, stuck jobs, and alerts."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from bots.base import log_bot_action
from database.supabase_client import SupabaseClient, get_supabase

logger = logging.getLogger(__name__)

BOT_NAME = "watchdog_bot"


class WatchdogBot:
    STALE_HOURS = 24

    def __init__(self, db: SupabaseClient | None = None) -> None:
        self.db = db or get_supabase()
        self.scheduler = BackgroundScheduler()
        self._alerts: list[str] = []

    def check_stuck_posts(self) -> list[str]:
        alerts = []
        failed = self.db.select("posts_queue", filters={"status": "failed"})
        for post in failed:
            alerts.append(f"Post failed: {post['id']} ({post['platform']})")
        return alerts

    def check_critical_tickets(self) -> list[str]:
        alerts = []
        tickets = self.db.select("tickets", filters={"status": "open"})
        critical = [t for t in tickets if t.get("priority") == "critical"]
        for ticket in critical:
            alerts.append(f"Ticket critique ouvert: {ticket['title']} ({ticket['id']})")
        return alerts

    def check_agent_errors(self) -> list[str]:
        alerts = []
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=self.STALE_HOURS)).isoformat()
        logs = self.db.select(
            "agent_logs",
            filters={"status": "error"},
            order_by="created_at",
            ascending=False,
            limit=20,
        )
        for log in logs:
            if log.get("created_at", "") >= cutoff:
                alerts.append(
                    f"Erreur agent {log['agent_name']}: {log['action']} — {log['output_summary'][:100]}"
                )
        return alerts

    def check_unprocessed_feedback(self, threshold: int = 50) -> list[str]:
        new_feedback = self.db.select("feedback", filters={"status": "new"})
        if len(new_feedback) >= threshold:
            return [f"{len(new_feedback)} feedbacks non traités (seuil: {threshold})"]
        return []

    def run_health_check(self) -> dict[str, Any]:
        self._alerts = []
        self._alerts.extend(self.check_stuck_posts())
        self._alerts.extend(self.check_critical_tickets())
        self._alerts.extend(self.check_agent_errors())
        self._alerts.extend(self.check_unprocessed_feedback())

        status = "healthy" if not self._alerts else "degraded"
        for alert in self._alerts:
            logger.warning("WATCHDOG: %s", alert)

        log_bot_action(
            self.db,
            BOT_NAME,
            "run_health_check",
            input_summary="full scan",
            output_summary=f"status={status}, alerts={len(self._alerts)}",
            status="success" if status == "healthy" else "error",
        )
        return {"status": status, "alerts": self._alerts}

    def start_scheduler(self) -> None:
        self.scheduler.add_job(
            self.run_health_check,
            CronTrigger(minute="*/30"),
            id="watchdog_half_hourly",
            replace_existing=True,
        )
        self.scheduler.start()
        logger.info("WatchdogBot scheduler started (every 30 min)")
