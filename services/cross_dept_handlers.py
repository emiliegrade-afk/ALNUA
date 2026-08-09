"""Cross-department event handlers — Phase 36 MVP.

On project_validated / content_validated: enqueue honest work items for
Marketing, Accounting, Analytics. No fabricated metrics or auto LLM calls.
"""

from __future__ import annotations

import json
import logging
import threading
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


def _append(item: dict[str, Any]) -> None:
    with _LOCK:
        rows: list[dict[str, Any]] = []
        if _QUEUE.exists():
            try:
                rows = json.loads(_QUEUE.read_text(encoding="utf-8"))
            except Exception:
                rows = []
        if not isinstance(rows, list):
            rows = []
        rows.append(item)
        rows = rows[-_CAP:]
        _QUEUE.parent.mkdir(parents=True, exist_ok=True)
        _QUEUE.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")


def list_cross_dept_queue(*, limit: int = 50) -> list[dict[str, Any]]:
    with _LOCK:
        if not _QUEUE.exists():
            return []
        try:
            rows = json.loads(_QUEUE.read_text(encoding="utf-8"))
        except Exception:
            return []
    if not isinstance(rows, list):
        return []
    return list(reversed(rows[-max(1, min(limit, 200)) :]))


def _fan_out(event: Event, departments: list[tuple[str, str]]) -> None:
    title = (event.payload or {}).get("title") or (event.payload or {}).get("project_id") or ""
    for dept, action in departments:
        item = {
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
        }
        _append(item)
        logger.info(
            "cross_dept queued dept=%s action=%s event=%s",
            dept,
            action,
            event.event_type,
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
    """Content passed gate → schedule / measure hooks (queue only)."""
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
