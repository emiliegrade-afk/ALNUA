"""Cross-department event handlers — Phase 36 queue (fan-out only).

Drain / execution lives in ``cross_dept_drain`` so this file stays a thin
pub/sub adapter (no LLM here).
"""

from __future__ import annotations

import json
import logging
import threading
import uuid
from datetime import datetime, timezone
from typing import Any

from config.paths import get_hub_repo_path
from services.event_bus import Event, subscribe

logger = logging.getLogger(__name__)

_LOCK = threading.Lock()
_QUEUE = get_hub_repo_path() / "data" / "cross_dept_queue.json"
_CAP = 200


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_rows() -> list[dict[str, Any]]:
    if not _QUEUE.exists():
        return []
    try:
        rows = json.loads(_QUEUE.read_text(encoding="utf-8"))
    except Exception:
        return []
    return rows if isinstance(rows, list) else []


def _write_rows(rows: list[dict[str, Any]]) -> None:
    _QUEUE.parent.mkdir(parents=True, exist_ok=True)
    _QUEUE.write_text(
        json.dumps(rows[-_CAP:], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _append(item: dict[str, Any]) -> None:
    with _LOCK:
        rows = _read_rows()
        rows.append(item)
        _write_rows(rows)


def list_cross_dept_queue(
    *,
    limit: int = 50,
    status: str | None = None,
) -> list[dict[str, Any]]:
    with _LOCK:
        rows = _read_rows()
    if status:
        rows = [r for r in rows if r.get("status") == status]
    return list(reversed(rows[-max(1, min(limit, 200)) :]))


def get_queue_item(item_id: str) -> dict[str, Any] | None:
    with _LOCK:
        for row in _read_rows():
            if row.get("id") == item_id:
                return dict(row)
    return None


def update_queue_item(item_id: str, patch: dict[str, Any]) -> dict[str, Any] | None:
    with _LOCK:
        rows = _read_rows()
        updated: dict[str, Any] | None = None
        for i, row in enumerate(rows):
            if row.get("id") == item_id:
                rows[i] = {**row, **patch, "updated_at": _now()}
                updated = dict(rows[i])
                break
        if updated is None:
            return None
        _write_rows(rows)
        return updated


def _fan_out(event: Event, departments: list[tuple[str, str]]) -> None:
    title = (event.payload or {}).get("title") or (event.payload or {}).get("project_id") or ""
    for dept, action in departments:
        item = {
            "id": f"xd_{uuid.uuid4().hex[:12]}",
            "at": _now(),
            "event_type": event.event_type,
            "event_id": event.event_id,
            "department": dept,
            "action": action,
            "title": str(title)[:120],
            "payload": {
                k: event.payload.get(k)
                for k in ("project_id", "campaign_id", "score", "department", "producer_agent_id")
                if event.payload.get(k) is not None
            },
            "status": "queued",
            "result_summary": None,
            "artifact_path": None,
        }
        _append(item)
        logger.info(
            "cross_dept queued dept=%s action=%s event=%s id=%s",
            dept,
            action,
            event.event_type,
            item["id"],
        )


@subscribe("project_validated")
def on_project_validated(event: Event) -> None:
    """APP project validated → Marketing launch, Accounting forecast, Analytics KPIs."""
    _fan_out(
        event,
        [
            ("marketing", "draft_launch_plan"),
            ("finances", "draft_budget_forecast"),
            ("analytics", "prepare_kpi_sheet"),
        ],
    )


@subscribe("content_validated")
def on_content_validated(event: Event) -> None:
    _fan_out(
        event,
        [
            ("marketing", "schedule_distribution"),
            ("analytics", "track_content_performance"),
        ],
    )


@subscribe("campaign_validated")
def on_campaign_validated(event: Event) -> None:
    _fan_out(
        event,
        [
            ("finances", "link_campaign_budget"),
            ("analytics", "prepare_campaign_kpis"),
        ],
    )
