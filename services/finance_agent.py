"""Finance agent — monthly aggregation + OpenRouter summary."""

from __future__ import annotations

import json
import logging
from calendar import monthrange
from collections import defaultdict
from datetime import date
from typing import Any

import httpx

from config.settings import get_settings
from database.supabase_client import SupabaseClient, get_supabase

logger = logging.getLogger(__name__)

FINANCE_MODEL = "anthropic/claude-3-haiku"

EXPENSE_CATEGORIES = (
    "saas_tools",
    "hardware",
    "freelance",
    "marketing",
    "legal",
    "hosting",
    "formation",
    "autre",
)

INCOME_CATEGORIES = (
    "app_revenue",
    "grant",
    "consulting",
    "investment",
    "autre",
)

CATEGORY_LABELS: dict[str, str] = {
    "saas_tools": "Outils SaaS",
    "hardware": "Matériel",
    "freelance": "Freelance",
    "marketing": "Marketing",
    "legal": "Juridique",
    "hosting": "Hébergement",
    "formation": "Formation",
    "autre": "Autre",
    "app_revenue": "Revenus app",
    "grant": "Subvention",
    "consulting": "Consulting",
    "investment": "Investissement",
}

SYSTEM_PROMPT = (
    "Tu es l'agent comptable d'Emilie, fondatrice d'ALNUA. "
    "Tu génères des résumés mensuels financiers clairs, directs et positifs. "
    "Tu signales les anomalies (dépense inhabituelle, baisse de revenu) sans dramatiser."
)


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


def _is_income(tx_type: str) -> bool:
    return tx_type in ("income", "revenue")


def _tx_date(tx: dict[str, Any]) -> date:
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
        rows = [r for r in rows if start <= _tx_date(r) <= end]

    return rows


def compute_totals(transactions: list[dict[str, Any]]) -> dict[str, Any]:
    total_income = 0.0
    total_expenses = 0.0
    by_category: dict[str, float] = defaultdict(float)

    for tx in transactions:
        amount = float(tx["amount"])
        cat = tx.get("category") or "autre"
        by_category[cat] += amount
        if _is_income(str(tx.get("type", ""))):
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


def _format_category_lines(totals: dict[str, float]) -> str:
    if not totals:
        return "— aucune"
    return ", ".join(
        f"{CATEGORY_LABELS.get(k, k)}: {v:.2f} EUR"
        for k, v in totals.items()
    )


def _income_by_category(transactions: list[dict[str, Any]]) -> dict[str, float]:
    out: dict[str, float] = defaultdict(float)
    for tx in transactions:
        if _is_income(str(tx.get("type", ""))):
            out[tx.get("category") or "autre"] += float(tx["amount"])
    return {k: round(v, 2) for k, v in out.items()}


def _expense_by_category(transactions: list[dict[str, Any]]) -> dict[str, float]:
    out: dict[str, float] = defaultdict(float)
    for tx in transactions:
        if not _is_income(str(tx.get("type", ""))):
            out[tx.get("category") or "autre"] += float(tx["amount"])
    return {k: round(v, 2) for k, v in out.items()}


