"""Department budget envelopes — allocation tracking without auto-transfer.

JSON ledger (same pattern as invoices). Agents never move money; Emilie
adjusts envelopes. Spent is computed from tagged transactions when available.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_PATH = Path(__file__).parent.parent / "data" / "budgets.json"

DEPARTMENTS = frozenset(
    {"app", "gaming", "robo", "marketing", "rnd", "finances", "company", "other"}
)


def _load() -> list[dict[str, Any]]:
    if not _PATH.is_file():
        return []
    try:
        rows = json.loads(_PATH.read_text(encoding="utf-8"))
        return rows if isinstance(rows, list) else []
    except Exception as exc:
        logger.warning("budgets load failed: %s", exc)
        return []


def _save(rows: list[dict[str, Any]]) -> None:
    _PATH.parent.mkdir(parents=True, exist_ok=True)
    _PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


def _enrich(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    from services.finance_budget_spent import computed_spent_by_dept_period, enrich_budget_row

    if not rows:
        return []
    periods = {str(r.get("period") or "") for r in rows if r.get("period")}
    computed: dict[tuple[str, str], float] | None = {}
    for period in periods:
        part = computed_spent_by_dept_period(period=period)
        if part is None:
            computed = None
            break
        computed.update(part)
    return [enrich_budget_row(r, computed) for r in rows]


def list_budgets(*, department: str | None = None, period: str | None = None) -> list[dict[str, Any]]:
    rows = _load()
    if department:
        rows = [r for r in rows if r.get("department") == department]
    if period:
        rows = [r for r in rows if r.get("period") == period]
    rows = sorted(rows, key=lambda r: (r.get("period") or "", r.get("department") or ""), reverse=True)
    return _enrich(rows)


def create_budget(
    *,
    department: str,
    period: str,
    amount: float,
    currency: str = "EUR",
    label: str = "",
    notes: str = "",
) -> dict[str, Any]:
    dept = department.strip().lower()
    if dept not in DEPARTMENTS:
        raise ValueError(f"department invalide: {department}")
    if not period or len(period) < 4:
        raise ValueError("period requis (ex. 2026-08 ou 2026-Q3)")
    if amount < 0:
        raise ValueError("amount must be >= 0")
    row = {
        "id": uuid.uuid4().hex[:12],
        "department": dept,
        "period": period.strip(),
        "amount": round(float(amount), 2),
        "currency": currency.upper(),
        "label": label.strip() or f"Budget {dept} {period}",
        "notes": notes.strip(),
        "spent": 0.0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "transfer_policy": "Manuel uniquement — budget_transfer workflow reporté (Vague 3).",
    }
    rows = _load()
    rows.append(row)
    _save(rows)
    return _enrich([row])[0]


def update_budget(budget_id: str, **updates: Any) -> dict[str, Any]:
    rows = _load()
    for i, row in enumerate(rows):
        if row.get("id") != budget_id:
            continue
        if "department" in updates and updates["department"] is not None:
            dept = str(updates["department"]).strip().lower()
            if dept not in DEPARTMENTS:
                raise ValueError(f"department invalide: {dept}")
            row["department"] = dept
        if "period" in updates and updates["period"] is not None:
            row["period"] = str(updates["period"]).strip()
        if "amount" in updates and updates["amount"] is not None:
            amt = float(updates["amount"])
            if amt < 0:
                raise ValueError("amount must be >= 0")
            row["amount"] = round(amt, 2)
        if "spent" in updates and updates["spent"] is not None:
            spent = float(updates["spent"])
            if spent < 0:
                raise ValueError("spent must be >= 0")
            row["spent"] = round(spent, 2)
        for key in ("label", "notes", "currency"):
            if key in updates and updates[key] is not None:
                row[key] = updates[key] if key != "currency" else str(updates[key]).upper()
        row["updated_at"] = datetime.now(timezone.utc).isoformat()
        rows[i] = row
        _save(rows)
        return _enrich([row])[0]
    raise KeyError(f"budget not found: {budget_id}")


def budget_summary(*, period: str | None = None) -> dict[str, Any]:
    rows = list_budgets(period=period) if period else list_budgets()
    total = sum(float(r.get("amount") or 0) for r in rows)
    # Dedupe (dept, period) so duplicate envelopes do not double-count spend.
    seen: set[tuple[str, str]] = set()
    spent = 0.0
    by_dept: dict[str, float] = {}
    for r in rows:
        d = str(r.get("department") or "other")
        p = str(r.get("period") or "")
        by_dept[d] = by_dept.get(d, 0.0) + float(r.get("amount") or 0)
        key = (d, p)
        if key in seen:
            continue
        seen.add(key)
        spent += float(r.get("spent") or 0)
    return {
        "count": len(rows),
        "total_allocated": round(total, 2),
        "total_spent": round(spent, 2),
        "remaining": round(total - spent, 2),
        "by_department": {k: round(v, 2) for k, v in by_dept.items()},
        "transfer_policy": "Pas de transfert auto — paiement/mouvement hors Hub.",
    }


def budget_alerts(*, period: str | None = None) -> dict[str, Any]:
    """Per-department utilization alerts for a period (default: current month)."""
    from services.finance_budget_spent import severity_for_utilization

    period_key = (period or date.today().strftime("%Y-%m")).strip()
    rows = list_budgets(period=period_key)
    by_dept: dict[str, dict[str, Any]] = {}
    spent_keys: set[tuple[str, str]] = set()
    for row in rows:
        dept = str(row.get("department") or "other")
        p = str(row.get("period") or period_key)
        agg = by_dept.setdefault(
            dept,
            {"department": dept, "allocated": 0.0, "spent": 0.0, "budget_count": 0},
        )
        agg["allocated"] = round(agg["allocated"] + float(row.get("amount") or 0), 2)
        agg["budget_count"] += 1
        sk = (dept, p)
        if sk not in spent_keys:
            spent_keys.add(sk)
            agg["spent"] = round(agg["spent"] + float(row.get("spent") or 0), 2)

    alerts: list[dict[str, Any]] = []
    for dept, agg in sorted(by_dept.items()):
        allocated = float(agg["allocated"])
        spent = float(agg["spent"])
        remaining = round(allocated - spent, 2)
        util = (spent / allocated * 100) if allocated else 0.0
        severity = severity_for_utilization(util)
        alerts.append(
            {
                "department": dept,
                "period": period_key,
                "allocated": allocated,
                "spent": spent,
                "remaining": remaining,
                "utilization_pct": round(util, 1),
                "severity": severity,
                "budget_count": agg["budget_count"],
            }
        )

    for alert in alerts:
        if alert["severity"] != "critical":
            continue
        try:
            from services.event_bus import emit

            emit(
                "budget_alert",
                payload={
                    "department": alert["department"],
                    "period": period_key,
                    "severity": "critical",
                    "spent": alert["spent"],
                    "allocated": alert["allocated"],
                    "utilization_pct": alert["utilization_pct"],
                },
                source_agent="finance_budgets",
            )
        except Exception as exc:
            logger.debug("budget_alert emit skipped: %s", exc)

    critical_count = sum(1 for a in alerts if a["severity"] == "critical")
    warning_count = sum(1 for a in alerts if a["severity"] == "warning")
    return {
        "period": period_key,
        "alerts": alerts,
        "critical_count": critical_count,
        "warning_count": warning_count,
        "thresholds": {"warning_pct": 80, "critical_pct": 100},
    }
