"""Finance estimates for R&D dossiers — solo founder + AI agents + real ALNUA data."""

from __future__ import annotations

import logging
import os
from datetime import date
from typing import Any

from database.supabase_client import SupabaseClient, get_supabase
from services.rnd_pricing_model import revenue_from_pricing
from services.finance_agent import (
    build_dashboard,
    compute_totals,
    fetch_recurring_expenses,
    fetch_transactions,
)

logger = logging.getLogger(__name__)

# Effort → agent work duration (weeks of solo+AI pipeline, not human payroll)
EFFORT_WEEKS: dict[str, int] = {
    "S": 2,
    "M": 4,
    "L": 10,
    "XL": 20,
}

DOMAIN_MULTIPLIER: dict[str, float] = {
    "app": 1.0,
    "saas": 1.15,
    "ia": 1.1,
    "jeu": 1.3,
    "game": 1.3,
    "gaming": 1.3,
    "hardware": 1.6,
    "robotique": 1.6,
    "robotics": 1.6,
    "autre": 1.0,
}

# Revenue ramp: how fast a new product can reach fraction of portfolio per domain
DOMAIN_REVENUE_POTENTIAL: dict[str, float] = {
    "app": 1.2,
    "saas": 1.5,
    "ia": 1.3,
    "jeu": 0.85,
    "game": 0.85,
    "gaming": 0.85,
    "hardware": 0.55,
    "robotique": 0.55,
    "robotics": 0.55,
    "autre": 1.0,
}

EFFORT_REVENUE_SPEED: dict[str, float] = {
    "S": 1.25,
    "M": 1.0,
    "L": 0.75,
    "XL": 0.55,
}

COST_MODEL = os.getenv("RND_COST_MODEL", "ai_solo").lower()
FINANCE_VERSION = 3

# AI solo defaults (OpenRouter + outillage — pas de salaire dev)
LLM_EUR_PER_AGENT_WEEK = float(os.getenv("RND_LLM_EUR_PER_AGENT_WEEK", "14"))
DOSSIER_ENRICH_EUR = float(os.getenv("RND_DOSSIER_ENRICH_EUR", "8"))
MARKETING_LAUNCH_EUR = float(os.getenv("RND_MARKETING_LAUNCH_EUR", "80"))
PROJECT_HOSTING_MONTHLY_EUR = float(os.getenv("RND_PROJECT_HOSTING_MONTHLY_EUR", "12"))

# Legacy human-dev model (only if RND_COST_MODEL=human_dev)
HOURLY_RATE_EUR = float(os.getenv("RND_DEV_HOURLY_RATE_EUR", "50"))
HOURS_PER_WEEK = int(os.getenv("RND_DEV_HOURS_PER_WEEK", "20"))
BASE_OPEX_MONTHLY = float(os.getenv("RND_BASE_OPEX_MONTHLY_EUR", "45"))
LEGACY_LLM_MONTHLY_EUR = float(os.getenv("RND_LLM_MONTHLY_EUR", "30"))


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
    out = {**finance, "revenue_hypothesis": rev}
    return out


def _effort_weeks(effort: str | None) -> int:
    return EFFORT_WEEKS.get((effort or "M").upper(), EFFORT_WEEKS["M"])


def _domain_multiplier(domain: str | None) -> float:
    return DOMAIN_MULTIPLIER.get((domain or "autre").lower(), 1.0)


def _domain_revenue_potential(domain: str | None) -> float:
    return DOMAIN_REVENUE_POTENTIAL.get((domain or "autre").lower(), 1.0)


def _effort_revenue_speed(effort: str | None) -> float:
    return EFFORT_REVENUE_SPEED.get((effort or "M").upper(), 1.0)


def _apply_constraint(weeks: int, mult: float, constraint: str | None) -> tuple[int, float]:
    if not constraint or "reduce" not in constraint.lower():
        return weeks, mult
    if "50" in constraint:
        return max(1, int(weeks * 0.5)), mult * 0.7
    if "30" in constraint:
        return max(1, int(weeks * 0.7)), mult * 0.85
    return weeks, mult


