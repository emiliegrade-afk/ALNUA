---
name: alnua-n8n
description: Orchestration autonome ALNUA via n8n — workflows, endpoints /orchestration, câblage événements.
---

# ALNUA n8n — Orchestration autonome

## Quand invoquer ce skill

- Ajouter un workflow n8n qui déclenche des agents
- Câbler un événement externe (GitHub, Supabase, cron) vers le Hub
- Créer une chaîne agent→agent (spec→QA, morning COO, etc.)

## Doc complète

Lire `docs/N8N_ORCHESTRATION.md` avant toute modification.

## Endpoints Hub (tous requièrent `X-Hub-Key`)

| Workflow | Endpoint |
|----------|----------|
| Morning briefing + COO | `POST /orchestration/morning` |
| Spec adversariale | `POST /orchestration/spec-qa-chain` |
| Revue PR GitHub | `POST /orchestration/github-pr-review` |
| Email bienvenue | `POST /orchestration/welcome-user` |
| Sprint contenu | `POST /orchestration/content-sprint` |
| Catalogue | `GET /orchestration/workflows` |

## Pattern — ajouter un workflow

1. **Service** : ajouter `run_<workflow>()` dans `services/orchestration.py`
2. **Schema** : modèle Pydantic dans `api/schemas.py`
3. **Router** : endpoint dans `api/routers/orchestration.py`
4. **Catalogue** : entrée dans `WORKFLOW_CATALOG`
5. **n8n** : export JSON dans `n8n/workflows/`
6. **Doc** : mettre à jour `docs/N8N_ORCHESTRATION.md`

## Variables n8n — pas besoin

Les workflows embarquent URL + `X-Hub-Key` directement dans le node HTTP Request.  
Aucune Variable, Credential ou Settings à chercher.

## Règles

- n8n appelle le Hub — jamais l'inverse (sauf webhooks entrants n8n)
- Toujours `X-Hub-Key` sur les HTTP Request nodes
- Loguer via `_log_run()` dans orchestration.py (agent_logs Supabase)
- Dégradé silencieux sur les étapes non-critiques

## Workflows existants

```
n8n/workflows/01-morning-briefing.json
n8n/workflows/02-github-pr-review.json
n8n/workflows/03-spec-qa-chain.json
n8n/workflows/04-welcome-user.json
n8n/workflows/05-content-sprint.json
```
