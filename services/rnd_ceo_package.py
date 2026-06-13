"""CEO package templates and dispatch matrix (phase 6)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from services.rnd_schemas import DOMAIN_TO_BRANCH, RndDossierOut

# Branch-specific section blocks for the CEO dossier
BRANCH_BLOCKS: dict[str, list[dict[str, str]]] = {
    "app": [
        {"key": "executive_summary", "title": "Executive summary (1 page)"},
        {"key": "business_pricing", "title": "Business model & pricing"},
        {"key": "product_market_risks", "title": "Risques produit / marché"},
        {"key": "ai_rnd_costs", "title": "R&D transverse IA (coûts agents, stack)"},
    ],
    "robotics": [
        {"key": "three_pillars", "title": "3 piliers : hardware / app / IA"},
        {"key": "regulation", "title": "Réglementation (RGPD, CE, certifications)"},
        {"key": "manufacturing_bom", "title": "Industrialisation & BOM"},
        {"key": "cogs_opex", "title": "COGS / OPEX détaillés"},
        {"key": "tech_supply_risks", "title": "Matrice risques technique + supply chain"},
    ],
    "gaming": [
        {"key": "perf_targets", "title": "Perfs cibles (FPS, plateformes)"},
        {"key": "network_multiplayer", "title": "Réseau / multijoueur"},
        {"key": "art_direction", "title": "Direction artistique (lore, identité visuelle)"},
    ],
    "other": [
        {"key": "executive_summary", "title": "Executive summary"},
        {"key": "business_pricing", "title": "Business model & pricing"},
        {"key": "product_market_risks", "title": "Risques produit / marché"},
    ],
}

DISPATCH_POLES: dict[str, list[dict[str, Any]]] = {
    "app": [
        {
            "pole": "Product / PM",
            "agent_id": "pm_agent",
            "deliverables": ["Backlog MVP priorisé", "Critères d'acceptation v1"],
            "priority": "high",
            "phase": "conception",
        },
        {
            "pole": "Spec & Architecture",
            "agent_id": "spec_agent",
            "deliverables": ["Spec technique", "Schéma données & API"],
            "priority": "high",
            "phase": "conception",
        },
        {
            "pole": "Dev App",
            "agent_id": "dev_app",
            "deliverables": ["Repo initial", "MVP sprint 1"],
            "priority": "high",
            "phase": "build",
        },
        {
            "pole": "Marketing & Content",
            "agent_id": "marketing_agent",
            "deliverables": ["Positionnement GTM", "Calendrier social (post-validation CEO)"],
            "priority": "medium",
            "phase": "launch_prep",
        },
        {
            "pole": "Comptabilité",
            "agent_id": "accountant_agent",
            "deliverables": ["Suivi CAPEX/OPEX", "Hypothèses revenus M3/M12"],
            "priority": "medium",
            "phase": "finance",
        },
    ],
    "robotics": [
        {
            "pole": "Hardware",
            "agent_id": "hardware_agent",
            "deliverables": ["BOM validée", "Plan industrialisation", "Certifications cibles"],
            "priority": "critical",
            "phase": "hardware",
        },
        {
            "pole": "Embedded / Firmware",
            "agent_id": "embedded_dev",
            "deliverables": ["Architecture firmware", "Protocoles capteurs"],
            "priority": "high",
            "phase": "firmware",
        },
        {
            "pole": "Dev App (companion)",
            "agent_id": "dev_app",
            "deliverables": ["App mobile/web companion", "Dashboard IoT"],
            "priority": "high",
            "phase": "app",
        },
        {
            "pole": "PM & Supply chain",
            "agent_id": "pm_agent",
            "deliverables": ["Roadmap 3 piliers", "Fournisseurs short-list"],
            "priority": "high",
            "phase": "conception",
        },
    ],
    "gaming": [
        {
            "pole": "Game Director",
            "agent_id": "game_director",
            "deliverables": ["GDD core loop", "Pillars gameplay", "Roadmap contenu"],
            "priority": "critical",
            "phase": "design",
        },
        {
            "pole": "Dev Gaming",
            "agent_id": "dev_gaming",
            "deliverables": ["Prototype vertical slice", "Perfs cibles plateformes"],
            "priority": "high",
            "phase": "prototype",
        },
        {
            "pole": "Content / Lore",
            "agent_id": "content_agent",
            "deliverables": ["Bible narrative", "Identité visuelle moodboard"],
            "priority": "medium",
            "phase": "art",
        },
        {
            "pole": "Marketing",
            "agent_id": "marketing_agent",
            "deliverables": ["Wishlist strategy", "Teasers post-launch CEO"],
            "priority": "medium",
            "phase": "launch_prep",
        },
    ],
    "other": [
        {
            "pole": "PM",
            "agent_id": "pm_agent",
            "deliverables": ["Plan conception", "Backlog initial"],
            "priority": "high",
            "phase": "conception",
        },
        {
            "pole": "Dev",
            "agent_id": "dev_app",
            "deliverables": ["Spike technique", "MVP scope"],
            "priority": "high",
            "phase": "build",
        },
    ],
}


def resolve_branch(dossier: RndDossierOut) -> str:
    branch = (dossier.branch or "").strip().lower()
    if branch in BRANCH_BLOCKS:
        return branch
    domain = (dossier.domain or "autre").lower()
    mapped = DOMAIN_TO_BRANCH.get(domain, "other")
    return mapped if mapped in BRANCH_BLOCKS else "other"


def _section_map(dossier: RndDossierOut) -> dict[str, str]:
    return {s.section_key: (s.content_md or "").strip() for s in dossier.sections}


def _excerpt(text: str, max_len: int = 500) -> str:
    if not text or text.startswith("_") or len(text) < 20:
        return "_Section à compléter._"
    para = text.split("\n\n")[0].strip()
    if len(para) > max_len:
        return para[: max_len - 3].rstrip() + "…"
    return para


def _pricing_table(dossier: RndDossierOut) -> str:
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
    m12 = rev.get("m12_monthly_run_rate_eur")
    if m12:
        lines.append(f"\n- Run-rate M12 : **{m12} €/mois**")
    return "\n".join(lines)


def _finance_summary(dossier: RndDossierOut) -> str:
    fj = dossier.finance_json or {}
    if not fj:
        return "_Business case non généré._"
    return (
        f"- CAPEX total : **{fj.get('capex_eur', 0)} €** "
        f"(dev {fj.get('capex_dev_eur', 0)} €, agents LLM {fj.get('capex_llm_agents_eur', 0)} €)\n"
        f"- OPEX mensuel incrémental : **{fj.get('opex_incremental_eur') or fj.get('opex_monthly_eur', 0)} €**\n"
        f"- Verdict finance : **{fj.get('verdict_finance', '—')}**\n"
        f"- Impact runway : {fj.get('runway_impact_months', '—')} mois\n"
        f"- Break-even : {fj.get('break_even_months') or 'N/A'} mois"
    )


def _build_block_content(key: str, dossier: RndDossierOut, sections: dict[str, str]) -> str:
    branch = resolve_branch(dossier)

    if key == "executive_summary":
        parts = [
            _excerpt(sections.get("problem", ""), 350),
            "",
            "**Solution :** " + _excerpt(sections.get("solution", ""), 280),
            "",
            "**Recommandation comité :** " + _excerpt(sections.get("decision", ""), 200),
        ]
        return "\n".join(parts)

    if key == "business_pricing":
        return _pricing_table(dossier) + "\n\n" + _excerpt(sections.get("business_case", ""), 400)

    if key == "product_market_risks":
        return _excerpt(sections.get("risks", ""), 600) + "\n\n" + _excerpt(sections.get("market", ""), 300)

    if key == "ai_rnd_costs":
        fj = dossier.finance_json or {}
        stack = _excerpt(sections.get("feasibility", ""), 350)
        return (
            f"{stack}\n\n"
            f"**Coûts pipeline agents IA :**\n"
            f"- Enrichissement dossier : {fj.get('capex_dossier_llm_eur', '—')} €\n"
            f"- Tokens agents / mois : {fj.get('llm_monthly_eur', '—')} €\n"
            f"- Modèle coût : {fj.get('cost_model', 'ai_solo')}"
        )

    if key == "three_pillars":
        return (
            "### Hardware\n" + _excerpt(sections.get("manufacturing", ""), 350)
            + "\n\n### App / Cloud\n" + _excerpt(sections.get("solution", ""), 350)
            + "\n\n### IA / Automatisation\n" + _excerpt(sections.get("feasibility", ""), 350)
        )

    if key == "regulation":
        risks = sections.get("risks", "")
        extra = (
            "- **RGPD** : minimisation données capteurs, consentement, DPA fournisseurs cloud.\n"
            "- **CE / RED** : conformité radio si connecté ; marquage CE avant vente UE.\n"
            "- **Certifications** : selon usage (domestique vs pro)."
        )
        return _excerpt(risks, 400) + "\n\n" + extra

    if key == "manufacturing_bom":
        return _excerpt(sections.get("manufacturing", ""), 700)

    if key == "cogs_opex":
        return _finance_summary(dossier) + "\n\n" + _excerpt(sections.get("manufacturing", ""), 300)

    if key == "tech_supply_risks":
        return _excerpt(sections.get("risks", ""), 500) + "\n\n" + _excerpt(sections.get("feasibility", ""), 300)

    if key == "perf_targets":
        mvp = sections.get("mvp", "")
        feas = sections.get("feasibility", "")
        return (
            _excerpt(mvp, 400)
            + "\n\n**Cibles perf :** 60 FPS (PC/console), 30 FPS mobile min — à valider en prototype."
            + "\n\n" + _excerpt(feas, 250)
        )

    if key == "network_multiplayer":
        feas = sections.get("feasibility", "")
        if "multi" in feas.lower() or "réseau" in feas.lower() or "network" in feas.lower():
            return _excerpt(feas, 600)
        return (
            "_Multijoueur non explicite dans le dossier._\n\n"
            "Si applicable : latence < 100 ms, authoritative server ou P2P relay, "
            "anti-cheat basique, matchmaking async pour solo founder."
        )

    if key == "art_direction":
        lore = _excerpt(sections.get("lore", ""), 350)
        visual = _excerpt(sections.get("visual_identity", ""), 350)
        return f"### Univers\n{lore}\n\n### Identité visuelle\n{visual}"

    return _excerpt(sections.get(key, ""), 500)


def build_dispatch_matrix(dossier: RndDossierOut) -> list[dict[str, Any]]:
    branch = resolve_branch(dossier)
    base = DISPATCH_POLES.get(branch, DISPATCH_POLES["other"])
    matrix: list[dict[str, Any]] = []
    for row in base:
        matrix.append(
            {
                **row,
                "roadmap_title": f"[{dossier.title}] {row['deliverables'][0]}",
                "description": (
                    f"Dispatch post-validation CEO — {dossier.title}.\n"
                    f"Livrables : {', '.join(row['deliverables'])}.\n"
                    f"Pôle : {row['pole']} ({row['agent_id']})."
                ),
            }
        )
    # COO orchestration row — after CEO, not in committee room
    matrix.append(
        {
            "pole": "COO (orchestration)",
            "agent_id": "coo_agent",
            "deliverables": [
                "Plan d'exécution multi-pôles",
                "Suivi roadmap & arbitrages",
            ],
            "priority": "high",
            "phase": "orchestration",
            "roadmap_title": f"[{dossier.title}] Orchestration COO",
            "description": (
                f"Le COO prend le relais **après** validation CEO sur {dossier.title}. "
                "Coordonne les pôles, protège le temps d'Emilie, pas de présence en comité R&D."
            ),
        }
    )
    return matrix


def build_portfolio_summary(
    dossier: RndDossierOut,
    *,
    portfolio_rows: list[dict[str, Any]] | None = None,
) -> str:
    branch = resolve_branch(dossier)
    branch_label = {
        "app": "App / SaaS",
        "robotics": "Robotique / Hardware",
        "gaming": "Jeu / 3D",
        "other": "Transverse",
    }.get(branch, branch)
    lines = [
        f"**Branche ALNUA :** {branch_label}",
        f"**Statut dossier :** {dossier.status} · **CEO :** {dossier.ceo_status}",
        f"**Sections validées :** {dossier.sections_validated_count}/{dossier.sections_total_count}",
        "",
        "Ce dossier s'inscrit dans le pipeline portfolio : Idée → Comité → Package CEO → "
        "Validation → Dispatch COO → Conception → Fiche produit publique.",
    ]

    if portfolio_rows:
        lines.extend(["", "### Roadmap portfolio ALNUA", ""])
        lines.append("| Projet | Branche | Statut | CEO | Validé |")
        lines.append("|--------|---------|--------|-----|--------|")
        for row in portfolio_rows[:15]:
            title = str(row.get("title", "—"))[:36]
            dom = row.get("domain") or row.get("branch") or "—"
            st = row.get("status", "—")
            ceo = row.get("ceo_status", "—")
            val = f"{row.get('sections_validated_count', 0)}/{row.get('sections_total_count', 0)}"
            marker = "**→** " if str(row.get("id")) == str(dossier.id) else ""
            lines.append(f"| {marker}{title} | {dom} | {st} | {ceo} | {val} |")
        active = sum(
            1
            for r in portfolio_rows
            if r.get("status") in ("committee_active", "ready_for_ceo", "in_conception", "ceo_approved")
        )
        lines.append("")
        lines.append(
            f"*{len(portfolio_rows)} dossier(s) portfolio · {active} actif(s) en pipeline R&D→CEO.*"
        )

    return "\n".join(lines)


def build_ceo_package_md(
    dossier: RndDossierOut,
    *,
    committee_report_md: str | None = None,
    portfolio_rows: list[dict[str, Any]] | None = None,
) -> str:
    branch = resolve_branch(dossier)
    sections = _section_map(dossier)
    blocks = BRANCH_BLOCKS.get(branch, BRANCH_BLOCKS["other"])
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    lines = [
        f"# Dossier CEO — {dossier.title}",
        f"*{dossier.tagline or dossier.domain} · {branch.upper()} · généré {now}*",
        "",
        "---",
        "",
        "## Portfolio & contexte",
        "",
        build_portfolio_summary(dossier, portfolio_rows=portfolio_rows),
        "",
    ]

    if committee_report_md and len(committee_report_md.strip()) > 40:
        lines.extend(
            [
                "---",
                "",
                "## Compte-rendu comité R&D",
                "",
                committee_report_md.strip(),
                "",
            ]
        )

    for block in blocks:
        content = _build_block_content(block["key"], dossier, sections)
        lines.extend(["---", "", f"## {block['title']}", "", content, ""])

    lines.extend(
        [
            "---",
            "",
            "## Finance (synthèse exécutive)",
            "",
            _finance_summary(dossier),
            "",
            "---",
            "",
            "## Matrice dispatch (post-validation CEO)",
            "",
            "| Pôle | Agent | Livrables | Priorité |",
            "|------|-------|-----------|----------|",
        ]
    )

    for row in build_dispatch_matrix(dossier):
        deliverables = "; ".join(row["deliverables"][:2])
        lines.append(
            f"| {row['pole']} | {row['agent_id']} | {deliverables} | {row['priority']} |"
        )

    lines.extend(
        [
            "",
            "---",
            "",
            "*Package CEO ALNUA Hub — phase 6. Validation Emilie requise avant dispatch COO.*",
        ]
    )
    return "\n".join(lines)


def build_ceo_package_json(
    dossier: RndDossierOut,
    *,
    committee_report_md: str | None = None,
    markdown: str | None = None,
    portfolio_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    branch = resolve_branch(dossier)
    sections = _section_map(dossier)
    blocks = BRANCH_BLOCKS.get(branch, BRANCH_BLOCKS["other"])
    block_contents = {
        b["key"]: {"title": b["title"], "content_md": _build_block_content(b["key"], dossier, sections)}
        for b in blocks
    }
    md = markdown or build_ceo_package_md(
        dossier,
        committee_report_md=committee_report_md,
        portfolio_rows=portfolio_rows,
    )
    return {
        "version": 1,
        "branch": branch,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dossier_id": dossier.id,
        "dossier_slug": dossier.slug,
        "title": dossier.title,
        "markdown": md,
        "blocks": block_contents,
        "finance_summary": _finance_summary(dossier),
        "dispatch_matrix": build_dispatch_matrix(dossier),
        "portfolio_summary": build_portfolio_summary(dossier, portfolio_rows=portfolio_rows),
        "portfolio_rows": portfolio_rows or [],
        "committee_report_md": committee_report_md,
        "recommendation": _extract_go_recommendation(sections.get("decision", "")),
    }


def _extract_go_recommendation(decision_md: str) -> str:
    text = (decision_md or "").upper()
    for verdict in ("GO", "MAYBE", "NO"):
        if verdict in text:
            return verdict
    return "MAYBE"
