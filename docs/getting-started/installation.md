# Getting Started — ALNUA Hub

## Prérequis

- Python 3.11+
- Node.js 18+
- Compte Supabase + OpenRouter API key

## Installation (15 minutes)

```bash
# 1. Cloner et configurer
cd C:\Dev\ALUNA_HUB
cp .env.example .env
# Remplir : SUPABASE_URL, SUPABASE_KEY, OPENROUTER_API_KEY, HUB_API_KEY

# 2. Backend
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8003

# 3. Frontend
cd web && npm install && npm run dev
```

Ouvre http://localhost:3000 — le Hub proxy `/api/hub` pointe vers le backend.

## Concepts clés

| Concept | Description |
|---------|-------------|
| **Agents** | 20 personas IA (COO, PM, QA, Dev, R&D…) avec operating specs |
| **Rooms** | 9 pièces thématiques (direction, app_office, rnd_lab…) |
| **Workflows** | Pipelines orchestrés remplaçant n8n pour les tâches internes |
| **Mémoire** | Mem0 — chaque agent apprend de ses tâches |
| **Compétition** | Scoring inter-agents avec milestones |

## Première action

1. Va sur **Assistants** → parle à Aria : *"Priorités du jour"*
2. Ou à Nadia : *"Rapport de la nuit Academy"*
3. Vérifie `/health` et `/v1/health` (API versionnée)

## Variables importantes

```env
HUB_API_KEY=          # Auth API (obligatoire en prod)
DEFAULT_TENANT_ID=    # Multi-tenancy (défaut: alnua_coo)
LLM_CACHE_ENABLED=1   # Cache réponses LLM déterministes
RATE_LIMIT_ENABLED=1  # Rate limiting assistant/chat
```

## Suite

- [Concepts détaillés](./concepts.md)
- [API Reference](../API_ROUTES.md)
- [Changelog](../changelog.md)
