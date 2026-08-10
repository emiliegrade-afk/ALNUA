"""Finance agent — dashboard, recurring expenses, project enrichment."""

from __future__ import annotations

from datetime import date
from typing import Any

from database.supabase_client import SupabaseClient, get_supabase
from services.finance_agent_transactions import (
    compute_totals,
    fetch_transactions,
    tx_date,
)


def month_series(
    db: SupabaseClient,
    end_month: str,
    count: int,
) -> list[dict[str, Any]]:
    year, mon = map(int, end_month.split("-"))
    series: list[dict[str, Any]] = []
    for _ in range(count):
        key = f"{year:04d}-{mon:02d}"
        txs = fetch_transactions(db, month=key)
        totals = compute_totals(txs)
        series.append({"month": key, **totals})
        if mon == 1:
            year -= 1
            mon = 12
        else:
            mon -= 1
    return list(reversed(series))


def fetch_recurring_expenses(db: SupabaseClient) -> list[dict[str, Any]]:
    rows = (
        db.table("transactions")
        .select("*")
        .eq("is_recurring", True)
        .order("amount", desc=True)
        .execute()
    )
    return rows.data or []


def build_dashboard(db: SupabaseClient, month: str | None = None) -> dict[str, Any]:
    current = month or date.today().strftime("%Y-%m")
    current_tx = fetch_transactions(db, month=current)
    current_totals = compute_totals(current_tx)
    recurring = fetch_recurring_expenses(db)

    today = date.today()
    ytd_start = date(today.year, 1, 1)
    all_tx = db.select("transactions", order_by="date", ascending=True, limit=5000)
    ytd_tx = [t for t in all_tx if ytd_start <= tx_date(t) <= today]
    ytd = compute_totals(ytd_tx)

    return {
        "current_month": {
            "month": current,
            **current_totals,
            "recurring_count": len(recurring),
        },
        "last_3_months": month_series(db, current, 3),
        "last_6_months": month_series(db, current, 6),
        "recurring_expenses": recurring,
        "ytd_balance": ytd["balance"],
    }


def estimate_project(
    *,
    title: str,
    description: str = "",
    domain: str | None = None,
    effort: str | None = None,
    constraint: str | None = None,
    db: SupabaseClient | None = None,
) -> dict[str, Any]:
    """R&D dossier business case estimate (delegates to rnd_finance_estimate)."""
    from services.rnd_finance_estimate import estimate_rnd_project

    return estimate_rnd_project(
        title=title,
        description=description,
        domain=domain,
        effort=effort,
        db=db or get_supabase(),
        constraint=constraint,
    )


def attach_project_names(
    db: SupabaseClient,
    transactions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    projects = {p["id"]: p["name"] for p in db.select("projects", columns="id, name")}
    enriched: list[dict[str, Any]] = []
    for tx in transactions:
        row = dict(tx)
        pid = row.get("project_id")
        if pid and pid in projects:
            row["project_name"] = projects[pid]
        enriched.append(row)
    return enriched
