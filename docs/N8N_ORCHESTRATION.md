# Orchestration n8n — ALNUA Hub

> Chaînes agent→agent déclenchées par n8n, le planificateur Hub, ou le panneau `/hub`.

## Statut (à jour)

| Fonctionnalité | Statut |
|----------------|--------|
| 5 workflows n8n (`01`–`05`) | ✅ Importables |
| Briefing matinal + COO | ✅ Hub 08:00 + n8n |
| Notification Telegram + Discord | ✅ Tous les workflows |
| Spec → QA → ticket Supabase | ✅ Automatique |
| Routeur LLM dynamique | ✅ Si `method_name` passé à `LLMClient` |
| Consoles Jules/Layla/Axel | ✅ `/finances` + `/analytics` |
| Panneau pilotage | ✅ `/hub` — boutons briefing |

## Déclenchement sans n8n

- **Automatique** : `api/lifespan.py` (lun-ven 8h, vendredi 17h)
- **Manuel UI** : `/hub` → « Briefing du jour » ou « Plan de la semaine »
- **API** : `POST /orchestration/morning` ou `POST /briefing/morning-run`

## Workflows n8n

```
n8n/workflows/01-morning-briefing.json
n8n/workflows/02-github-pr-review.json
n8n/workflows/03-spec-qa-chain.json
n8n/workflows/04-welcome-user.json
n8n/workflows/05-content-sprint.json
```

Tous appellent le Hub avec header `X-Hub-Key`.

## Chaîne spec → QA → ticket

`POST /orchestration/spec-qa-chain` :

1. Marcus ↔ Sven (`adversarial_spec`)
2. Création ticket QA dans Supabase (par défaut `create_qa_ticket: true`)
3. Notification Telegram/Discord

```json
{
  "spec_text": "L'agent doit…",
  "context": "Feature X",
  "ticket_title": "Valider spec scoring",
  "project_slug": "hub"
}
```

## Fichiers clés

```
services/orchestration.py
skills/skill_hub_notify.py
api/routers/orchestration.py
web/src/components/hub/hub-automation-panel.tsx
```
