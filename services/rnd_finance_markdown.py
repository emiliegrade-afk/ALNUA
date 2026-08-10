"""Finance estimate — markdown business case rendering."""
from __future__ import annotations

from typing import Any


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
        f"- Run-rate **M12** (médian) : **~{rev['m12_monthly_run_rate_eur']:.0f} EUR/mois**",
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
