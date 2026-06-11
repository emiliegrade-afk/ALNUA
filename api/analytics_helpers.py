"""Helpers pour agrégation analytics / transactions."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

PERIOD_DAYS: dict[str, int] = {
    "7d": 7,
    "30d": 30,
    "3m": 90,
    "6m": 180,
    "1y": 365,
}


def parse_period(period: str) -> tuple[date, date]:
    """Retourne (start, end) inclusifs pour une période relative."""
    end = date.today()
    days = PERIOD_DAYS.get(period, 30)
    start = end - timedelta(days=days - 1)
    return start, end


def month_bounds(reference: date | None = None) -> tuple[date, date]:
    """Premier et dernier jour du mois calendaire."""
    ref = reference or date.today()
    start = ref.replace(day=1)
    if ref.month == 12:
        end = ref.replace(day=31)
    else:
        end = (ref.replace(month=ref.month + 1, day=1) - timedelta(days=1))
    return start, end


def previous_month_bounds(reference: date | None = None) -> tuple[date, date]:
    ref = reference or date.today()
    first_this = ref.replace(day=1)
    last_prev = first_this - timedelta(days=1)
    return month_bounds(last_prev)


def pct_change(current: float | None, previous: float | None) -> float | None:
    if current is None or previous is None or previous == 0:
        return None
    return round((current - previous) / previous * 100, 1)


def filter_by_date_range(
    rows: list[dict[str, Any]],
    start: date,
    end: date,
    date_key: str = "date",
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for row in rows:
        raw = row.get(date_key)
        if not raw:
            continue
        d = date.fromisoformat(str(raw)[:10])
        if start <= d <= end:
            result.append(row)
    return result


def latest_values_by_project(
    rows: list[dict[str, Any]],
    metric_name: str,
    as_of: date | None = None,
) -> dict[str, float]:
    """Dernière valeur connue par projet pour une métrique."""
    cutoff = as_of or date.today()
    filtered = [
        r
        for r in rows
        if r.get("metric_name") == metric_name
        and date.fromisoformat(str(r["date"])[:10]) <= cutoff
    ]
    filtered.sort(key=lambda r: r["date"], reverse=True)
    latest: dict[str, float] = {}
    for row in filtered:
        pid = row["project_id"]
        if pid not in latest:
            latest[pid] = float(row["value"])
    return latest


def sum_metric_in_range(
    rows: list[dict[str, Any]],
    metric_name: str,
    start: date,
    end: date,
    project_id: str | None = None,
) -> float:
    total = 0.0
    for row in rows:
        if row.get("metric_name") != metric_name:
            continue
        if project_id and row.get("project_id") != project_id:
            continue
        d = date.fromisoformat(str(row["date"])[:10])
        if start <= d <= end:
            total += float(row["value"])
    return total
