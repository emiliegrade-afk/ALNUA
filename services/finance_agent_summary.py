"""Finance agent — LLM monthly summary generation and persistence."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from config.settings import get_settings
from database.supabase_client import SupabaseClient, get_supabase
from services.finance_agent_constants import CATEGORY_LABELS, FINANCE_MODEL, SYSTEM_PROMPT
from services.finance_agent_transactions import (
    compute_totals,
    expense_by_category,
    fetch_transactions,
    format_category_lines,
    income_by_category,
    previous_month,
)

logger = logging.getLogger(__name__)


def get_summary_row(db: SupabaseClient, month: str) -> dict[str, Any] | None:
    rows = db.select("financial_summaries", filters={"month": month}, limit=1)
    return rows[0] if rows else None


def fallback_summary(
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


def call_openrouter_summary(
    month: str,
    totals: dict[str, Any],
    income_cats: dict[str, float],
    expense_cats: dict[str, float],
    prev_totals: dict[str, Any] | None,
) -> str:
    settings = get_settings()
    if not settings.openrouter_api_key.strip():
        return fallback_summary(month, totals, income_cats, expense_cats)

    prev_block = ""
    if prev_totals:
        prev_block = (
            f"\nMois précédent — Revenus: {prev_totals['total_income']:.2f} EUR, "
            f"Dépenses: {prev_totals['total_expenses']:.2f} EUR, "
            f"Balance: {prev_totals['balance']:.2f} EUR"
        )

    user_prompt = (
        f"Voici les transactions de {month} :\n"
        f"Revenus : {totals['total_income']:.2f} EUR — {format_category_lines(income_cats)}\n"
        f"Dépenses : {totals['total_expenses']:.2f} EUR — {format_category_lines(expense_cats)}\n"
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
        return fallback_summary(month, totals, income_cats, expense_cats)


def generate_monthly_summary(month: str, *, force: bool = False) -> dict[str, Any]:
    """Aggregate month data, call LLM, persist summary."""
    db = get_supabase()
    existing = get_summary_row(db, month)
    if existing and not force and existing.get("summary_md"):
        return existing

    transactions = fetch_transactions(db, month=month)
    totals = compute_totals(transactions)
    income_cats = income_by_category(transactions)
    expense_cats = expense_by_category(transactions)

    prev_month = previous_month(month)
    prev_tx = fetch_transactions(db, month=prev_month)
    prev_totals = compute_totals(prev_tx) if prev_tx else None

    summary_md = call_openrouter_summary(
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
