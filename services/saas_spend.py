"""SaaS spend catalogue + live aggregation for Jules / Rémi.

Sources:
- data/saas_subscriptions.json (recurring estimates)
- services/cost_monitor.py (OpenRouter LLM — live)
- services/manual_costs.py (hosting etc. — manual)
- services/revolut_business.py (bank expenses — when configured)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_CATALOG_PATH = Path(__file__).parent.parent / "data" / "saas_subscriptions.json"
_DOC_PATH = Path(__file__).parent.parent / "docs" / "CATALOGUE_ABONNEMENTS_ALNUA.md"


def load_saas_catalog() -> dict[str, Any]:
    if not _CATALOG_PATH.is_file():
        return {"tools": [], "currency": "USD", "updated": None}
    try:
        return json.loads(_CATALOG_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("saas catalog load failed: %s", exc)
        return {"tools": [], "currency": "USD", "updated": None}


def catalog_for_agents(*, max_chars: int = 3500) -> str:
    """Compact text block injected into Jules/Rémi prompts."""
    cat = load_saas_catalog()
    lines = [
        f"Catalogue abonnements ALNUA (maj {cat.get('updated', '?')}, {cat.get('currency', 'USD')}):",
    ]
    for t in cat.get("tools") or []:
        sync = t.get("sync", "?")
        monthly = t.get("monthly_usd")
        amt = f"{monthly}$/mois" if monthly is not None else "usage"
        lines.append(
            f"- {t.get('name')} [{sync}] {amt} · {t.get('plan', '')} · cat={t.get('category')}"
        )
    if _DOC_PATH.is_file():
        lines.append(f"Doc détaillée : {_DOC_PATH.as_posix()}")
    text = "\n".join(lines)
    return text[:max_chars]


def estimated_recurring_usd() -> float:
    cat = load_saas_catalog()
    total = 0.0
    for t in cat.get("tools") or []:
        if t.get("sync") in ("estimated", "manual") and t.get("monthly_usd"):
            total += float(t["monthly_usd"])
    return round(total, 2)


def build_saas_spend_report(*, days: int = 30) -> dict[str, Any]:
    """Unified spend picture for accounting cockpit + agents."""
    from services.cost_monitor import get_cost_report
    from services.manual_costs import get_manual_costs_report

    catalog = load_saas_catalog()
    llm = get_cost_report(days=days)
    manual = get_manual_costs_report(months=max(1, days // 30))

    openrouter_usd = float(llm.get("total_cost_usd") or llm.get("total_usd") or 0.0)
    # cost_monitor may use different key
    if not openrouter_usd and isinstance(llm.get("by_agent"), dict):
        openrouter_usd = round(
            sum(float(v.get("cost_usd", 0)) for v in llm["by_agent"].values()), 2
        )

    manual_usd = float(manual.get("total_usd") or 0.0)
    recurring_est = estimated_recurring_usd()

    revolut: dict[str, Any] = {"configured": False, "expenses": [], "total_eur": 0.0}
    try:
        from services.revolut_business import fetch_expenses_summary

        revolut = fetch_expenses_summary(days=days)
    except Exception as exc:
        revolut = {"configured": False, "error": str(exc)[:200], "expenses": [], "total_eur": 0.0}

    # Rough EUR≈USD for dashboard (accounting can refine FX later)
    revolut_as_usd = float(revolut.get("total_eur") or 0.0)

    live_sources = [
        {
            "id": "openrouter",
            "name": "OpenRouter LLM",
            "sync": "live",
            "amount_usd": openrouter_usd,
            "detail": llm,
        },
        {
            "id": "manual_ledger",
            "name": "Coûts manuels (hosting…)",
            "sync": "manual",
            "amount_usd": manual_usd,
            "detail": {"by_source": manual.get("by_source"), "entries": len(manual.get("entries") or [])},
        },
        {
            "id": "catalog_recurring",
            "name": "Abonnements catalogue (estimé)",
            "sync": "estimated",
            "amount_usd": recurring_est,
            "detail": {"tools": len(catalog.get("tools") or [])},
        },
        {
            "id": "revolut",
            "name": "Revolut Business",
            "sync": "live" if revolut.get("configured") else "pending_api",
            "amount_usd": revolut_as_usd,
            "detail": {k: v for k, v in revolut.items() if k != "expenses"},
        },
    ]

    total_tracked = round(openrouter_usd + manual_usd + recurring_est + revolut_as_usd, 2)

    return {
        "as_of": datetime.now(timezone.utc).isoformat(),
        "days": days,
        "currency_note": "USD sauf Revolut (EUR) — pas de FX auto",
        "total_tracked_usd": total_tracked,
        "sources": live_sources,
        "catalog": catalog,
        "catalog_brief": catalog_for_agents(),
        "gmail_ops": _gmail_status_snippet(),
    }


def _gmail_status_snippet() -> dict[str, Any]:
    try:
        from services.secretary_composio import (
            connected_gmail_email,
            expected_ceo_gmail,
            gmail_account_ok,
            is_connected,
        )

        return {
            "connected": is_connected("gmail"),
            "expected": expected_ceo_gmail(),
            "profile": connected_gmail_email(),
            "ok": gmail_account_ok(),
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:160]}
