"""Finance estimate — core estimate_rnd_project and verdict reasoning."""
from __future__ import annotations

import logging
from typing import Any

from database.supabase_client import SupabaseClient, get_supabase
from services.finance_agent import build_dashboard
from services.rnd_finance_constants import (
    COST_MODEL,
    DOMAIN_MULTIPLIER,
    FINANCE_VERSION,
    PROJECT_HOSTING_MONTHLY_EUR,
)
from services.rnd_finance_helpers import (
    apply_constraint,
    capex_ai_solo,
    capex_human_dev,
    effort_weeks,
    human_dev_opex_incremental,
    portfolio_snapshot,
)
from services.rnd_pricing_model import revenue_from_pricing

logger = logging.getLogger(__name__)


def estimate_rnd_project(
    *,
    title: str,
    description: str = "",
    domain: str | None = None,
    effort: str | None = None,
    db: SupabaseClient | None = None,
    constraint: str | None = None,
    section_text: str = "",
) -> dict[str, Any]:
    """Build finance_json grounded in solo+AI costs and real Hub treasury."""
    db = db or get_supabase()
    weeks = effort_weeks(effort)
    mult = DOMAIN_MULTIPLIER.get((domain or "autre").lower(), 1.0)
    weeks, mult = apply_constraint(weeks, mult, constraint)

    portfolio = portfolio_snapshot(db)

    if COST_MODEL == "human_dev":
        capex_parts = capex_human_dev(weeks, mult, constraint)
        opex_incremental = human_dev_opex_incremental(mult)
        cost_model_label = "freelance/humain (legacy)"
    else:
        capex_parts = capex_ai_solo(weeks, mult, constraint)
        opex_incremental = round(PROJECT_HOSTING_MONTHLY_EUR * mult, 2)
        cost_model_label = "solo + agents IA (OpenRouter)"

    opex_existing = portfolio["portfolio_recurring_opex_eur"]
    opex_monthly = round(opex_existing + opex_incremental, 2)
    llm_share = round(capex_parts.get("capex_llm_agents_eur", 0) / max(weeks, 1) / 4, 2)

    try:
        dashboard = build_dashboard(db)
        treasury_ytd = float(dashboard.get("ytd_balance") or 0)
        current = dashboard.get("current_month") or {}
        monthly_balance = float(current.get("balance") or 0)
    except Exception as exc:
        logger.warning("rnd_finance: dashboard unavailable: %s", exc)
        treasury_ytd = 0.0
        monthly_balance = 0.0

    rev = revenue_from_pricing(
        domain=domain,
        effort=effort,
        title=title,
        description=description,
        section_text=section_text,
        constraint=constraint,
        portfolio_monthly=portfolio["portfolio_monthly_revenue_eur"],
        per_app_monthly=portfolio["portfolio_per_app_monthly_eur"],
        active_apps=portfolio["active_apps_count"],
    )

    pricing = rev.get("pricing_model") or {}
    subs = rev.get("paying_subscribers") or {}
    arpu = rev.get("blended_arpu_eur") or 0

    capex_total = capex_parts["capex_eur"]
    net_6m = round(rev["cumulative_6m_eur"] - capex_total - opex_incremental * 6, 2)
    net_12m = round(rev["cumulative_12m_eur"] - capex_total - opex_incremental * 12, 2)

    monthly_burn_new = opex_incremental
    net_monthly_m12 = rev["m12_monthly_run_rate_eur"] - monthly_burn_new
    break_even_months = (
        int(capex_total / net_monthly_m12) + 1 if net_monthly_m12 > 0 else None
    )

    runway_impact = round(capex_total / max(monthly_burn_new, 1), 1)

    portfolio_rev = portfolio["portfolio_monthly_revenue_eur"]
    if COST_MODEL == "ai_solo":
        if capex_total <= 400 and (net_12m > 0 or portfolio_rev > 200):
            verdict = "viable"
        elif capex_total <= 800 and treasury_ytd > -5000:
            verdict = "tight"
        elif net_12m > capex_total * 2:
            verdict = "viable"
        else:
            verdict = "tight" if capex_total < portfolio_rev * 2 else "no_go"
    else:
        if capex_total <= treasury_ytd * 0.15 and (break_even_months or 99) <= 18:
            verdict = "viable"
        elif capex_total <= treasury_ytd * 0.35:
            verdict = "tight"
        else:
            verdict = "no_go"

    assumptions = [
        f"Modèle de coût : {cost_model_label}",
        f"Effort {effort or 'M'} = {weeks} semaines pipeline agents",
        f"CAPEX agents IA : ~{capex_parts.get('capex_llm_agents_eur', capex_parts.get('capex_dev_eur', 0)):.0f} EUR (tokens OpenRouter, pas salaire dev)",
        f"Grille tarifaire : {pricing.get('price_range_eur', {}).get('min', '?')}–{pricing.get('price_range_eur', {}).get('max', '?')} EUR ({pricing.get('source', 'default')})",
        f"ARPU médian blendé : ~{arpu:.0f} EUR/mois",
        f"Abonnés payants médian : M3={subs.get('m3', '?')} · M6={subs.get('m6', '?')} · M12={subs.get('m12', '?')} (acquisition organique solo)",
        f"OPEX existant ALNUA (récurrent Hub) : ~{opex_existing:.0f} EUR/mois",
        f"OPEX incrémental nouveau projet : ~{opex_incremental:.0f} EUR/mois",
        f"Revenus portfolio actuel ({portfolio['active_apps_count']} apps) : ~{portfolio_rev:.0f} EUR/mois",
        f"Trésorerie YTD Hub : {treasury_ytd:.0f} EUR",
    ]
    if constraint:
        assumptions.append(f"Contrainte : {constraint}")

    return {
        **capex_parts,
        "finance_version": FINANCE_VERSION,
        "cost_model": COST_MODEL,
        "opex_monthly_eur": opex_monthly,
        "opex_incremental_eur": opex_incremental,
        "opex_existing_alnua_eur": opex_existing,
        "llm_monthly_eur": llm_share,
        "dev_weeks": weeks,
        "dev_hours": weeks * 8,
        "revenue_hypothesis": rev,
        "net_impact_6m_eur": net_6m,
        "net_impact_12m_eur": net_12m,
        "break_even_months": break_even_months,
        "runway_impact_months": runway_impact,
        "treasury_ytd_eur": treasury_ytd,
        "monthly_balance_eur": monthly_balance,
        "portfolio_monthly_revenue_eur": portfolio_rev,
        "portfolio_apps_count": portfolio["active_apps_count"],
        "portfolio_app_names": portfolio["active_app_names"],
        "funding_options": funding_options(verdict, treasury_ytd, capex_total, portfolio_rev),
        "verdict_finance": verdict,
        "assumptions": assumptions,
        "reasoning": reasoning_text(
            title,
            verdict,
            capex_total,
            opex_incremental,
            rev,
            portfolio_rev,
            COST_MODEL,
            net_12m,
        ),
    }


