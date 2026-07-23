"""CEO package templates and dispatch matrix (phase 6).

Template structure from Emilie's validation dossier spec (2026-06-12):
1. Executive Summary
2. Bilan technique (branch-specific)
3. Réglementation / sécurité / RGPD
4. Industrialisation ou go-to-market
5. Business model multicouche (COGS, OPEX, revenus M6/M12)
6. Matrice des risques
7. R&D transverse IA (mutualisation)
8. Master summary portfolio
9. Matrice dispatch — qui fait quoi
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from services.rnd_schemas import DOMAIN_TO_BRANCH, RndDossierOut

BRANCH_BLOCKS: dict[str, list[dict[str, str]]] = {
    "app": [
        {"key": "executive_summary", "title": "1. Executive Summary"},
        {"key": "technical_assessment", "title": "2. Bilan technique — produit & stack"},
        {"key": "compliance_security", "title": "3. Sécurité, conformité & RGPD"},
        {"key": "go_to_market", "title": "4. Go-to-market & acquisition"},
        {"key": "business_model", "title": "5. Business model multicouche"},
        {"key": "risk_matrix", "title": "6. Matrice des risques spécifiques"},
    ],
    "robotics": [
        {"key": "executive_summary", "title": "1. Executive Summary (Full Stack)"},
        {"key": "technical_assessment", "title": "2. Bilan technique — PoC hybride"},
        {"key": "compliance_security", "title": "3. Réglementation, sécurité & RGPD"},
        {"key": "industrialization", "title": "4. Plan d'industrialisation (supply chain)"},
        {"key": "business_model", "title": "5. Business model multicouche"},
        {"key": "risk_matrix", "title": "6. Matrice des risques spécifiques"},
    ],
    "gaming": [
        {"key": "executive_summary", "title": "1. Executive Summary"},
        {"key": "technical_assessment", "title": "2. Bilan technique — plateforme 3D"},
        {"key": "compliance_security", "title": "3. Conformité & sécurité"},
        {"key": "production_plan", "title": "4. Plan de production & livraison"},
        {"key": "business_model", "title": "5. Business model"},
        {"key": "risk_matrix", "title": "6. Matrice des risques spécifiques"},
    ],
    "hub": [
        {"key": "executive_summary", "title": "1. Executive Summary — amélioration Hub ALNUA"},
        {"key": "technical_assessment", "title": "2. Bilan technique — repo ALNUA_HUB"},
        {"key": "compliance_security", "title": "3. Stabilité ops & sécurité"},
        {"key": "go_to_market", "title": "4. Rollout interne & déploiement"},
        {"key": "business_model", "title": "5. ROI interne (temps gagné / coûts IA)"},
        {"key": "risk_matrix", "title": "6. Risques régression plateforme"},
    ],
    "other": [
        {"key": "executive_summary", "title": "1. Executive Summary"},
        {"key": "technical_assessment", "title": "2. Bilan technique"},
        {"key": "compliance_security", "title": "3. Sécurité & conformité"},
        {"key": "go_to_market", "title": "4. Plan de lancement"},
        {"key": "business_model", "title": "5. Business model multicouche"},
        {"key": "risk_matrix", "title": "6. Matrice des risques"},
    ],
}

CEO_PACKAGE_OUTLINE = """
Structure OBLIGATOIRE du dossier CEO (ne pas réordonner les ##) :
1. Executive Summary — promesse produit, statut (3 piliers si hardware), enveloppe budgétaire
2. Bilan technique — découpage Hardware / Software / IA (robotique) ou Produit / Stack / IA (app)
3. Réglementation, sécurité, RGPD
4. Industrialisation supply chain OU go-to-market OU plan production
5. Business model — COGS, OPEX récurrents, pricing, revenus estimés M6/M12
6. Matrice risques — risque → impact → mitigation
7. R&D transverse IA — mutualisation agents/modèles entre projets ALNUA
8. Master summary — position portfolio
9. Matrice dispatch — pôle, agent, livrables, priorité (qui reçoit quoi après validation CEO)
10. Product Engineering Spec — écrans, user stories, contrat API, tables Supabase, tests E2E, task breakdown JSON (généré post-validation CEO)
"""

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
            "agent_id": "accounting",
            "deliverables": ["Suivi CAPEX/OPEX", "Hypothèses revenus M3/M12"],
            "priority": "medium",
            "phase": "finance",
        },
    ],
    "robotics": [
        {
            "pole": "Hardware",
            "agent_id": "hardware",
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
            "agent_id": "content",
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
    "hub": [
        {
            "pole": "Spec & Architecture Hub",
            "agent_id": "spec_agent",
            "deliverables": ["Spec ALNUA_HUB (fichiers impactés)", "Prompt Cursor prêt"],
            "priority": "critical",
            "phase": "conception",
        },
        {
            "pole": "PM Ops",
            "agent_id": "pm_agent",
            "deliverables": ["Backlog infra Hub", "Critères d'acceptation"],
            "priority": "high",
            "phase": "conception",
        },
        {
            "pole": "Dev Backend Hub",
            "agent_id": "dev_backend",
            "deliverables": ["Routes API / services Python", "Tests pytest"],
            "priority": "high",
            "phase": "build",
        },
        {
            "pole": "Dev App (UI Hub)",
            "agent_id": "dev_app",
            "deliverables": ["Composants web/src/", "Intégration API Hub"],
            "priority": "high",
            "phase": "build",
        },
        {
            "pole": "QA Hub",
            "agent_id": "qa",
            "deliverables": ["Plan de tests", "Checklist non-régression"],
            "priority": "high",
            "phase": "qa",
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
    m6 = rev.get("m6_monthly_run_rate_eur") or rev.get("m6_mrr_eur")
    m12 = rev.get("m12_monthly_run_rate_eur") or rev.get("m12_mrr_eur")
    if m6:
        lines.append(f"\n- **Revenu estimé M6 :** {m6} €/mois")
    if m12:
        lines.append(f"- **Revenu estimé M12 :** {m12} €/mois")
    return "\n".join(lines)


def _finance_summary(dossier: RndDossierOut) -> str:
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


def _revenue_projection(dossier: RndDossierOut) -> str:
    fj = dossier.finance_json or {}
    rev = fj.get("revenue_hypothesis") or {}
    sections = _section_map(dossier)
    if not rev:
        return "_Hypothèses revenus non renseignées — compléter la section business case._"
    lines = [
        "### COGS & investissement initial",
        "",
        _finance_summary(dossier),
        "",
        "### OPEX récurrents",
        "",
        f"- Hébergement / infra : {fj.get('opex_hosting_eur', fj.get('opex_monthly_eur', '—'))} €/mois",
        f"- Tokens agents IA : {fj.get('llm_monthly_eur', '—')} €/mois",
        "",
        "### Stratégie de vente & pricing",
        "",
        _pricing_table(dossier),
        "",
        "### Projection impact (si le produit fonctionne)",
        "",
        _excerpt(
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


def _build_block_content(key: str, dossier: RndDossierOut, sections: dict[str, str]) -> str:
    branch = resolve_branch(dossier)
    fj = dossier.finance_json or {}

    if key == "executive_summary":
        if branch == "robotics":
            return (
                "### La promesse produit\n"
                + _excerpt(sections.get("solution", ""), 350)
                + "\n\n### Statut des 3 piliers\n"
                "- **Hardware :** "
                + _excerpt(sections.get("manufacturing", ""), 200)
                + "\n- **Software (app compagnon) :** "
                + _excerpt(sections.get("solution", ""), 200)
                + "\n- **IA (cerveau) :** "
                + _excerpt(sections.get("feasibility", ""), 200)
                + "\n\n### Enveloppe budgétaire globale\n"
                + _finance_summary(dossier)
            )
        if branch == "gaming":
            return (
                "### La promesse produit\n"
                + _excerpt(sections.get("solution", ""), 350)
                + "\n\n### Statut vertical slice\n"
                + _excerpt(sections.get("mvp", ""), 300)
                + "\n\n### Enveloppe budgétaire globale\n"
                + _finance_summary(dossier)
            )
        if branch == "hub":
            return (
                "### Capacité visée pour ALNUA (entreprise)\n"
                + _excerpt(sections.get("problem", ""), 280)
                + "\n\n### Solution proposée dans ALNUA_HUB\n"
                + _excerpt(sections.get("solution", ""), 350)
                + "\n\n### Périmètre v1 (MVP interne)\n"
                + _excerpt(sections.get("mvp", ""), 300)
                + "\n\n### Coût / effort estimé\n"
                + _finance_summary(dossier)
                + "\n\n> **Cible repo :** `ALNUA_HUB` — infra interne, pas produit marché externe."
            )
        return (
            "### La promesse produit\n"
            + _excerpt(sections.get("problem", ""), 280)
            + "\n\n"
            + _excerpt(sections.get("solution", ""), 280)
            + "\n\n### Statut produit & MVP\n"
            + _excerpt(sections.get("mvp", ""), 300)
            + "\n\n### Enveloppe budgétaire globale\n"
            + _finance_summary(dossier)
        )

    if key == "technical_assessment":
        if branch == "robotics":
            return (
                "### Hardware (le corps)\n"
                + _excerpt(sections.get("manufacturing", ""), 450)
                + "\n\n### Software (l'interface)\n"
                + _excerpt(sections.get("solution", ""), 400)
                + "\n\n### Intelligence artificielle (le cerveau)\n"
                + _excerpt(sections.get("feasibility", ""), 450)
            )
        if branch == "gaming":
            return (
                "### Performances cibles\n"
                + _excerpt(sections.get("mvp", ""), 400)
                + "\n\n### Réseau / multijoueur\n"
                + (
                    _excerpt(sections.get("feasibility", ""), 400)
                    if any(
                        w in sections.get("feasibility", "").lower()
                        for w in ("multi", "réseau", "network")
                    )
                    else "_Multijoueur non explicite — préciser latence, authoritative server, anti-cheat._"
                )
                + "\n\n### Direction artistique\n"
                + _excerpt(sections.get("lore", ""), 300)
                + "\n\n"
                + _excerpt(sections.get("visual_identity", ""), 300)
            )
        if branch == "hub":
            return (
                "### Backend (FastAPI)\n"
                + _excerpt(sections.get("feasibility", ""), 400)
                + "\n- `api/routers/` · `services/` · `agents/`\n\n"
                "### Frontend (Next.js web/)\n"
                + _excerpt(sections.get("solution", ""), 350)
                + "\n\n### Agents & workflows impactés\n"
                + _excerpt(sections.get("mvp", ""), 350)
                + "\n\n### Repo cible\n"
                "- **ALNUA_HUB** uniquement — pas nomad/naia/wyrdheim."
            )
        return (
            "### Produit & UX\n"
            + _excerpt(sections.get("solution", ""), 400)
            + "\n\n### Stack & scalabilité\n"
            + _excerpt(sections.get("feasibility", ""), 400)
            + "\n\n### IA intégrée\n"
            + (
                f"Coût pipeline agents : {fj.get('capex_llm_agents_eur', '—')} € · "
                f"{fj.get('llm_monthly_eur', '—')} €/mois\n\n"
                + _excerpt(sections.get("feasibility", ""), 250)
            )
        )

    if key == "compliance_security":
        risks = _excerpt(sections.get("risks", ""), 350)
        base = (
            "### Sécurité & données\n"
            "- Minimisation des données collectées, chiffrement en transit/repos.\n"
            "- **RGPD** : consentement, DPA fournisseurs cloud, droit à l'effacement.\n\n"
        )
        if branch == "robotics":
            base += (
                "### Sécurité physique\n"
                "- Matériaux non toxiques, normes CE/FCC, absence de pincement/surchauffe.\n\n"
                "### Privacy & capteurs\n"
                "- Micro/caméra : traitement local si possible, anonymisation, rétention limitée.\n\n"
            )
        return base + "### Risques conformité (dossier)\n" + risks

    if key == "industrialization":
        return (
            "### Sourcing\n"
            + _excerpt(sections.get("manufacturing", ""), 400)
            + "\n\n### Assemblage\n"
            + "_Préciser site d'assemblage, volumes pilotes, lead times fournisseurs._\n\n"
            "### Déploiement logiciel (OTA)\n"
            + _excerpt(sections.get("feasibility", ""), 350)
        )

    if key == "go_to_market":
        if branch == "hub":
            return (
                "### Rollout interne\n"
                + _excerpt(sections.get("mvp", ""), 400)
                + "\n\n### Déploiement Hub\n"
                "- Redémarrage API uvicorn + rebuild web si UI\n"
                "- Tests `pytest` + smoke test UI\n"
                "- Pas de page publique `/p/` ni marketing externe\n\n"
                "### Communication\n"
                "- Brief Emilie (CEO) + note dans agent_logs"
            )
        return (
            "### Acquisition & scalabilité cloud\n"
            + _excerpt(sections.get("market", ""), 450)
            + "\n\n### UI/UX & rétention\n"
            + _excerpt(sections.get("solution", ""), 300)
            + "\n\n### Stratégie sociale\n"
            + _excerpt(sections.get("social_strategy", ""), 300)
        )

    if key == "production_plan":
        return (
            "### Pipeline contenu & perfs\n"
            + _excerpt(sections.get("mvp", ""), 400)
            + "\n\n### Architecture réseau\n"
            + _excerpt(sections.get("feasibility", ""), 350)
            + "\n\n### Direction artistique\n"
            + _excerpt(sections.get("visual_identity", ""), 350)
        )

    if key == "business_model":
        return _revenue_projection(dossier)

    if key == "risk_matrix":
        risks = sections.get("risks", "")
        body = _excerpt(risks, 600) if risks else ""
        template = (
            "| Risque | Impact | Mitigation |\n"
            "|--------|--------|------------|\n"
            "| Dépendance technique | Moyen | Plan B stack / fournisseur alternatif |\n"
            "| Marché / adoption | Élevé | MVP ciblé, validation early adopters |\n"
            "| Coûts IA / infra | Moyen | Budget plafonné, monitoring coûts |\n"
        )
        return (body + "\n\n" if body else "") + template

    if key == "rd_transverse":
        return (
            "L'investissement IA n'est pas isolé à ce projet : ALNUA mutualise agents, prompts "
            "et modèles via le Hub.\n\n"
            "**Argument financier :** les coûts OpenRouter alimentent un socle réutilisable "
            "(R&D, comité, contenu, spec) — pas un one-shot par produit.\n\n"
            "**Argument stratégique :** écosystème cohérent (app + hardware + contenu) "
            "→ valorisation portfolio.\n\n"
            f"**Ce projet ({dossier.title})** consomme : enrichissement dossier, comité multi-agents, "
            f"pipeline CEO — réutilisable pour les prochains lancements."
        )

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
                    f"**À envoyer à :** {row['pole']} ({row['agent_id']}).\n"
                    f"**Livrables :** {', '.join(row['deliverables'])}."
                ),
            }
        )
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
                "Coordonne les pôles — pas de présence en comité R&D."
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
        "app": "Software / App",
        "robotics": "Robotique / Hardware full stack",
        "gaming": "Logiciel lourd / Plateforme 3D",
        "hub": "Hub ALNUA — infra interne entreprise",
        "other": "Transverse",
    }.get(branch, branch)
    lines = [
        f"**Typologie dossier :** {branch_label}",
        f"**Statut :** {dossier.status} · **CEO :** {dossier.ceo_status}",
        f"**Sections validées :** {dossier.sections_validated_count}/{dossier.sections_total_count}",
        "",
        "Ordre de priorisation suggéré (portfolio ALNUA) :",
        "- **Court terme :** apps SaaS — cash-flow rapide, test marché.",
        "- **Moyen terme :** modules IA & contenu mutualisés.",
        "- **Long terme :** hardware / robotique — inertie fabrication.",
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

    return "\n".join(lines)


def build_ceo_package_md(
    dossier: RndDossierOut,
    *,
    committee_report_md: str | None = None,
    committee_transcript_md: str | None = None,
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
        "> Dossier de validation CEO — pourquoi du comment, chiffres, risques, dispatch.",
        "",
        "---",
        "",
    ]

    if committee_report_md and len(committee_report_md.strip()) > 40:
        lines.extend(
            [
                "## Compte-rendu comité R&D",
                "",
                committee_report_md.strip(),
                "",
                "---",
                "",
            ]
        )

    if committee_transcript_md and len(committee_transcript_md.strip()) > 80:
        lines.extend(
            [
                "## Synthèse des échanges — réunion comité",
                "",
                "_Décisions, chiffres et demandes discutés en salle (source : transcript)._",
                "",
                committee_transcript_md.strip()[:28000],
                "",
                "---",
                "",
            ]
        )

    for block in blocks:
        content = _build_block_content(block["key"], dossier, sections)
        lines.extend([f"## {block['title']}", "", content, "", "---", ""])

    lines.extend(
        [
            "## 7. R&D transverse — socle IA mutualisé",
            "",
            _build_block_content("rd_transverse", dossier, sections),
            "",
            "---",
            "",
            "## 8. Master Summary — roadmap portfolio",
            "",
            build_portfolio_summary(dossier, portfolio_rows=portfolio_rows),
            "",
            "---",
            "",
            "## 9. Matrice dispatch — qui fait quoi, quoi envoyer à qui",
            "",
            "| Pôle | Agent | Livrables à envoyer | Priorité |",
            "|------|-------|---------------------|----------|",
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
            "*Dossier CEO ALNUA — validation Emilie requise avant dispatch COO.*",
        ]
    )
    return "\n".join(lines)


def build_ceo_package_json(
    dossier: RndDossierOut,
    *,
    committee_report_md: str | None = None,
    committee_transcript_md: str | None = None,
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
    block_contents["rd_transverse"] = {
        "title": "7. R&D transverse — socle IA mutualisé",
        "content_md": _build_block_content("rd_transverse", dossier, sections),
    }
    md = markdown or build_ceo_package_md(
        dossier,
        committee_report_md=committee_report_md,
        committee_transcript_md=committee_transcript_md,
        portfolio_rows=portfolio_rows,
    )
    return {
        "version": 2,
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
        "committee_transcript_md": committee_transcript_md,
        "recommendation": _extract_go_recommendation(sections.get("decision", "")),
    }


def _extract_go_recommendation(decision_md: str) -> str:
    text = (decision_md or "").upper()
    for verdict in ("GO", "MAYBE", "NO"):
        if verdict in text:
            return verdict
    return "MAYBE"
