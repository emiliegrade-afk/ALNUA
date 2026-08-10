"""Cost monitor — Hub UI / lobby adapter shapes."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from services.cost_monitor_reports import get_monthly_summary
from services.cost_monitor_store import ensure_loaded
from services import cost_monitor_store


def get_daily_costs(target_date: date | None = None) -> dict[str, Any]:
    """Daily costs grouped by agent (Hub UI + lobby)."""
    ensure_loaded()
    if target_date is None:
        target_date = date.today()

    day_key = target_date.isoformat()
    entries = [e for e in cost_monitor_store._cost_log if e.get("date") == day_key]

    by_agent: dict[str, dict[str, Any]] = {}
    total = 0.0
    for e in entries:
        name = e.get("agent_id", "unknown")
        cost = float(e.get("cost_usd", 0.0))
        total += cost
        if name not in by_agent:
            by_agent[name] = {
                "total_usd": 0.0,
                "calls": 0,
                "tokens_in": 0,
                "tokens_out": 0,
            }
        by_agent[name]["total_usd"] = round(by_agent[name]["total_usd"] + cost, 6)
        by_agent[name]["calls"] += 1
        by_agent[name]["tokens_in"] += e.get("prompt_tokens", 0)
        by_agent[name]["tokens_out"] += e.get("completion_tokens", 0)

    return {
        "date": day_key,
        "total_usd": round(total, 4),
        "by_agent": by_agent,
    }


def get_monthly_costs() -> dict[str, Any]:
    """Current month costs — lobby / finances format."""
    today = date.today()
    month_prefix = today.strftime("%Y-%m")
    summary = get_monthly_summary(month=month_prefix)
    return {
        "month": today.strftime("%B %Y"),
        "total_usd": summary.get("total_cost_usd", 0.0),
        "by_agent": summary.get("by_agent", {}),
    }


def get_weekly_costs() -> dict[str, Any]:
    """Last 7 days — Hub dashboard format."""
    ensure_loaded()
    today = date.today()
    start = today - timedelta(days=6)

    by_date: dict[str, dict[str, float]] = {}
    total = 0.0
    for e in cost_monitor_store._cost_log:
        day = e.get("date", "")
        if not day:
            continue
        try:
            d = date.fromisoformat(day)
        except ValueError:
            continue
        if d < start or d > today:
            continue
        agent = e.get("agent_id", "unknown")
        cost = float(e.get("cost_usd", 0.0))
        total += cost
        by_date.setdefault(day, {})
        by_date[day][agent] = round(by_date[day].get(agent, 0.0) + cost, 6)

    by_day: list[dict[str, Any]] = []
    for i in range(7):
        d = start + timedelta(days=i)
        key = d.isoformat()
        entry: dict[str, Any] = {"date": d.strftime("%d/%m")}
        for agent, cost in by_date.get(key, {}).items():
            entry[agent] = round(cost, 4)
        by_day.append(entry)

    return {"total_usd": round(total, 4), "by_day": by_day}
