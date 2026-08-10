"""Compute budget envelope spend from tagged transactions (Phase 34).

Maps project.branch and expense category → budget department when transactions
lack an explicit department field.
"""

from __future__ import annotations

import logging
import re
from calendar import monthrange
from datetime import date
from typing import Any

logger = logging.getLogger(__name__)

BRANCH_TO_DEPT: dict[str, str] = {
    "app": "app",
    "gaming": "gaming",
    "robotics": "robo",
    "hub": "company",
    "other": "other",
}

CATEGORY_TO_DEPT: dict[str, str] = {
    "marketing": "marketing",
    "saas_tools": "finances",
    "hosting": "finances",
    "hardware": "robo",
    "freelance": "other",
    "legal": "company",
    "formation": "rnd",
    "autre": "other",
}

_MONTH_RE = re.compile(r"^(\d{4})-(\d{2})$")
_QUARTER_RE = re.compile(r"^(\d{4})-Q([1-4])$")


def period_date_bounds(period: str) -> tuple[date, date] | None:
    """Return inclusive date bounds for YYYY-MM or YYYY-Qn period keys."""
    m = _MONTH_RE.match(period.strip())
    if m:
        year, mon = int(m.group(1)), int(m.group(2))
        if not 1 <= mon <= 12:
            return None
        last = monthrange(year, mon)[1]
        return date(year, mon, 1), date(year, mon, last)
    q = _QUARTER_RE.match(period.strip())
    if q:
        year, qi = int(q.group(1)), int(q.group(2))
        start_mon = (qi - 1) * 3 + 1
        end_mon = start_mon + 2
        last = monthrange(year, end_mon)[1]
        return date(year, start_mon, 1), date(year, end_mon, last)
    return None


def tx_in_period(tx_date_str: str, period: str) -> bool:
    bounds = period_date_bounds(period)
    if bounds is None:
        return False
    try:
        tx_d = date.fromisoformat(str(tx_date_str)[:10])
    except ValueError:
        return False
    start, end = bounds
    return start <= tx_d <= end


def resolve_tx_department(
    tx: dict[str, Any],
    project_branch_by_id: dict[str, str],
) -> str:
    project_id = tx.get("project_id")
    if project_id and project_id in project_branch_by_id:
        branch = str(project_branch_by_id[project_id]).lower()
        return BRANCH_TO_DEPT.get(branch, "other")
    category = str(tx.get("category") or "autre").lower()
    return CATEGORY_TO_DEPT.get(category, "other")


def _load_expense_context() -> tuple[list[dict[str, Any]], dict[str, str]] | None:
    try:
        from database.supabase_client import get_supabase
        from services.finance_agent_transactions import is_income

        db = get_supabase()
        txs = db.select("transactions") or []
        expenses = [t for t in txs if not is_income(str(t.get("type", "")))]
        projects = db.select("projects") or []
        branch_map = {str(p["id"]): str(p.get("branch") or "other") for p in projects}
        return expenses, branch_map
    except Exception as exc:
        logger.debug("budget spent: transactions unavailable: %s", exc)
        return None


def computed_spent_by_dept_period(
    *,
    department: str | None = None,
    period: str | None = None,
) -> dict[tuple[str, str], float] | None:
    """Sum expenses per (department, period). None if ledger unavailable."""
    ctx = _load_expense_context()
    if ctx is None:
        return None
    expenses, branch_map = ctx
    totals: dict[tuple[str, str], float] = {}
    for tx in expenses:
        dept = resolve_tx_department(tx, branch_map)
        if department and dept != department:
            continue
        amount = float(tx.get("amount") or 0)
        tx_date_str = str(tx.get("date") or "")
        if period:
            if not tx_in_period(tx_date_str, period):
                continue
            key = (dept, period.strip())
            totals[key] = totals.get(key, 0.0) + amount
        else:
            # Attribute to every period key matching tx date — used rarely.
            for p_key in _period_keys_for_tx_date(tx_date_str):
                if department and dept != department:
                    continue
                key = (dept, p_key)
                totals[key] = totals.get(key, 0.0) + amount
    return {k: round(v, 2) for k, v in totals.items()}


def _period_keys_for_tx_date(tx_date_str: str) -> list[str]:
    try:
        tx_d = date.fromisoformat(str(tx_date_str)[:10])
    except ValueError:
        return []
    month_key = f"{tx_d.year:04d}-{tx_d.month:02d}"
    quarter = ((tx_d.month - 1) // 3) + 1
    return [month_key, f"{tx_d.year:04d}-Q{quarter}"]


def enrich_budget_row(
    row: dict[str, Any],
    computed: dict[tuple[str, str], float] | None,
) -> dict[str, Any]:
    """Overlay spent_manual / spent_computed / spent on a budget envelope."""
    out = dict(row)
    spent_manual = round(float(row.get("spent") or 0), 2)
    out["spent_manual"] = spent_manual
    dept = str(row.get("department") or "other")
    period = str(row.get("period") or "")
    spent_computed: float | None = None
    if computed is not None and period:
        spent_computed = computed.get((dept, period))
        if spent_computed is not None:
            spent_computed = round(float(spent_computed), 2)
    out["spent_computed"] = spent_computed
    out["spent"] = spent_computed if spent_computed is not None else spent_manual
    amt = float(row.get("amount") or 0)
    spent_eff = float(out["spent"])
    out["remaining"] = round(amt - spent_eff, 2)
    out["utilization_pct"] = round((spent_eff / amt * 100) if amt else 0.0, 1)
    return out


def severity_for_utilization(utilization_pct: float) -> str:
    if utilization_pct >= 100:
        return "critical"
    if utilization_pct >= 80:
        return "warning"
    return "ok"