def _call_openrouter_summary(
    month: str,
    totals: dict[str, Any],
    income_cats: dict[str, float],
    expense_cats: dict[str, float],
    prev_totals: dict[str, Any] | None,
) -> str:
    settings = get_settings()
    if not settings.openrouter_api_key.strip():
        return _fallback_summary(month, totals, income_cats, expense_cats)

    prev_block = ""
    if prev_totals:
        prev_block = (
            f"\nMois précédent — Revenus: {prev_totals['total_income']:.2f} EUR, "
            f"Dépenses: {prev_totals['total_expenses']:.2f} EUR, "
            f"Balance: {prev_totals['balance']:.2f} EUR"
        )

    user_prompt = (
        f"Voici les transactions de {month} :\n"
        f"Revenus : {totals['total_income']:.2f} EUR — {_format_category_lines(income_cats)}\n"
        f"Dépenses : {totals['total_expenses']:.2f} EUR — {_format_category_lines(expense_cats)}\n"
        f"Balance : {totals['balance']:.2f} EUR"
        f"{prev_block}\n\n"
        "Génère un résumé mensuel en markdown avec :\n"
        f"## Résumé {month}\n"
        f"Solde net : {totals['balance']:.2f} EUR\n\n"
        "### ✅ Points positifs\n"
        "### ⚠️ Points d'attention (si applicable)\n"
        "### 💸 Top dépenses\n"
        "### 📊 Comparaison mois précédent (si données disponibles)\n"
        "### 💡 Recommandation (1 seule, actionnable)\n\n"
        "Max 200 mots."
    )

    payload = {
        "model": FINANCE_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.4,
        "max_tokens": 600,
    }
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://alnua-hub.local",
        "X-Title": "ALNUA Hub Finance",
    }

    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{settings.openrouter_base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception:
        logger.exception("OpenRouter finance summary failed")
        return _fallback_summary(month, totals, income_cats, expense_cats)


def _fallback_summary(
    month: str,
    totals: dict[str, Any],
    income_cats: dict[str, float],
    expense_cats: dict[str, float],
) -> str:
    top_expenses = sorted(expense_cats.items(), key=lambda x: x[1], reverse=True)[:3]
    top_lines = (
        ", ".join(f"{CATEGORY_LABELS.get(k, k)} ({v:.0f} €)" for k, v in top_expenses)
        if top_expenses
        else "Aucune dépense"
    )
    sign = "positif" if totals["balance"] >= 0 else "négatif"
    return (
        f"## Résumé {month}\n"
        f"Solde net : {totals['balance']:.2f} EUR\n\n"
        f"### ✅ Points positifs\n"
        f"Revenus du mois : {totals['total_income']:.2f} EUR.\n\n"
        f"### 💸 Top dépenses\n"
        f"{top_lines}\n\n"
        f"### 💡 Recommandation\n"
        f"Solde {sign} — vérifie les abonnements récurrents et reporte les grosses dépenses."
    )


def get_summary_row(db: SupabaseClient, month: str) -> dict[str, Any] | None:
    rows = db.select("financial_summaries", filters={"month": month}, limit=1)
    return rows[0] if rows else None


def generate_monthly_summary(month: str, *, force: bool = False) -> dict[str, Any]:
    """Aggregate month data, call LLM, persist summary."""
    db = get_supabase()
    existing = get_summary_row(db, month)
    if existing and not force and existing.get("summary_md"):
        return existing

    transactions = fetch_transactions(db, month=month)
    totals = compute_totals(transactions)
    income_cats = _income_by_category(transactions)
    expense_cats = _expense_by_category(transactions)

    prev_month = previous_month(month)
    prev_tx = fetch_transactions(db, month=prev_month)
    prev_totals = compute_totals(prev_tx) if prev_tx else None

    summary_md = _call_openrouter_summary(
        month, totals, income_cats, expense_cats, prev_totals
    )

    row_data = {
        "month": month,
        "summary_md": summary_md,
        "total_income": totals["total_income"],
        "total_expenses": totals["total_expenses"],
        "balance": totals["balance"],
        "by_category": totals["by_category"],
    }

    existing = get_summary_row(db, month)
    if existing:
        saved = db.update("financial_summaries", existing["id"], row_data)
    else:
        saved = db.insert("financial_summaries", row_data)

    return saved


def get_or_generate_summary(month: str) -> dict[str, Any]:
    db = get_supabase()
    existing = get_summary_row(db, month)
    if existing and existing.get("summary_md"):
        return existing
    return generate_monthly_summary(month, force=bool(existing))


def _month_series(
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
    ytd_tx = [t for t in all_tx if ytd_start <= _tx_date(t) <= today]
    ytd = compute_totals(ytd_tx)

    return {
        "current_month": {
            "month": current,
            **current_totals,
            "recurring_count": len(recurring),
        },
        "last_3_months": _month_series(db, current, 3),
        "last_6_months": _month_series(db, current, 6),
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
