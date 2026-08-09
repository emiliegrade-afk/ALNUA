# Architecture — ALNUA Hub

## Vision

Hub d'orchestration multi-agents IA — le "siège social virtuel" d'ALNUA, société solo
d'Emilie. **49** personas LLM (COO, PM, QA, dev, marketing, R&D, comptabilité, hardware,
analytics, rôles Gaming/Robo…) réparties en 9 "poles"/rooms simulent les départements
d'une entreprise et travaillent au service de 3 branches produit :

| Branche | Projet | Description |
|---------|--------|--------------|
| App | Naïa | Application bien-être (repo séparé `NAÏA/`) |
| Gaming | Wyrdheim Online | MMORPG fantasy nordique |
| Robotique | Eve | Robot compagnon domestique |

## Tech stack

| Couche | Technologie | Status |
|--------|-------------|--------|
| API REST | FastAPI (`api/main.py` → `api/app.py` → `api/routers/`) | Active |
| Agents LLM | OpenRouter REST (`agents/base.py::LLMClient`), routage dynamique par tier (fast/standard/premium) | Active |
| Orchestration | CrewAI (tâches multi-agents complexes) | Active |
| Base de données | Supabase (PostgreSQL), RLS restreinte SELECT sur tables sensibles | Active |
| Mémoire agents | Mem0 (`skills/skill_mem0.py`) + compression digest | Active |
| Observabilité | Langfuse (`skills/skill_langfuse.py`, `@trace_agent`) | Active |
| Automatisation | n8n (workflows externes, briefing quotidien, orchestration) | Active |
| MCP Server | `fastapi-mcp` monté sur `/mcp` dans `api/app.py`, protégé par `X-Hub-Key` | Active |
| Frontend | Next.js 16 + React 18 + TypeScript (`web/`), Playwright e2e | Active |
| Bots | Discord, Telegram (bot + secretary + presence), Publisher, Reviews, Analytics, SAV, Watchdog (`bots/`) | Active |
| Files d'attente | Redis (`services/redis_client.py`, `services/rq_queue.py`) | Active |
| Intégrations tierces | Composio (OAuth gateway 250+ APIs), ElevenLabs (voix), Google Calendar (jalons) | Active |

## Modules — vue d'ensemble

> Table non exhaustive au niveau fichier — le détail agent-par-agent (49 personas,
> room/team/tier/persona) est tenu à jour dans `CLAUDE.md`, source de vérité, pas ici.
> Cette table donne l'altitude "où chercher", pas le contenu.

| Module | Emplacement | Taille approx. | Status |
|--------|-------------|-----------------|--------|
| Routers API | `api/routers/` | Voir `ALL_ROUTERS` (+ `gdd.py` conditionnel) ; R&D éclaté en `rnd_*` | Active |
| Agents personas | `agents/*_agent.py` | **49** agents personas (34 + 15 rôles Gaming/Robo, Phase 13) + orchestrateurs infra | Active |
| Services métier | `services/` | ~128 modules (compétition, coûts, R&D dossier, academy, telegram, brand, coding pipeline...) | Active |
| Config | `config/` | Personas, tiers, specs opérationnelles 9-couches, settings pydantic | Active |
| Bots | `bots/` | 11 bots (Discord/Telegram/Publisher/Reviews/Analytics/SAV/Watchdog) | Active |
| Frontend dashboard | `web/` | Siège social virtuel (lobby + bureaux + `*-v2` Marketing/Finance/R&D), Next.js 16 | Active |
| Base de données | `database/schema.sql` + `database/supabase_client.py` | — | Active |
| Tests | `tests/` | **80** fichiers `test_*.py` (**433** tests collectés, Vague F 2026-08-10) + `web/e2e` Playwright + Vitest | Active |
| Gouvernance + méthode de travail | `AGENTS.md` (entrée universelle), `CLAUDE.md`, `.cursor/rules/*.mdc` (agent-orchestration, ai-agent-survival, async-jobs + règles scopées par feature) | 8 fichiers gouvernance + 3 règles générales + règles scopées | Active |

## Data flow

