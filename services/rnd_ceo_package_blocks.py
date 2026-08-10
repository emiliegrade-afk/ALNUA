"""CEO package block content builders — branch-specific section bodies."""

from __future__ import annotations

from services.rnd_ceo_package_helpers import (
    excerpt,
    finance_summary,
    resolve_branch,
    revenue_projection,
)
from services.rnd_schemas import RndDossierOut


def build_block_content(key: str, dossier: RndDossierOut, sections: dict[str, str]) -> str:
    branch = resolve_branch(dossier)
    fj = dossier.finance_json or {}

    if key == "executive_summary":
        if branch == "robotics":
            return (
                "### La promesse produit\n"
                + excerpt(sections.get("solution", ""), 350)
                + "\n\n### Statut des 3 piliers\n"
                "- **Hardware :** "
                + excerpt(sections.get("manufacturing", ""), 200)
                + "\n- **Software (app compagnon) :** "
                + excerpt(sections.get("solution", ""), 200)
                + "\n- **IA (cerveau) :** "
                + excerpt(sections.get("feasibility", ""), 200)
                + "\n\n### Enveloppe budgétaire globale\n"
                + finance_summary(dossier)
            )
        if branch == "gaming":
            return (
                "### La promesse produit\n"
                + excerpt(sections.get("solution", ""), 350)
                + "\n\n### Statut vertical slice\n"
                + excerpt(sections.get("mvp", ""), 300)
                + "\n\n### Enveloppe budgétaire globale\n"
                + finance_summary(dossier)
            )
        if branch == "hub":
            return (
                "### Capacité visée pour ALNUA (entreprise)\n"
                + excerpt(sections.get("problem", ""), 280)
                + "\n\n### Solution proposée dans ALNUA_HUB\n"
                + excerpt(sections.get("solution", ""), 350)
                + "\n\n### Périmètre v1 (MVP interne)\n"
                + excerpt(sections.get("mvp", ""), 300)
                + "\n\n### Coût / effort estimé\n"
                + finance_summary(dossier)
                + "\n\n> **Cible repo :** `ALNUA_HUB` — infra interne, pas produit marché externe."
            )
        return (
            "### La promesse produit\n"
            + excerpt(sections.get("problem", ""), 280)
            + "\n\n"
            + excerpt(sections.get("solution", ""), 280)
            + "\n\n### Statut produit & MVP\n"
            + excerpt(sections.get("mvp", ""), 300)
            + "\n\n### Enveloppe budgétaire globale\n"
            + finance_summary(dossier)
        )

    if key == "technical_assessment":
        if branch == "robotics":
            return (
                "### Hardware (le corps)\n"
                + excerpt(sections.get("manufacturing", ""), 450)
                + "\n\n### Software (l'interface)\n"
                + excerpt(sections.get("solution", ""), 400)
                + "\n\n### Intelligence artificielle (le cerveau)\n"
                + excerpt(sections.get("feasibility", ""), 450)
            )
        if branch == "gaming":
            return (
                "### Performances cibles\n"
                + excerpt(sections.get("mvp", ""), 400)
                + "\n\n### Réseau / multijoueur\n"
                + (
                    excerpt(sections.get("feasibility", ""), 400)
                    if any(
                        w in sections.get("feasibility", "").lower()
                        for w in ("multi", "réseau", "network")
                    )
                    else "_Multijoueur non explicite — préciser latence, authoritative server, anti-cheat._"
                )
                + "\n\n### Direction artistique\n"
                + excerpt(sections.get("lore", ""), 300)
                + "\n\n"
                + excerpt(sections.get("visual_identity", ""), 300)
            )
        if branch == "hub":
            return (
                "### Backend (FastAPI)\n"
                + excerpt(sections.get("feasibility", ""), 400)
                + "\n- `api/routers/` · `services/` · `agents/`\n\n"
                "### Frontend (Next.js web/)\n"
                + excerpt(sections.get("solution", ""), 350)
                + "\n\n### Agents & workflows impactés\n"
                + excerpt(sections.get("mvp", ""), 350)
                + "\n\n### Repo cible\n"
                "- **ALNUA_HUB** uniquement — pas nomad/naia/wyrdheim."
            )
        return (
            "### Produit & UX\n"
            + excerpt(sections.get("solution", ""), 400)
            + "\n\n### Stack & scalabilité\n"
            + excerpt(sections.get("feasibility", ""), 400)
            + "\n\n### IA intégrée\n"
            + (
                f"Coût pipeline agents : {fj.get('capex_llm_agents_eur', '—')} € · "
                f"{fj.get('llm_monthly_eur', '—')} €/mois\n\n"
                + excerpt(sections.get("feasibility", ""), 250)
            )
        )

    if key == "compliance_security":
        risks = excerpt(sections.get("risks", ""), 350)
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
            + excerpt(sections.get("manufacturing", ""), 400)
            + "\n\n### Assemblage\n"
            + "_Préciser site d'assemblage, volumes pilotes, lead times fournisseurs._\n\n"
            "### Déploiement logiciel (OTA)\n"
            + excerpt(sections.get("feasibility", ""), 350)
        )

    if key == "go_to_market":
        if branch == "hub":
            return (
                "### Rollout interne\n"
                + excerpt(sections.get("mvp", ""), 400)
                + "\n\n### Déploiement Hub\n"
                "- Redémarrage API uvicorn + rebuild web si UI\n"
                "- Tests `pytest` + smoke test UI\n"
                "- Pas de page publique `/p/` ni marketing externe\n\n"
                "### Communication\n"
                "- Brief Emilie (CEO) + note dans agent_logs"
            )
        return (
            "### Acquisition & scalabilité cloud\n"
            + excerpt(sections.get("market", ""), 450)
            + "\n\n### UI/UX & rétention\n"
            + excerpt(sections.get("solution", ""), 300)
            + "\n\n### Stratégie sociale\n"
            + excerpt(sections.get("social_strategy", ""), 300)
        )

    if key == "production_plan":
        return (
            "### Pipeline contenu & perfs\n"
            + excerpt(sections.get("mvp", ""), 400)
            + "\n\n### Architecture réseau\n"
            + excerpt(sections.get("feasibility", ""), 350)
            + "\n\n### Direction artistique\n"
            + excerpt(sections.get("visual_identity", ""), 350)
        )

    if key == "business_model":
        return revenue_projection(dossier)

    if key == "risk_matrix":
        risks = sections.get("risks", "")
        body = excerpt(risks, 600) if risks else ""
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

    return excerpt(sections.get(key, ""), 500)
