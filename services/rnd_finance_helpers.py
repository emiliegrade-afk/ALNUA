"""Finance estimate — stale detection and effort/domain helpers."""
from __future__ import annotations

from datetime import date
from typing import Any

from database.supabase_client import SupabaseClient
from services.finance_agent import fetch_recurring_expenses, fetch_transactions
from services.rnd_finance_constants import (
    BASE_OPEX_MONTHLY,
    DOSSIER_ENRICH_EUR,
    EFFORT_WEEKS,
    FINANCE_VERSION,
    HOURS_PER_WEEK,
    HOURLY_RATE_EUR,
    LEGACY_LLM_MONTHLY_EUR,
    LLM_EUR_PER_AGENT_WEEK,
    MARKETING_LAUNCH_EUR,
)


def is_stale_finance(finance: dict[str, Any] | None) -> bool:
    """True if finance_json needs recalculation (legacy human dev or pre-pricing model)."""
    if not finance:
        return False
    rev = finance.get("revenue_hypothesis") or {}
    if int(finance.get("finance_version") or 0) >= FINANCE_VERSION and rev.get("pricing_model"):
        return False
    if finance.get("cost_model") == "ai_solo":
        return not rev.get("pricing_model")
    assumptions = " ".join(finance.get("assumptions") or [])
    if "EUR/h" in assumptions or "@ 50" in assumptions:
        return True
    dev = float(finance.get("capex_dev_eur") or 0)
    llm = float(finance.get("capex_llm_agents_eur") or 0)
    return dev > 400 and llm == 0


def normalize_finance_for_display(finance: dict[str, Any]) -> dict[str, Any]:
    """Map legacy revenue fields so UI can render old dossiers until refresh."""
    if is_stale_finance(finance):
        return {**finance, "_stale": True}
    rev = dict(finance.get("revenue_hypothesis") or {})
    if rev.get("m12_monthly_run_rate_eur") is None and rev.get("revenue_m12_eur"):
        rev["m12_monthly_run_rate_eur"] = rev["revenue_m12_eur"]
    if rev.get("m6_monthly_run_rate_eur") is None and rev.get("revenue_m6_eur"):
        rev["m6_monthly_run_rate_eur"] = rev["revenue_m6_eur"]
    if rev.get("cumulative_12m_eur") is None and rev.get("m12_monthly_run_rate_eur"):
        m12 = float(rev["m12_monthly_run_rate_eur"])
        m6 = float(rev.get("m6_monthly_run_rate_eur") or m12 * 0.4)
        rev["cumulative_6m_eur"] = round(m6 * 3, 2)
        rev["cumulative_12m_eur"] = round(m6 * 3 + (m6 + m12) * 3, 2)
    return {**finance, "revenue_hypothesis": rev}


def effort_weeks(effort: str | None) -> int:
    return EFFORT_WEEKS.get((effort or "M").upper(), EFFORT_WEEKS["M"])


def apply_constraint(weeks: int, mult: float, constraint: str | None) -> tuple[int, float]:
    if not constraint or "reduce" not in constraint.lower():
        return weeks, mult
    if "50" in constraint:
        return max(1, int(weeks * 0.5)), mult * 0.7
    if "30" in constraint:
        return max(1, int(weeks * 0.7)), mult * 0.85
    return weeks, mult


def portfolio_snapshot(db: SupabaseClient) -> dict[str, Any]:
    """Real ALNUA numbers: apps revenue, recurring costs, project count."""
    try:
        projects = db.select("projects", order_by="name")
    except Exception:
        projects = []

    active_apps = [p for p in projects if p.get("branch") in ("app", "gaming", "robotics")]

    today = date.today()
    app_income_total = 0.0
    year, mon = today.year, today.month
    for _ in range(6):
        key = f"{year:04d}-{mon:02d}"
        txs = fetch_transactions(db, month=key)
        month_income = sum(
            float(t["amount"])
            for t in txs
            if str(t.get("type", "")) in ("income", "revenue")
        )
        app_rev = sum(
            float(t["amount"])
            for t in txs
            if str(t.get("type", "")) in ("income", "revenue")
            and (t.get("category") == "app_revenue" or t.get("project_id"))
        )
        app_income_total += app_rev if app_rev > 0 else month_income * 0.7
        if mon == 1:
            year -= 1
            mon = 12
        else:
            mon -= 1

    avg_monthly_income = round(app_income_total / 6, 2) if app_income_total else 0.0
    avg_per_app = round(avg_monthly_income / max(len(active_apps), 1), 2)

    recurring = fetch_recurring_expenses(db)
    recurring_monthly = round(
        sum(float(r.get("amount", 0)) for r in recurring if str(r.get("type", "expense")) != "income"),
        2,
    )

    return {
        "active_apps_count": len(active_apps),
        "active_app_names": [p.get("name", "") for p in active_apps[:8]],
        "portfolio_monthly_revenue_eur": avg_monthly_income,
        "portfolio_per_app_monthly_eur": avg_per_app,
        "portfolio_recurring_opex_eur": recurring_monthly,
    }


def capex_ai_solo(weeks: int, mult: float, constraint: str | None) -> dict[str, float]:
    llm_dev = round(weeks * LLM_EUR_PER_AGENT_WEEK * mult, 2)
    llm_dossier = round(DOSSIER_ENRICH_EUR * (0.5 if constraint else 1.0), 2)
    marketing = round(MARKETING_LAUNCH_EUR * (0.5 if constraint else 1.0), 2)
    total = round(llm_dev + llm_dossier + marketing, 2)
    return {
        "capex_eur": total,
        "capex_llm_agents_eur": llm_dev,
        "capex_dossier_llm_eur": llm_dossier,
        "capex_marketing_eur": marketing,
        "capex_dev_eur": llm_dev,
    }


def capex_human_dev(weeks: int, mult: float, constraint: str | None) -> dict[str, float]:
    dev_hours = weeks * HOURS_PER_WEEK
    dev = round(dev_hours * HOURLY_RATE_EUR * mult, 2)
    marketing = round(MARKETING_LAUNCH_EUR * (0.5 if constraint else 1.0), 2)
    total = round(dev + marketing, 2)
    return {
        "capex_eur": total,
        "capex_llm_agents_eur": 0.0,
        "capex_dossier_llm_eur": 0.0,
        "capex_dev_eur": dev,
        "capex_marketing_eur": marketing,
    }


def human_dev_opex_incremental(mult: float) -> float:
    return round((BASE_OPEX_MONTHLY + LEGACY_LLM_MONTHLY_EUR) * mult, 2)
