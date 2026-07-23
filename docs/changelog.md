# Changelog ALNUA Hub

## [Unreleased] — Sprints 1-4 (2026-07-09)

### Sprint 1 — Fondations production
- Tests pytest : COO intents, fix_pipeline, services foundation
- Multi-tenancy : `models/tenant.py`, middleware `X-Tenant-ID`
- Sécurité : `input_sanitizer`, rate limiting assistant/API

### Sprint 2 — Scaling
- Cache LLM in-memory avec TTL (`services/llm_cache.py`)
- `LLMClient.chat_async()` — wrapper asyncio
- Task queue async (`services/task_queue.py`)
- Métriques Prometheus `/metrics`

### Sprint 3 — Business
- Personnalisation agents (`agents/personalities.py`, `/personality`)
- Feedback 👍/👎 (`/feedback/agent`) avec regen sur négatif
- Métriques business (`services/analytics.py`, `/platform/stats`)
- API versioning `/v1/*`

### Sprint 4 — Moat
- Marketplace plugins (`plugins/example_echo`, `/plugins`)
- Documentation `docs/getting-started/`
- Backup DR `scripts/backup_daily.py`
