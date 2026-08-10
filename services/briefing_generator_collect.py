"""Daily briefing — Supabase data collectors."""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

from database.supabase_client import SupabaseClient

logger = logging.getLogger(__name__)


def project_name_map(db: SupabaseClient) -> dict[str, str]:
    projects = db.select("projects", columns="id, name")
    return {p["id"]: p["name"] for p in projects}


def attach_project_names(
    rows: list[dict[str, Any]],
    names: dict[str, str],
) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        pid = item.get("project_id")
        if pid and pid in names:
            item["project_name"] = names[pid]
        enriched.append(item)
    return enriched


def collect_urgent_tickets(
    db: SupabaseClient,
    project_id: str | None,
    names: dict[str, str],
) -> list[dict[str, Any]]:
    query = (
        db.table("tickets")
        .select("*")
        .in_("priority", ["critical", "high"])
        .in_("status", ["open", "in_progress"])
        .order("created_at", desc=True)
    )
    if project_id:
        query = query.eq("project_id", project_id)
    response = query.execute()
    return attach_project_names(response.data or [], names)


def collect_pending_posts(
    db: SupabaseClient,
    project_id: str | None,
    names: dict[str, str],
) -> list[dict[str, Any]]:
    query = (
        db.table("posts_queue")
        .select("*")
        .eq("status", "pending_approval")
        .order("scheduled_at", desc=False)
    )
    if project_id:
        query = query.eq("project_id", project_id)
    response = query.execute()
    return attach_project_names(response.data or [], names)


def collect_imminent_roadmap(
    db: SupabaseClient,
    project_id: str | None,
    names: dict[str, str],
) -> list[dict[str, Any]]:
    today = date.today()
    horizon = (today + timedelta(days=7)).isoformat()
    query = (
        db.table("roadmap")
        .select("*")
        .neq("status", "done")
        .not_.is_("due_date", "null")
        .lte("due_date", horizon)
        .order("due_date", desc=False)
    )
    if project_id:
        query = query.eq("project_id", project_id)
    response = query.execute()
    rows = response.data or []
    return attach_project_names(rows, names)


def collect_recent_dev_log(
    db: SupabaseClient,
    project_id: str | None,
    names: dict[str, str],
) -> list[dict[str, Any]]:
    query = db.table("dev_log").select("*").order("created_at", desc=True).limit(3)
    if project_id:
        query = query.eq("project_id", project_id)
    try:
        response = query.execute()
    except Exception as exc:
        msg = str(exc)
        if "dev_log" in msg and ("PGRST205" in msg or "schema cache" in msg):
            logger.warning("dev_log table missing — skipping dev_log in briefing")
            return []
        raise
    return attach_project_names(response.data or [], names)


def collect_analytics_anomalies(
    db: SupabaseClient,
    project_id: str | None,
    names: dict[str, str],
) -> list[dict[str, Any]]:
    today = date.today()
    yesterday = today - timedelta(days=1)
    query = (
        db.table("analytics")
        .select("*")
        .in_("date", [today.isoformat(), yesterday.isoformat()])
    )
    if project_id:
        query = query.eq("project_id", project_id)
    response = query.execute()
    rows = response.data or []
    if not rows:
        return []

    by_key: dict[tuple[str, str, str], dict[str, float]] = {}
    for row in rows:
        key = (row["project_id"], row["metric_name"], row.get("source", ""))
        by_key.setdefault(key, {})[row["date"]] = float(row["value"])

    anomalies: list[dict[str, Any]] = []
    for (pid, metric, source), values in by_key.items():
        prev = values.get(yesterday.isoformat())
        curr = values.get(today.isoformat())
        if prev is None or curr is None or prev <= 0:
            continue
        drop_pct = ((prev - curr) / prev) * 100
        if drop_pct > 20:
            anomalies.append(
                {
                    "project_id": pid,
                    "project_name": names.get(pid, "—"),
                    "metric_name": metric,
                    "source": source,
                    "yesterday": prev,
                    "today": curr,
                    "drop_pct": round(drop_pct, 1),
                }
            )
    return anomalies
