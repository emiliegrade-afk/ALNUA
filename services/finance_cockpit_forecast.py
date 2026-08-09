"""Deterministic finance cockpit forecast (Vague C / Phase 34).

Grounded on budget envelopes + fiscal obligations + optional SaaS spend.
No invented bank balances. Does not pay or transfer. LLM forecast stays on
ControllerAgent.build_forecast — this service feeds it real ledgers.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any


def build_cockpit_forecast(
    *,
    period: str | None = None,
    horizon_months: int = 6,
) -> dict[str, Any]:
    """Aggregate ledgers into a cockpit forecast snapshot."""
    from services.finance_budgets import budget_summary, list_budgets
    from services.finance_fiscal import fiscal_summary, list_obligations

    period = (period or date.today().strftime("%Y-%m")).strip()
    horizon = max(1, min(int(horizon_months), 24))

    budgets_all = list_budgets()
    budgets_period = list_budgets(period=period)
    bsum = budget_summary()
    fsum = fiscal_summary()
    open_fiscal = [
        o
        for o in list_obligations()
        if o.get("status") in ("upcoming", "due")
    ]

    allocated_period = sum(float(b.get("amount") or 0) for b in budgets_period)
    spent_period = sum(float(b.get("spent") or 0) for b in budgets_period)
    remaining_period = round(allocated_period - spent_period, 2)

    saas_monthly = 0.0
    saas_note = "SaaS non chargé"
    try:
        from services.saas_spend import build_saas_spend_report

        report = build_saas_spend_report(days=30)
        # Report is primarily USD-tracked; treat as monthly burn estimate.
        saas_monthly = float(report.get("total_tracked_usd") or 0)
        saas_note = "SaaS + LLM + manuels (USD trackés ~30j → mensuel estimé)"
    except Exception as exc:
        saas_note = f"SaaS indisponible: {exc}"

    # Burn ≈ period spend + open fiscal / horizon + saas
    fiscal_open_total = float(fsum.get("open_total") or 0)
    monthly_burn = round(
        spent_period + (fiscal_open_total / horizon) + saas_monthly,
        2,
    )
    runway_months: float | None
    if monthly_burn > 0 and remaining_period > 0:
        runway_months = round(remaining_period / monthly_burn, 1)
    elif remaining_period <= 0 and allocated_period > 0:
        runway_months = 0.0
    else:
        runway_months = None

    by_dept: list[dict[str, Any]] = []
    for b in budgets_period:
        amt = float(b.get("amount") or 0)
        spent = float(b.get("spent") or 0)
        by_dept.append(
            {
                "department": b.get("department"),
                "amount": amt,
                "spent": spent,
                "remaining": round(amt - spent, 2),
                "utilization_pct": round((spent / amt * 100) if amt else 0, 1),
            }
        )

    monthly: list[dict[str, Any]] = []
    year, month = int(period[:4]), int(period[5:7])
    carry = remaining_period
    for i in range(horizon):
        m = month + i
        y = year + (m - 1) // 12
        mm = ((m - 1) % 12) + 1
        key = f"{y:04d}-{mm:02d}"
        costs = round(monthly_burn, 2)
        carry = round(carry - costs, 2)
        monthly.append(
            {
                "month": key,
                "projected_costs": costs,
                "envelope_remaining_end": carry,
                "notes": "Projection linéaire — pas un solde bancaire.",
            }
        )

    assumptions = (
        f"Période {period}: enveloppes {allocated_period:.0f}€ "
        f"(dépensé {spent_period:.0f}€), fiscal ouvert {fiscal_open_total:.0f}€, "
        f"SaaS ~{saas_monthly:.0f}€/mois. Horizon {horizon} mois. "
        "Pas de transfert auto ni paiement Hub (DEC-016)."
    )

    return {
        "ok": True,
        "period": period,
        "horizon_months": horizon,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "budgets": {
            "summary": bsum,
            "period_allocated": round(allocated_period, 2),
            "period_spent": round(spent_period, 2),
            "period_remaining": remaining_period,
            "by_department": by_dept,
            "envelopes_total": len(budgets_all),
            "envelopes_period": len(budgets_period),
        },
        "fiscal": {
            "summary": fsum,
            "open_items": [
                {
                    "id": o.get("id"),
                    "title": o.get("title"),
                    "amount": o.get("amount"),
                    "due_date": o.get("due_date"),
                    "kind": o.get("kind"),
                    "status": o.get("status"),
                }
                for o in open_fiscal[:12]
            ],
        },
        "saas": {"monthly_estimate": round(saas_monthly, 2), "note": saas_note},
        "projection": {
            "monthly_burn_estimate": monthly_burn,
            "runway_months_on_envelopes": runway_months,
            "monthly_forecast": monthly,
        },
        "assumptions_for_llm": assumptions,
        "policies": {
            "budget_transfer": "reporté",
            "payments": "externes uniquement",
        },
    }
