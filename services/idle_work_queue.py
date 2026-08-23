"""Idle work day queue — DEC-021 / SPEC_IDLE_AGENT_WORK.

Persists the CEO day file (L0–L2 items). L0–L1 runnable without validation;
L2 requires ceo_validated. Self-dev requires trust >= 0.70.
Plan builder lives in ``idle_work_plan`` (Vague 5 split).
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from config.paths import get_hub_repo_path

logger = logging.getLogger(__name__)

_QUEUE_PATH = get_hub_repo_path() / "data" / "idle_queue.json"
_TRUST_SELF_DEV_MIN = 0.70

# Map Phase 30 autonomy_level (0–3) → max idle level allowed to auto-run.
_AUTONOMY_MAX_IDLE_LEVEL = {0: 0, 1: 1, 2: 2, 3: 2}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_queue(day: str | None = None) -> dict[str, Any]:
    return {
        "date": day or date.today().isoformat(),
        "ceo_validated": False,
        "validated_at": None,
        "items": [],
        "updated_at": _now_iso(),
    }


def load_queue() -> dict[str, Any]:
    if not _QUEUE_PATH.exists():
        return _default_queue()
    try:
        data = json.loads(_QUEUE_PATH.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return _default_queue()
        data.setdefault("items", [])
        data.setdefault("ceo_validated", False)
        return data
    except Exception as exc:
        logger.warning("idle_queue load failed: %s", exc)
        return _default_queue()


def save_queue(queue: dict[str, Any]) -> Path:
    _QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    queue["updated_at"] = _now_iso()
    _QUEUE_PATH.write_text(
        json.dumps(queue, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return _QUEUE_PATH


def clamp_autonomy(raw: Any) -> int:
    try:
        level = int(raw)
    except (TypeError, ValueError):
        level = 1
    return max(0, min(3, level))


def max_idle_level_for_autonomy(autonomy_level: int) -> int:
    return _AUTONOMY_MAX_IDLE_LEVEL.get(clamp_autonomy(autonomy_level), 1)


def budget_severity(*, daily_budget_usd: float | None = None) -> dict[str, Any]:
    from services.cost_monitor import check_budget_alert

    budget = daily_budget_usd
    if budget is None:
        try:
            from config.settings import settings

            budget = float(getattr(settings, "idle_daily_budget_usd", 10.0) or 10.0)
        except Exception:
            budget = 10.0
    return check_budget_alert(daily_budget_usd=budget)


def agent_trust_score(agent_id: str) -> float:
    try:
        from services.agent_trust import get_trust

        return float(get_trust(agent_id).get("score") or 0.0)
    except Exception:
        return 0.0


def validate_day_queue(
    *,
    validated: bool = True,
    promote_tickets: bool = True,
) -> dict[str, Any]:
    """CEO validates the day queue (unlocks L2). Optionally promotes idle-ok tickets once."""
    queue = load_queue()
    if queue.get("date") != date.today().isoformat():
        queue = build_day_plan(autonomy_level=int(queue.get("autonomy_level") or 1))
    was_validated = bool(queue.get("ceo_validated"))
    queue["ceo_validated"] = bool(validated)
    queue["validated_at"] = _now_iso() if validated else None
    if not validated:
        queue.pop("tickets_promoted_at", None)
    save_queue(queue)

    promote_result: dict[str, Any] | None = None
    # Auto-create [idle-ok] tickets once when unlocking L2 (Vague 3 / DEC-032).
    if (
        validated
        and promote_tickets
        and not was_validated
        and not queue.get("tickets_promoted_at")
    ):
        try:
            from services.idle_work_deliverables import promote_triage_to_tickets

            promote_result = promote_triage_to_tickets(dry_run=False)
            if int(promote_result.get("created_count") or 0) > 0:
                queue["tickets_promoted_at"] = _now_iso()
                save_queue(queue)
        except Exception as exc:
            logger.warning("idle auto-promote after validate failed: %s", exc)
            promote_result = {"ok": False, "error": str(exc)[:200]}

    out = dict(queue)
    if promote_result is not None:
        out["promote"] = promote_result
    return out


def _item_eligible(item: dict[str, Any], queue: dict[str, Any], severity: str) -> str | None:
    """Return skip reason or None if eligible."""
    if item.get("status") != "pending":
        return "not_pending"
    level = int(item.get("level") or 0)
    if level >= 3:
        return "l3_forbidden"
    if level >= 2 and not queue.get("ceo_validated"):
        return "l2_needs_ceo_validation"
    if severity == "critical":
        return "budget_critical"
    if severity == "warning" and item.get("family") in {"company", "self_dev", "lounge"}:
        return "budget_warning_deferred"
    if item.get("kind") == "self_dev":
        score = agent_trust_score(str(item.get("agent_id") or ""))
        if score < _TRUST_SELF_DEV_MIN:
            return f"trust_below_70 ({score:.2f})"
    return None


def pick_next_item(*, max_items: int = 1) -> dict[str, Any]:
    queue = load_queue()
    if queue.get("date") != date.today().isoformat():
        return {"ok": False, "reason": "stale_queue", "item": None, "queue": queue}

    alert = budget_severity()
    severity = str(alert.get("severity") or "ok")
    picked: list[dict[str, Any]] = []
    skips: list[dict[str, str]] = []

    for item in queue.get("items") or []:
        if len(picked) >= max_items:
            break
        reason = _item_eligible(item, queue, severity)
        if reason:
            skips.append({"id": item.get("id", ""), "reason": reason})
            continue
        picked.append(item)

    return {
        "ok": bool(picked),
        "reason": "picked" if picked else "nothing_eligible",
        "items": picked,
        "skips": skips[:20],
        "budget": alert,
        "queue": queue,
    }


def mark_item(
    item_id: str,
    *,
    status: str,
    run_id: str | None = None,
    detail: str = "",
) -> dict[str, Any]:
    queue = load_queue()
    for item in queue.get("items") or []:
        if item.get("id") == item_id:
            item["status"] = status
            item["finished_at"] = _now_iso()
            if run_id:
                item["run_id"] = run_id
            if detail:
                item["detail"] = detail[:500]
            break
    save_queue(queue)
    return queue


def build_day_plan(*, autonomy_level: int = 1) -> dict[str, Any]:
    """Build / refresh today's idle file — see ``idle_work_plan``."""
    from services.idle_work_plan import build_day_plan as _build

    return _build(autonomy_level=autonomy_level)
