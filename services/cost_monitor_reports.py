"""Cost monitor — aggregated reports and budget alerts."""

from __future__ import annotations

import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from services.cost_monitor_store import ensure_loaded
from services import cost_monitor_store


def get_cost_report(
    agent_id: str | None = None,
    days: int = 7,
    model: str | None = None,
) -> dict[str, Any]:
    """Cost report by agent over N days."""
    ensure_loaded()
    cutoff = time.time() - days * 86400
    entries = [e for e in cost_monitor_store._cost_log if e.get("ts", 0) > cutoff]

    if agent_id:
        entries = [e for e in entries if e.get("agent_id") == agent_id]
    if model:
        entries = [e for e in entries if e.get("model") == model]

    by_agent: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"calls": 0, "cost_usd": 0.0, "prompt_tokens": 0, "completion_tokens": 0}
    )
    by_model: dict[str, dict[str, Any]] = defaultdict(lambda: {"calls": 0, "cost_usd": 0.0})
    by_day: dict[str, float] = defaultdict(float)

    for e in entries:
        aid = e.get("agent_id", "unknown")
        mod = e.get("model", "unknown")
        day = e.get("date", "unknown")
        cost = e.get("cost_usd", 0.0)

        by_agent[aid]["calls"] += 1
        by_agent[aid]["cost_usd"] += cost
        by_agent[aid]["prompt_tokens"] += e.get("prompt_tokens", 0)
        by_agent[aid]["completion_tokens"] += e.get("completion_tokens", 0)

        by_model[mod]["calls"] += 1
        by_model[mod]["cost_usd"] += cost

        by_day[day] += cost

    total_cost = sum(e.get("cost_usd", 0.0) for e in entries)

    return {
        "period_days": days,
        "agent_id_filter": agent_id,
        "total_calls": len(entries),
        "total_cost_usd": round(total_cost, 4),
        "by_agent": {
            k: {**v, "cost_usd": round(v["cost_usd"], 4)}
            for k, v in sorted(by_agent.items(), key=lambda x: x[1]["cost_usd"], reverse=True)
        },
        "by_model": {
            k: {**v, "cost_usd": round(v["cost_usd"], 4)}
            for k, v in sorted(by_model.items(), key=lambda x: x[1]["cost_usd"], reverse=True)
        },
        "by_day": dict(sorted(by_day.items())),
        "most_expensive_agent": max(
            by_agent, key=lambda k: by_agent[k]["cost_usd"], default=None
        ),
    }


def get_monthly_summary(month: str | None = None) -> dict[str, Any]:
    """Monthly LLM cost summary for Jules (accounting)."""
    ensure_loaded()
    if not month:
        month = datetime.now(timezone.utc).strftime("%Y-%m")

    entries = [e for e in cost_monitor_store._cost_log if e.get("date", "").startswith(month)]
    total = sum(e.get("cost_usd", 0.0) for e in entries)
    calls = len(entries)

    by_agent: dict[str, float] = defaultdict(float)
    for e in entries:
        by_agent[e.get("agent_id", "unknown")] += e.get("cost_usd", 0.0)

    return {
        "month": month,
        "total_cost_usd": round(total, 4),
        "total_calls": calls,
        "avg_cost_per_call_usd": round(total / calls, 6) if calls else 0,
        "by_agent": {
            k: round(v, 4) for k, v in sorted(by_agent.items(), key=lambda x: x[1], reverse=True)
        },
        "projection_30d_usd": round(
            total * 30 / max(1, len({e.get("date") for e in entries})), 2
        ),
    }


def check_budget_alert(
    daily_budget_usd: float = 5.0,
    agent_id: str | None = None,
) -> dict[str, Any]:
    """Check whether daily budget is exceeded."""
    ensure_loaded()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    entries = [e for e in cost_monitor_store._cost_log if e.get("date") == today]
    if agent_id:
        entries = [e for e in entries if e.get("agent_id") == agent_id]

    spent = sum(e.get("cost_usd", 0.0) for e in entries)
    pct = spent / daily_budget_usd * 100 if daily_budget_usd > 0 else 0
    alert = spent >= daily_budget_usd

    return {
        "date": today,
        "agent_id_filter": agent_id,
        "daily_budget_usd": daily_budget_usd,
        "spent_usd": round(spent, 4),
        "remaining_usd": round(max(0, daily_budget_usd - spent), 4),
        "pct_used": round(pct, 1),
        "alert": alert,
        "severity": "critical" if pct >= 100 else "warning" if pct >= 80 else "ok",
        "calls_today": len(entries),
    }


def get_top_costs(limit: int = 10, days: int = 7) -> list[dict[str, Any]]:
    """Top N most expensive calls over N days."""
    ensure_loaded()
    cutoff = time.time() - days * 86400
    entries = [e for e in cost_monitor_store._cost_log if e.get("ts", 0) > cutoff]
    return sorted(entries, key=lambda e: e.get("cost_usd", 0), reverse=True)[:limit]
