"""CEO package shared helpers — branch resolution, finance excerpts, recommendations."""

from __future__ import annotations

from services.rnd_ceo_package_constants import BRANCH_BLOCKS
from services.rnd_schemas import DOMAIN_TO_BRANCH, RndDossierOut


def resolve_branch(dossier: RndDossierOut) -> str:
    branch = (dossier.branch or "").strip().lower()
    if branch in BRANCH_BLOCKS:
        return branch
    domain = (dossier.domain or "autre").lower()
    mapped = DOMAIN_TO_BRANCH.get(domain, "other")
    return mapped if mapped in BRANCH_BLOCKS else "other"


def section_map(dossier: RndDossierOut) -> dict[str, str]:
    return {s.section_key: (s.content_md or "").strip() for s in dossier.sections}


def excerpt(text: str, max_len: int = 500) -> str:
    if not text or text.startswith("_") or len(text) < 20:
        return "_Section à compléter._"
    para = text.split("\n\n")[0].strip()
    if len(para) > max_len:
        return para[: max_len - 3].rstrip() + "…"
    return para


def pricing_table(dossier: RndDossierOut) -> str:
    fj = dossier.finance_json or {}
    rev = fj.get("revenue_hypothesis") or {}
    pm = rev.get("pricing_model") or {}
    tiers = pm.get("tiers") or []
    lines = [
        f"- Modèle : {pm.get('model_type', 'subscription')}",
        f"- ARPU blended : {pm.get('blended_arpu_eur') or rev.get('blended_arpu_eur', '—')} €",
    ]
    if tiers:
        lines.append("")
        lines.append("| Tier | Prix | Mix |")
        lines.append("|------|------|-----|")
        for t in tiers[:6]:
            lines.append(
                f"| {t.get('name', '?')} | {t.get('price_eur', '—')} € | "
                f"{int((t.get('mix_pct') or 0) * 100)}% |"
            )
    m6 = rev.get("m6_monthly_run_rate_eur") or rev.get("m6_mrr_eur")
    m12 = rev.get("m12_monthly_run_rate_eur") or rev.get("m12_mrr_eur")
    if m6:
        lines.append(f"\n- **Revenu estimé M6 :** {m6} €/mois")
    if m12:
        lines.append(f"- **Revenu estimé M12 :** {m12} €/mois")
    return "\n".join(lines)


def finance_summary(dossier: RndDossierOut) -> str:
    fj = dossier.finance_json or {}
    if not fj:
        return "_Business case non généré._"
    cost_model = fj.get("cost_model", "ai_solo")
    model_label = "agents IA (OpenRouter)" if cost_model == "ai_solo" else "dev humain"
    return (
        f"- Modèle coût : **{model_label}**\n"
        f"- CAPEX total : **{fj.get('capex_eur', 0)} €** "
        f"(dev {fj.get('capex_dev_eur', 0)} €, agents LLM {fj.get('capex_llm_agents_eur', 0)} €)\n"
        f"- OPEX mensuel incrémental : **{fj.get('opex_incremental_eur') or fj.get('opex_monthly_eur', 0)} €**\n"
        f"- Verdict finance : **{fj.get('verdict_finance', '—')}**\n"
        f"- Impact runway : {fj.get('runway_impact_months', '—')} mois\n"
        f"- Break-even : {fj.get('break_even_months') or 'N/A'} mois"
    )


def revenue_projection(dossier: RndDossierOut) -> str:
    fj = dossier.finance_json or {}
    rev = fj.get("revenue_hypothesis") or {}
    sections = section_map(dossier)
    if not rev:
        return "_Hypothèses revenus non renseignées — compléter la section business case._"
    lines = [
        "### COGS & investissement initial",
        "",
        finance_summary(dossier),
        "",
        "### OPEX récurrents",
        "",
        f"- Hébergement / infra : {fj.get('opex_hosting_eur', fj.get('opex_monthly_eur', '—'))} €/mois",
        f"- Tokens agents IA : {fj.get('llm_monthly_eur', '—')} €/mois",
        "",
        "### Stratégie de vente & pricing",
        "",
        pricing_table(dossier),
        "",
        "### Projection impact (si le produit fonctionne)",
        "",
        excerpt(
            (
                rev.get("narrative")
                if isinstance(rev.get("narrative"), str)
                else (fj.get("revenue_narrative_md") or "")
            )
            or sections.get("business_case", ""),
            400,
        ),
    ]
    return "\n".join(lines)


def extract_go_recommendation(decision_md: str) -> str:
    text = (decision_md or "").upper()
    for verdict in ("GO", "MAYBE", "NO"):
        if verdict in text:
            return verdict
    return "MAYBE"