def _portfolio_snapshot(db: SupabaseClient) -> dict[str, Any]:
    """Real ALNUA numbers: apps revenue, recurring costs, project count."""
    try:
        projects = db.select("projects", order_by="name")
    except Exception:
        projects = []

    active_apps = [p for p in projects if p.get("branch") in ("app", "gaming", "robotics")]

    # Last 6 months app revenue from transactions
    today = date.today()
    months_income: list[float] = []
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
        months_income.append(month_income)
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


def _capex_ai_solo(weeks: int, mult: float, constraint: str | None) -> dict[str, float]:
    llm_dev = round(weeks * LLM_EUR_PER_AGENT_WEEK * mult, 2)
    llm_dossier = round(DOSSIER_ENRICH_EUR * (0.5 if constraint else 1.0), 2)
    marketing = round(MARKETING_LAUNCH_EUR * (0.5 if constraint else 1.0), 2)
    total = round(llm_dev + llm_dossier + marketing, 2)
    return {
        "capex_eur": total,
        "capex_llm_agents_eur": llm_dev,
        "capex_dossier_llm_eur": llm_dossier,
        "capex_marketing_eur": marketing,
        "capex_dev_eur": llm_dev,  # backward compat for charts
    }


def _capex_human_dev(weeks: int, mult: float, constraint: str | None) -> dict[str, float]:
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


