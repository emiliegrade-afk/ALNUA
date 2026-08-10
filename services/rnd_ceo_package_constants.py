"""CEO package branch templates and dispatch pole definitions."""

from __future__ import annotations

from typing import Any

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
            "pole": "Dev Mobile",
            "agent_id": "dev_app",
            "deliverables": ["Repo Expo initial", "MVP sprint 1 mobile"],
            "priority": "high",
            "phase": "build",
        },
        {
            "pole": "Dev Backend",
            "agent_id": "dev_backend",
            "deliverables": ["API / Supabase", "Auth & données"],
            "priority": "high",
            "phase": "build",
        },
        {
            "pole": "Content App",
            "agent_id": "content_app",
            "deliverables": ["Posts lancement app", "Calendrier social app"],
            "priority": "medium",
            "phase": "launch_prep",
        },
        {
            "pole": "Marketing Ads",
            "agent_id": "marketing_agent",
            "deliverables": ["Positionnement GTM", "Briefs pubs (déléguer rédaction content_*)"],
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
            "pole": "Content Robotique",
            "agent_id": "content_robo",
            "deliverables": ["Posts MAJ robotique", "Teasers hardware"],
            "priority": "medium",
            "phase": "launch_prep",
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
            "pole": "Content Gaming / Devlogs",
            "agent_id": "content_gaming",
            "deliverables": ["Devlogs Discord", "Teasers réseaux jeux"],
            "priority": "medium",
            "phase": "art",
        },
        {
            "pole": "Marketing Ads",
            "agent_id": "marketing_agent",
            "deliverables": ["Wishlist strategy", "Briefs pubs post-CEO"],
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
            "pole": "Dev Frontend Hub",
            "agent_id": "dev_frontend",
            "deliverables": ["Composants web/src/", "Intégration API Hub"],
            "priority": "high",
            "phase": "build",
        },
        {
            "pole": "Intégrateur",
            "agent_id": "dev_integrator",
            "deliverables": ["Merge worktrees → staging", "Smoke post-merge"],
            "priority": "high",
            "phase": "integrate",
        },
        {
            "pole": "QA Senior",
            "agent_id": "qa",
            "deliverables": ["Review permanente", "Checklist non-régression"],
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
            "pole": "Dev Backend",
            "agent_id": "dev_backend",
            "deliverables": ["Spike technique", "MVP scope backend"],
            "priority": "high",
            "phase": "build",
        },
        {
            "pole": "Content Corporate",
            "agent_id": "content_company",
            "deliverables": ["Annonce ALNUA", "Posts entreprise"],
            "priority": "medium",
            "phase": "launch_prep",
        },
    ],
}
