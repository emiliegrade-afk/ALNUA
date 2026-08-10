"""Workflow catalog for orchestration endpoints."""

from __future__ import annotations

from typing import Any

WORKFLOW_CATALOG: list[dict[str, Any]] = [
    {
        "id": "morning",
        "name": "Briefing matinal + plan COO",
        "endpoint": "POST /orchestration/morning",
        "trigger": "Automatique lun-ven 08:00 + n8n",
        "agents": ["coo"],
        "level": 3,
    },
    {
        "id": "spec_qa_chain",
        "name": "Spec adversariale → ticket QA",
        "endpoint": "POST /orchestration/spec-qa-chain",
        "trigger": "Webhook n8n après spec",
        "agents": ["spec", "qa"],
        "level": 3,
    },
    {
        "id": "github_pr_review",
        "name": "Revue PR GitHub",
        "endpoint": "POST /orchestration/github-pr-review",
        "trigger": "Webhook n8n — GitHub PR",
        "agents": ["dev_backend"],
        "level": 4,
    },
    {
        "id": "welcome_user",
        "name": "Email de bienvenue",
        "endpoint": "POST /orchestration/welcome-user",
        "trigger": "Webhook n8n — nouvel inscrit",
        "agents": ["secretary"],
        "level": 4,
    },
    {
        "id": "content_sprint",
        "name": "Sprint contenu multi-plateforme",
        "endpoint": "POST /orchestration/content-sprint",
        "trigger": "Automatique vendredi 17:00 + n8n",
        "agents": ["content", "marketing"],
        "level": 2,
    },
    {
        "id": "academy_sprint",
        "name": "Sprint Académie dev_app",
        "endpoint": "POST /orchestration/academy-sprint",
        "trigger": "n8n workflow 08 — lundi 09:00",
        "agents": ["dev_app"],
        "level": 2,
    },
    {
        "id": "academy_poll",
        "name": "Poll Academy + sync + queue",
        "endpoint": "POST /orchestration/academy-poll",
        "trigger": "n8n workflow 12 — toutes les 30 min",
        "agents": ["dev_app"],
        "level": 2,
    },
    {
        "id": "prd_decompose",
        "name": "PRD Engineering → issues GitHub",
        "endpoint": "POST /orchestration/prd-decompose",
        "trigger": "n8n workflow 07 — après validation CEO",
        "agents": ["spec", "pm", "qa"],
        "level": 3,
    },
    {
        "id": "sentry_ingest",
        "name": "Sentry alert → hotfix issue",
        "endpoint": "POST /orchestration/sentry-ingest",
        "trigger": "n8n workflow 09 — alertes production",
        "agents": ["dev_app", "dev_backend", "qa"],
        "level": 4,
    },
    {
        "id": "security_ingest",
        "name": "Security barrier → Telegram/email + journal",
        "endpoint": "POST /orchestration/security-ingest",
        "trigger": "RESONANCE fortress / apps — auth burst, data anomaly",
        "agents": ["dev_resonance", "qa_agent", "coo"],
        "level": 4,
    },
    {
        "id": "academy_gate",
        "name": "Évaluation gate readiness Academy → Lounge",
        "endpoint": "POST /orchestration/academy-gate",
        "trigger": "n8n workflow 10 — check quotidien CEO",
        "agents": ["coo"],
        "level": 3,
    },
]
