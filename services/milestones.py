"""Jalons à venir — real Google Calendar events (via Nadia/Composio), not a
static demo list. Milestones are calendar events tagged with a `[JALON]`
prefix in the title, so they stay visible/editable directly in the user's
own Google Calendar too.

Validation is tracked in a small local ledger keyed by calendar event id —
Google Calendar has no native "validated" flag, and round-tripping a custom
tag through the API on every validate click isn't worth the extra call.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

MILESTONE_TAG = "[JALON]"
_POLE_RE = re.compile(r"^\[\[pole:(?P<pole>[^\]]+)\]\]\n?", re.MULTILINE)

_LEDGER_FILE = Path(__file__).resolve().parent.parent / "data" / "milestones_state.json"


def _load_ledger() -> dict[str, Any]:
    if not _LEDGER_FILE.is_file():
        return {}
    try:
        return json.loads(_LEDGER_FILE.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("milestones ledger load failed: %s", exc)
        return {}


def _save_ledger(state: dict[str, Any]) -> None:
    _LEDGER_FILE.parent.mkdir(parents=True, exist_ok=True)
    _LEDGER_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _encode_description(pole: str, description: str) -> str:
    return f"[[pole:{pole}]]\n{description}" if pole else description


def _decode_description(raw: str) -> tuple[str, str]:
    m = _POLE_RE.match(raw or "")
    if not m:
        return "", raw or ""
    pole = m.group("pole")
    rest = _POLE_RE.sub("", raw, count=1)
    return pole, rest


def list_upcoming_milestones(*, days_ahead: int = 120) -> list[dict[str, Any]]:
    """Real upcoming milestones from Google Calendar (tagged [JALON])."""
    from services.secretary_composio import fetch_calendar_events_raw, is_connected

    if not is_connected("googlecalendar"):
        return []

    ledger = _load_ledger()
    rows = fetch_calendar_events_raw(days_ahead=days_ahead, max_results=50)
    milestones: list[dict[str, Any]] = []
    for row in rows:
        title = row.get("title", "")
        if not title.startswith(MILESTONE_TAG):
            continue
        pole, description = _decode_description(row.get("description", ""))
        state = ledger.get(row["id"], {})
        milestones.append(
            {
                "id": row["id"],
                "title": title[len(MILESTONE_TAG):].strip(),
                "date": row.get("when", ""),
                "pole": pole,
                "description": description,
                "validated": bool(state.get("validated", False)),
                "validated_at": state.get("validated_at"),
            }
        )
    milestones.sort(key=lambda m: m["date"])
    return milestones


def create_milestone(
    title: str,
    date_iso: str,
    *,
    pole: str = "",
    description: str = "",
) -> dict[str, Any]:
    from services.secretary_composio import create_calendar_event

    result = create_calendar_event(
        f"{MILESTONE_TAG} {title}",
        date_iso,
        description=_encode_description(pole, description),
        duration_minutes=30,
    )
    if not result.get("success"):
        return result

    data = result.get("data") or {}
    if isinstance(data, dict) and "data" in data:
        data = data["data"]
    # Composio wraps the real Google Calendar event under response_data.
    if isinstance(data, dict) and isinstance(data.get("response_data"), dict):
        data = data["response_data"]
    event_id = str(data.get("id") or "") if isinstance(data, dict) else ""
    return {"success": True, "id": event_id}


def update_milestone(
    event_id: str,
    *,
    title: str | None = None,
    date_iso: str,
    pole: str | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    from services.secretary_composio import update_calendar_event

    full_title = f"{MILESTONE_TAG} {title}" if title is not None else None
    full_description = (
        _encode_description(pole or "", description or "")
        if description is not None or pole is not None
        else None
    )
    return update_calendar_event(
        event_id,
        title=full_title,
        start_datetime=date_iso,
        description=full_description,
        duration_minutes=30,
    )


def set_milestone_validated(event_id: str, validated: bool) -> dict[str, Any]:
    ledger = _load_ledger()
    ledger[event_id] = {
        "validated": validated,
        "validated_at": datetime.now(timezone.utc).isoformat() if validated else None,
    }
    _save_ledger(ledger)
    return {"success": True, "id": event_id, "validated": validated}