def _revenue_projection(
    *,
    portfolio_monthly: float,
    per_app_monthly: float,
    active_apps: int,
    domain: str | None,
    effort: str | None,
    title: str = "",
    description: str = "",
    section_text: str = "",
    constraint: str | None = None,
) -> dict[str, Any]:
    """Revenue from product pricing tiers × paying subscriber ramp."""
    return revenue_from_pricing(
        domain=domain,
        effort=effort,
        title=title,
        description=description,
        section_text=section_text,
        constraint=constraint,
        portfolio_monthly=portfolio_monthly,
        per_app_monthly=per_app_monthly,
        active_apps=active_apps,
    )


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
    weeks = _effort_weeks(effort)
    mult = _domain_multiplier(domain)
    weeks, mult = _apply_constraint(weeks, mult, constraint)

    portfolio = _portfolio_snapshot(db)

    if COST_MODEL == "human_dev":
        capex_parts = _capex_human_dev(weeks, mult, constraint)
        opex_incremental = round((BASE_OPEX_MONTHLY + LEGACY_LLM_MONTHLY_EUR) * mult, 2)
        cost_model_label = "freelance/humain (legacy)"
    else:
        capex_parts = _capex_ai_solo(weeks, mult, constraint)
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

    rev = _revenue_projection(
        portfolio_monthly=portfolio["portfolio_monthly_revenue_eur"],
        per_app_monthly=portfolio["portfolio_per_app_monthly_eur"],
        active_apps=portfolio["active_apps_count"],
        domain=domain,
        effort=effort,
        title=title,
        description=description,
        section_text=section_text,
        constraint=constraint,
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

    # Verdict: solo+AI — CAPEX faible + portefeuille existant = souvent viable
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
        "dev_hours": weeks * 8,  # solo focused blocks, not 20h/week payroll
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
        "funding_options": _funding_options(verdict, treasury_ytd, capex_total, portfolio_rev),
        "verdict_finance": verdict,
        "assumptions": assumptions,
        "reasoning": _reasoning_text(
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


def _funding_options(
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


def _reasoning_text(
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


def finance_json_to_markdown(finance: dict[str, Any]) -> str:
    rev = finance.get("revenue_hypothesis") or {}
    model = finance.get("cost_model", "ai_solo")
    is_ai = model == "ai_solo"

    lines = [
        "## Business case",
        "",
        f"**Verdict finance :** {finance.get('verdict_finance', '?').upper()}",
        f"**Modèle :** {'Solo + agents IA (OpenRouter)' if is_ai else 'Dev humain (legacy)'}",
        "",
        "### Ton contexte ALNUA (données réelles Hub)",
        f"- Apps actives : **{finance.get('portfolio_apps_count', 0)}**",
        f"- Revenus portfolio : **~{finance.get('portfolio_monthly_revenue_eur', 0):.0f} EUR/mois**",
        f"- OPEX récurrent existant : **~{finance.get('opex_existing_alnua_eur', 0):.0f} EUR/mois**",
        f"- Trésorerie YTD : **{finance.get('treasury_ytd_eur', 0):.0f} EUR**",
        "",
        "### Investissement initial (CAPEX)",
    ]
    if is_ai:
        lines.extend([
            f"- Agents IA (dev + itérations) : **{finance.get('capex_llm_agents_eur', 0):.0f} EUR**",
            f"- Enrichissement dossier LLM : **{finance.get('capex_dossier_llm_eur', 0):.0f} EUR**",
        ])
    else:
        lines.append(
            f"- Développement humain : **{finance.get('capex_dev_eur', 0):.0f} EUR**"
        )
    lines.extend([
        f"- Marketing lancement : **{finance.get('capex_marketing_eur', 0):.0f} EUR**",
        f"- **Total CAPEX : {finance.get('capex_eur', 0):.0f} EUR**",
        "",
        "### Coûts récurrents (OPEX)",
        f"- ALNUA existant (infra, outils) : ~{finance.get('opex_existing_alnua_eur', 0):.0f} EUR/mois",
        f"- **Nouveau projet (incrémental) : ~{finance.get('opex_incremental_eur', 0):.0f} EUR/mois**",
        "",
        "### Revenus estimés si le produit fonctionne",
    ])
    pricing = rev.get("pricing_model") or {}
    tiers = pricing.get("tiers") or []
    subs = rev.get("paying_subscribers") or {}
    if tiers:
        lines.extend([
            "",
            "### Grille tarifaire (hypothèse produit)",
            f"- Fourchette : **{pricing.get('price_range_eur', {}).get('min', '?')} – {pricing.get('price_range_eur', {}).get('max', '?')} EUR**",
            f"- ARPU médian blendé : **~{rev.get('blended_arpu_eur', 0):.0f} EUR/mois**",
            f"- Source : {pricing.get('source', 'default')}",
            "",
        ])
        for tier in tiers:
            lines.append(
                f"  - **{tier.get('name')}** : {tier.get('price_eur')} EUR "
                f"({int(float(tier.get('mix_pct', 0)) * 100)} % du mix)"
            )
        lines.extend([
            "",
            "### Abonnés payants (scénario médian, acquisition organique)",
            f"- M3 : **{subs.get('m3', '?')} clients**",
            f"- M6 : **{subs.get('m6', '?')} clients**",
            f"- M12 : **{subs.get('m12', '?')} clients**",
            "",
        ])
    lines.extend([
        f"- Run-rate **M3** (médian) : **~{rev.get('m3_monthly_run_rate_eur', 0):.0f} EUR/mois**",
        f"- Run-rate **M6** (médian) : **~{rev.get('m6_monthly_run_rate_eur', 0):.0f} EUR/mois**",
        f"- Run-rate **M12** (médian) : **~{rev.get('m12_monthly_run_rate_eur', 0):.0f} EUR/mois**",
        f"- Cumul sur 6 mois : **~{rev.get('cumulative_6m_eur', 0):.0f} EUR**",
        f"- Cumul sur 12 mois : **~{rev.get('cumulative_12m_eur', 0):.0f} EUR**",
        f"- Scénario prudent M12 : ~{rev.get('conservative_m12_monthly_eur', 0):.0f} EUR/mois",
        f"- Scénario optimiste M12 : ~{rev.get('optimistic_m12_monthly_eur', 0):.0f} EUR/mois",
        "",
        "### Impact net (nouveau projet seul)",
        f"- Net 6 mois : **{finance.get('net_impact_6m_eur', 0):.0f} EUR**",
        f"- Net 12 mois : **{finance.get('net_impact_12m_eur', 0):.0f} EUR**",
        f"- Break-even : **{finance.get('break_even_months') or 'N/A'} mois**",
        "",
        "### Options",
    ])
    for opt in finance.get("funding_options") or []:
        lines.append(f"- {opt}")
    lines.extend(["", "### Hypothèses", ""])
    for a in finance.get("assumptions") or []:
        lines.append(f"- {a}")
    lines.extend(["", finance.get("reasoning", "")])
    return "\n".join(lines)
