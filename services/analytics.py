"""Business metrics aggregation — agent success, cost, latency, satisfaction."""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any


@dataclass
class DailyMetric:
    date: str
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_cost_usd: float = 0.0
    avg_latency_ms: float = 0.0
    feedback_positive: int = 0
    feedback_negative: int = 0


@dataclass
class AgentMetrics:
    agent_id: str
    success_rate: float = 0.0
    avg_cost_per_task: float = 0.0
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    user_satisfaction: float = 0.0
    last_7_days: list[DailyMetric] = field(default_factory=list)


# In-memory rolling store (7 days)
_task_log: dict[str, list[dict[str, Any]]] = defaultdict(list)
_feedback_log: dict[str, list[dict[str, Any]]] = defaultdict(list)
_MAX_ENTRIES = 5000


def record_task(
    agent_id: str,
    *,
    success: bool,
    cost_usd: float = 0.0,
    latency_ms: float = 0.0,
) -> None:
    entry = {
        "ts": time.time(),
        "success": success,
        "cost_usd": cost_usd,
        "latency_ms": latency_ms,
    }
    bucket = _task_log[agent_id]
    bucket.append(entry)
    if len(bucket) > _MAX_ENTRIES:
        _task_log[agent_id] = bucket[-_MAX_ENTRIES:]


def record_feedback(agent_id: str, *, rating: int, response_id: str) -> None:
    _feedback_log[agent_id].append({
        "ts": time.time(),
        "rating": rating,
        "response_id": response_id,
    })


def get_agent_metrics(agent_id: str, days: int = 7) -> AgentMetrics:
    cutoff = time.time() - days * 86400
    tasks = [t for t in _task_log.get(agent_id, []) if t["ts"] >= cutoff]
    feedback = [f for f in _feedback_log.get(agent_id, []) if f["ts"] >= cutoff]

    total = len(tasks)
    successes = sum(1 for t in tasks if t["success"])
    success_rate = round(100.0 * successes / total, 1) if total else 0.0

    costs = [t["cost_usd"] for t in tasks if t["cost_usd"] > 0]
    latencies = [t["latency_ms"] for t in tasks if t["latency_ms"] > 0]

    avg_cost = round(sum(costs) / len(costs), 4) if costs else 0.0
    avg_lat = round(sum(latencies) / len(latencies), 1) if latencies else 0.0
    p95 = 0.0
    if latencies:
        sorted_lat = sorted(latencies)
        p95 = sorted_lat[int(len(sorted_lat) * 0.95)]

    rated = [f for f in feedback if f["rating"] in (1, -1)]
    positive = sum(1 for f in rated if f["rating"] == 1)
    satisfaction = round(100.0 * positive / len(rated), 1) if rated else 0.0

    daily: dict[str, DailyMetric] = {}
    for i in range(days):
        d = (date.today() - timedelta(days=i)).isoformat()
        daily[d] = DailyMetric(date=d)

    for t in tasks:
        d = date.fromtimestamp(t["ts"]).isoformat()
        if d in daily:
            if t["success"]:
                daily[d].tasks_completed += 1
            else:
                daily[d].tasks_failed += 1
            daily[d].total_cost_usd += t["cost_usd"]
    for f in feedback:
        d = date.fromtimestamp(f["ts"]).isoformat()
        if d in daily:
            if f["rating"] == 1:
                daily[d].feedback_positive += 1
            elif f["rating"] == -1:
                daily[d].feedback_negative += 1

    return AgentMetrics(
        agent_id=agent_id,
        success_rate=success_rate,
        avg_cost_per_task=avg_cost,
        avg_latency_ms=avg_lat,
        p95_latency_ms=round(p95, 1),
        user_satisfaction=satisfaction,
        last_7_days=sorted(daily.values(), key=lambda m: m.date, reverse=True),
    )


def get_all_metrics(days: int = 7) -> dict[str, AgentMetrics]:
    agent_ids = set(_task_log.keys()) | set(_feedback_log.keys())
    return {aid: get_agent_metrics(aid, days) for aid in sorted(agent_ids)}