```
web/ (dashboard) ─┐
bots/ (Discord/Telegram) ─┤
n8n (workflows externes) ─┼─→ api/routers/*.py (X-Hub-Key + sanitize_user_input)
Cursor (MCP client) ──────┘         │
                                     ▼
                          agents/*_agent.py (AgentBase)
                                     │  self.llm (OpenRouter) + self.db (Supabase)
                    ┌────────────────┼────────────────┐
                    ▼                ▼                ▼
            services/*.py    skills/skill_mem0.py   skills/skill_langfuse.py
         (compétition, coûts,   (mémoire persistante)   (tracing @trace_agent)
          pipelines R&D...)
                    │
                    ▼
        database/supabase_client.py → Supabase (Postgres + RLS)
```

## External dependencies

| Service | Usage | Notes |
|---------|-------|-------|
| OpenRouter | Modèle LLM par agent, routé dynamiquement (`services/llm_router.py`) | Clé dans `.env`, jamais en dur |
| Supabase | Persistance + auth + RLS | `SUPABASE_URL`/`SUPABASE_KEY` dans `.env` |
| Mem0 | Mémoire longue par agent | — |
| Langfuse | Traces LLM | — |
| n8n | Déclenchement de workflows (briefing quotidien, orchestration) | `alnua.app.n8n.cloud` |
| Composio | Passerelle OAuth vers 250+ APIs tierces | — |
| Discord / Telegram | Bots opérationnels | Fallback gracieux si token/channel absent (voir commit `f9054d0`) |
| ElevenLabs | Suivi coûts voix (`services/elevenlabs_monitor.py`) | — |
| Google Calendar | Jalons ("Jalons à venir") via Nadia | — |

## Security model

- **Auth API** : header `X-Hub-Key` obligatoire dans **tous** les environnements (`HUB_API_KEY`) — l'API refuse de démarrer sans clé configurée, plus de bypass dev (durci le 2026-07-25, voir DEC-.. dans `DECISIONS.md` et SEC-002 dans `BUGS.md`).
- **Sanitization** : `services/input_sanitizer.py::sanitize_user_input` sur la quasi-totalité des entrées libres avant LLM/DB — **exception documentée et volontaire** : `api/routers/agents_pole.py` désactive la redaction PII car ces endpoints véhiculent volontairement des données business réelles (cf. CLAUDE.md).
- **RLS Supabase** : restreinte à `SELECT` sur les tables sensibles (commit `2df9669`).
- **Accès fichiers** : `/brand/assets` restreint au dossier `brand_kits/` (commit `d094203`), pas de traversée de chemin arbitraire.
- **Secrets** : `.env`/`.env.prod` gitignorés, jamais commités ; `.env.example` sert de gabarit.
- **MCP** : monté sur `/mcp`, protégé par le même `X-Hub-Key` que le reste de l'API.

## Performance targets

Non formalisé à ce jour — pas de budget de latence/coût explicite documenté ailleurs
que `services/cost_monitor.py::check_budget_alert(daily_budget_usd)` (alerte budget
LLM, pas un SLA). À définir si des exigences de latence/coût deviennent un besoin réel
plutôt qu'un objectif hypothétique.

## Glossary

- **Pole / Room** : département simulé de l'entreprise (direction, app_office, gaming_studio, rnd_lab, comms_hub, accounting_office, hardware_workshop, analytics_room).
- **Team** : regroupement fonctionnel d'agents au sein d'un pole (ex. `app`, `gaming`, `innovation`, `business`, `finance`, `robo`, `analytics`).
- **Tier** : niveau de modèle LLM alloué à un agent (`fast` / `standard` / `premium`), résolu dynamiquement par `services/llm_router.py`.
- **Persona** : identité incarnée d'un agent (prénom, titre, ton) définie dans `config/agent_personas.py`.
- **Dossier hub (R&D)** : pipeline d'assemblage d'un dossier R&D complet (hypothèses, deck, package CEO, comité) — voir `SPEC_RND_DOSSIER_HUB.md`.
- **9-layer operating spec** : format de `SYSTEM_PROMPT` généré par `config/agent_operating_spec.py::get_system_prompt(agent_id)`, remplace progressivement les prompts inline 5-sections.
