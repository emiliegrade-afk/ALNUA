"""Finance agent — transaction fetch and aggregation."""

from __future__ import annotations

from calendar import monthrange
from collections import defaultdict
from datetime import date
from typing import Any

from database.supabase_client import SupabaseClient
from services.finance_agent_constants import CATEGORY_LABELS


def month_bounds(month: str) -> tuple[date, date]:
    """Return inclusive start/end dates for YYYY-MM."""
    year, mon = map(int, month.split("-"))
    last_day = monthrange(year, mon)[1]
    return date(year, mon, 1), date(year, mon, last_day)


def previous_month(month: str) -> str:
    year, mon = map(int, month.split("-"))
    if mon == 1:
        return f"{year - 1}-12"
    return f"{year:04d}-{mon - 1:02d}"


def is_income(tx_type: str) -> bool:
    return tx_type in ("income", "revenue")


def tx_date(tx: dict[str, Any]) -> date:
    return date.fromisoformat(str(tx["date"])[:10])


def fetch_transactions(
    db: SupabaseClient,
    *,
    month: str | None = None,
    tx_type: str | None = None,
    category: str | None = None,
    project_id: str | None = None,
) -> list[dict[str, Any]]:
    query = db.table("transactions").select("*").order("date", desc=True)
    if tx_type:
        query = query.eq("type", tx_type)
    if category:
        query = query.eq("category", category)
    if project_id:
        query = query.eq("project_id", project_id)
    response = query.execute()
    rows = response.data or []

    if month:
        start, end = month_bounds(month)
        rows = [r for r in rows if start <= tx_date(r) <= end]

    return rows


def compute_totals(transactions: list[dict[str, Any]]) -> dict[str, Any]:
    total_income = 0.0
    total_expenses = 0.0
    by_category: dict[str, float] = defaultdict(float)

    for tx in transactions:
        amount = float(tx["amount"])
        cat = tx.get("category") or "autre"
        by_category[cat] += amount
        if is_income(str(tx.get("type", ""))):
            total_income += amount
        else:
            total_expenses += amount

    balance = round(total_income - total_expenses, 2)
    return {
        "total_income": round(total_income, 2),
        "total_expenses": round(total_expenses, 2),
        "balance": balance,
        "by_category": {k: round(v, 2) for k, v in sorted(by_category.items())},
    }


def format_category_lines(totals: dict[str, float]) -> str:
    if not totals:
        return "— aucune"
    return ", ".join(
        f"{CATEGORY_LABELS.get(k, k)}: {v:.2f} EUR" for k, v in totals.items()
    )


def income_by_category(transactions: list[dict[str, Any]]) -> dict[str, float]:
    out: dict[str, float] = defaultdict(float)
    for tx in transactions:
        if is_income(str(tx.get("type", ""))):
            out[tx.get("category") or "autre"] += float(tx["amount"])
    return {k: round(v, 2) for k, v in out.items()}


def expense_by_category(transactions: list[dict[str, Any]]) -> dict[str, float]:
    out: dict[str, float] = defaultdict(float)
    for tx in transactions:
        if not is_income(str(tx.get("type", ""))):
            out[tx.get("category") or "autre"] += float(tx["amount"])
    return {k: round(v, 2) for k, v in out.items()}