def funding_options(
    verdict: str, treasury: float, capex: float, portfolio_rev: float
) -> list[str]:
    options = []
    if portfolio_rev > 0:
        options.append(
            f"Réinvestir les revenus apps existants (~{portfolio_rev:.0f} EUR/mois)"
        )
    if capex < 300:
        options.append("Autofinancement OpenRouter — coût agents IA négligeable vs revenus actuels")
    elif treasury >= capex:
        options.append("Autofinancement depuis trésorerie Hub")
    options.append("BPI French Tech / subventions innovation")
    if verdict == "tight":
        options.append("Réduire le scope MVP (contrainte -30% coûts)")
    return options


def reasoning_text(
    title: str,
    verdict: str,
    capex: float,
    opex_incr: float,
    rev: dict[str, Any],
    portfolio_rev: float,
    cost_model: str,
    net_12m: float,
) -> str:
    labels = {"viable": "viable", "tight": "serré mais faisable", "no_go": "trop risqué"}
    model = "agents IA" if cost_model == "ai_solo" else "dev humain"
    pm = rev.get("pricing_model") or {}
    subs = rev.get("paying_subscribers") or {}
    arpu = rev.get("blended_arpu_eur") or 0
    return (
        f"« {title} » — modèle {model}. "
        f"Investissement initial ~{capex:.0f} EUR. "
        f"Pricing {pm.get('price_range_eur', {}).get('min', '?')}–{pm.get('price_range_eur', {}).get('max', '?')} EUR/mois "
        f"(ARPU médian ~{arpu:.0f} EUR). "
        f"Abonnés payants visés : {subs.get('m3', '?')} à M3, {subs.get('m6', '?')} à M6, {subs.get('m12', '?')} à M12. "
        f"MRR médian : ~{rev.get('m3_monthly_run_rate_eur', 0):.0f} EUR/mois à M3, "
        f"~{rev['m6_monthly_run_rate_eur']:.0f} à M6, "
        f"~{rev['m12_monthly_run_rate_eur']:.0f} à M12 "
        f"(cumul 12 mois ~{rev['cumulative_12m_eur']:.0f} EUR, impact net ~{net_12m:.0f} EUR). "
        f"Verdict : {labels.get(verdict, verdict)}."
    )
