# Concepts ALNUA Hub

## Architecture 3 couches

```
web/ (Next.js)  →  api/ (FastAPI)  →  agents/ + services/
```

## Agents & Operating Specs

Chaque agent a un contrat 9 couches : mission, hors-périmètre, processus, priorités, communication, mémoire, relations, format, qualité.

Compilé via `config/agent_operating_spec.py` → injecté dans le system prompt.

## Multi-tenancy (Sprint 1)

- Header `X-Tenant-ID` sur chaque requête API
- Défaut : `DEFAULT_TENANT_ID` (`.env`)
- Helper : `models/tenant.py` → `with_tenant()`, `tenant_filter()`

## Sécurité (Sprint 1)

- `services/input_sanitizer.py` — filtre injection + longueur max
- `services/rate_limiter.py` — sliding window par IP/session
- Hub key middleware sur routes protégées

## Cache LLM (Sprint 2)

- `services/llm_cache.py` — in-memory TTL
- Activé si `temperature <= 0.1` et `LLM_CACHE_ENABLED=1`
- `LLMClient.chat_async()` pour appels non-bloquants

## Observabilité (Sprint 2)

- Langfuse : tracing agents (`@trace_agent`)
- `/metrics` : format Prometheus
- `/platform/stats` : snapshot admin

## Feedback loop (Sprint 3)

- `POST /feedback/agent` — rating 1 ou -1
- Rating négatif → regen + lesson Mem0
- UI : boutons 👍/👎 dans AssistantChat

## API Versioning (Sprint 3)

Toutes les routes existent sous `/v1/*` en miroir. Exemple :
- `/health` et `/v1/health`
- `/assistant/chat` et `/v1/assistant/chat`

## Plugins (Sprint 4)

```
plugins/
  example_echo/
    manifest.json
    agent.py
```

`GET /plugins` — liste  
`POST /plugins/{id}/run` — exécution

## Backup (Sprint 4)

```bash
python scripts/backup_daily.py
# → backups/YYYY-MM-DD/
```
