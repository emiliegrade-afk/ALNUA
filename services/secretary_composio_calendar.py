"""Google Calendar actions via Composio for Nadia."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from services.secretary_composio_gmail import execute
from services.secretary_composio_oauth import is_connected

_PARIS = ZoneInfo("Europe/Paris")


def extract_event_items(result: dict[str, Any]) -> list[dict[str, Any]]:
    """Unwrap the event list from a Composio Calendar response.

    Verified against the live API (2026-07-24): GOOGLECALENDAR_FIND_EVENT
    returns `data.event_data.event_data` (a list, double-nested) —
    `data.items`/`data.events` never actually occur but are kept as a
    fallback in case Composio's shape changes again.
    """
    data = result.get("data") or {}
    if isinstance(data, dict) and "data" in data:
        data = data["data"]
    if isinstance(data, list):
        return [ev for ev in data if isinstance(ev, dict)]
    if not isinstance(data, dict):
        return []
    event_data = data.get("event_data")
    if isinstance(event_data, dict):
        inner = event_data.get("event_data")
        if isinstance(inner, list):
            return [ev for ev in inner if isinstance(ev, dict)]
    if isinstance(event_data, list):
        return [ev for ev in event_data if isinstance(ev, dict)]
    items = data.get("items") or data.get("events") or []
    return [ev for ev in items if isinstance(ev, dict)] if isinstance(items, list) else []


def parse_event_row(ev: dict[str, Any]) -> dict[str, str]:
    start = ev.get("start") or {}
    when = start.get("dateTime") or start.get("date") or "?"
    return {
        "id": str(ev.get("id") or ""),
        "title": str(ev.get("summary") or ev.get("title") or "Sans titre")[:200],
        "when": str(when),
        "description": str(ev.get("description") or ""),
        "location": str(ev.get("location") or "")[:80],
    }


def fetch_calendar_events(*, days_ahead: int = 2) -> list[dict[str, str]]:
    if not is_connected("googlecalendar"):
        return []

    now = datetime.now(_PARIS)
    time_min = now.isoformat()
    time_max = (now + timedelta(days=days_ahead)).isoformat()

    for action, params in (
        (
            "GOOGLECALENDAR_FIND_EVENT",
            {"time_min": time_min, "time_max": time_max, "max_results": 12},
        ),
        (
            "GOOGLECALENDAR_EVENTS_LIST",
            {
                "time_min": time_min,
                "time_max": time_max,
                "max_results": 12,
                "calendar_id": "primary",
            },
        ),
    ):
        result = execute(action, params)
        if not result.get("success"):
            continue
        events: list[dict[str, str]] = []
        for ev in extract_event_items(result):
            start = ev.get("start") or {}
            when = start.get("dateTime") or start.get("date") or "?"
            events.append(
                {
                    "title": str(ev.get("summary") or ev.get("title") or "Sans titre")[:120],
                    "when": str(when),
                    "location": str(ev.get("location") or "")[:80],
                }
            )
        if events:
            return events
    return []


def create_calendar_event(
    title: str,
    start_datetime: str,
    *,
    description: str = "",
    duration_minutes: int = 60,
) -> dict[str, Any]:
    if not is_connected("googlecalendar"):
        return {
            "success": False,
            "error": "Google Calendar non connecté — /connect googlecalendar",
        }
    return execute(
        "GOOGLECALENDAR_CREATE_EVENT",
        {
            "summary": title,
            "start_datetime": start_datetime,
            "description": description,
            "event_duration_minutes": duration_minutes,
        },
    )


def update_calendar_event(
    event_id: str,
    *,
    title: str | None = None,
    start_datetime: str,
    description: str | None = None,
    duration_minutes: int = 60,
) -> dict[str, Any]:
    """Edit an existing event (title/date/description) — needs a fresh
    start_datetime on every call, GOOGLECALENDAR_UPDATE_EVENT requires it."""
    if not is_connected("googlecalendar"):
        return {
            "success": False,
            "error": "Google Calendar non connecté — /connect googlecalendar",
        }
    params: dict[str, Any] = {
        "event_id": event_id,
        "start_datetime": start_datetime,
        "event_duration_minutes": duration_minutes,
    }
    if title is not None:
        params["summary"] = title
    if description is not None:
        params["description"] = description
    return execute("GOOGLECALENDAR_UPDATE_EVENT", params)


def fetch_calendar_events_raw(*, days_ahead: int = 2, max_results: int = 20) -> list[dict[str, str]]:
    """Like fetch_calendar_events but keeps the event id — needed to later
    edit/validate a specific event (the trimmed version drops it)."""
    if not is_connected("googlecalendar"):
        return []

    now = datetime.now(_PARIS)
    result = execute(
        "GOOGLECALENDAR_FIND_EVENT",
        {
            "time_min": now.isoformat(),
            "time_max": (now + timedelta(days=days_ahead)).isoformat(),
            "max_results": max_results,
        },
    )
    if not result.get("success"):
        return []
    return [parse_event_row(ev) for ev in extract_event_items(result)]
