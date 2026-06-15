# ALNUA Hub — Cursor Briefing Complet

> Lis ce fichier en entier avant de toucher au code. Il décrit l'état exact du projet, ce qui a été construit récemment, et les patterns à respecter absolument.

---

## Stack technique

| Couche | Tech |
|--------|------|
| API REST | FastAPI — entry: `api/main.py` → `api/app.py` → `api/routers/` |
| Agents LLM | OpenRouter REST via `agents/base.py::LLMClient` |
| Orchestration | CrewAI (tâches complexes multi-agents) |
| Base de données | Supabase (PostgreSQL) — `database/supabase_client.py` |
| Mémoire | Mem0 — `skills/skill_mem0.py` |
| Observabilité | Langfuse — `skills/skill_langfuse.py` |
| Automatisation | n8n (workflows externes) |
| Scores compétition | `services/competition.py` + `data/agent_scores.json` |
| Routage LLM dynamique | `services/llm_router.py` (NadirClaw-inspired) |
| Specs adversariales | `services/adversarial_spec.py` |
| Exécution parallèle | `services/parallel_runner.py` |
| Pipeline contenu | `services/content_pipeline.py` |
| MCP Server | fastapi-mcp monté dans `api/app.py` |

---

## Architecture routers

```
api/
  app.py              ← FastAPI factory + fastapi-mcp mount
  main.py             ← entrypoint uvicorn
  route_common.py     ← tous les imports partagés (wildcard dans chaque router)
  schemas.py          ← tous les modèles Pydantic
  routers/
    __init__.py       ← register_routers(app)
    agents_pole.py    ← 24 endpoints agents (secretary, dev-backend, level-designer,
                         controller, analyst-business, analyst-data + anciens)
    competition.py    ← GET/POST /agents/scores, /agents/leaderboard
    advanced_services.py ← endpoints LLM router, adversarial spec, parallel runner
    core.py           ← endpoints principaux (COO, PM, QA, spec...)
    [+ 14 autres routers]
```

**Règle invariante :** chaque router commence par `from api.route_common import *` — ne jamais dupliquer les imports.

---

## 20 agents ALNUA

### Direction (`direction`)
| Agent ID | Fichier | Persona | Tier |
|----------|---------|---------|------|
| `coo` | `agents/coo_agent.py` | Aria Voss — COO | premium |
| `spec` | `agents/spec_agent.py` | Léon Marchand — Spec | fast |
| `qa` | `agents/qa_agent.py` | Alex Okafor — QA | standard |
| `pm` | `agents/pm_agent.py` | Sam Rivera — PM | standard |

### App Office (`app_office`) — Équipe `app`
| Agent ID | Fichier | Persona | Tier |
|----------|---------|---------|------|
| `dev_app` | `agents/dev_app_agent.py` | Théo Laurent | standard |
| `dev_backend` | `agents/dev_backend_agent.py` | Hao Chen | standard |

### Gaming Studio (`gaming_studio`) — Équipe `innovation`
| Agent ID | Fichier | Persona | Tier |
|----------|---------|---------|------|
| `game_director` | `agents/game_director_agent.py` | Mira Chen | standard |
| `dev_gaming` | `agents/dev_gaming_agent.py` | Nova Fischer | standard |

### R&D Lab (`rnd_lab`)
| Agent ID | Fichier | Persona | Tier |
|----------|---------|---------|------|
| `brainstorm` | `agents/brainstorm_agent.py` | Idris Okonkwo | standard |
| `rnd_agent` | `agents/rnd_agent.py` | Alex Mercer | premium |

### Comms Hub (`comms_hub`)
| Agent ID | Fichier | Persona | Tier |
|----------|---------|---------|------|
| `marketing` | `agents/marketing_agent.py` | Camille Rousseau | standard |
| `content` | `agents/content_agent.py` | Sofia Reyes | standard |

### Accounting Office (`accounting_office`) — Équipe `finance`
| Agent ID | Fichier | Persona | Tier |
|----------|---------|---------|------|
| `accounting` | `agents/accounting_agent.py` | Jules Bernard | fast |
| `controller` | `agents/controller_agent.py` | Rémi Chassagne | fast |

### Hardware Workshop (`hardware_workshop`)
| Agent ID | Fichier | Persona | Tier |
|----------|---------|---------|------|
| `hardware` | `agents/hardware_agent.py` | Yuki Tanaka | fast |
| `embedded_dev` | `agents/embedded_dev_agent.py` | Zara Singh | fast |

### Analytics Room (`analytics_room`) — Équipe `analytics`
| Agent ID | Fichier | Persona | Tier |
|----------|---------|---------|------|
| `analyst_business` | `agents/analyst_business_agent.py` | Layla Hassan | standard |
| `analyst_data` | `agents/analyst_data_agent.py` | Axel Roux | fast |

### Sans room fixe
| Agent ID | Fichier | Persona | Tier |
|----------|---------|---------|------|
| `secretary` | `agents/secretary_agent.py` | Nadia Faure | standard |
| `level_designer` | `agents/level_designer_agent.py` | Finn Larsen | fast |

---

## Pattern agent — règle de création

```python
"""[Role] Agent — [Prénom Nom], [Titre] ALNUA."""
from __future__ import annotations
from typing import Any
from agents.base import LLMClient, log_agent_action, parse_json_response
from database.supabase_client import SupabaseClient, get_supabase
from skills.skill_agent_learning import inject_learning_context, record_task_learning
from skills.skill_langfuse import trace_agent

class MyAgent:
    AGENT_NAME = "my_agent"

    SYSTEM_PROMPT = """Tu es [Prénom], [Titre] d'ALNUA.
[Relation pipeline avec un autre agent nommé explicitement]

Tes spécialités :
- ...

Méthode de travail :
[1-2 règles comportementales concrètes]

Règles de format :
Réponds en JSON valide structuré.

Relation à la qualité :
[Une phrase manifeste courte]"""

    def __init__(self, db=None, llm=None):
        self.db = db or get_supabase()
        self.llm = llm or LLMClient()

    @trace_agent("my_agent")
    def my_method(self, param: str) -> dict[str, Any]:
        prompt = inject_learning_context(f"...", self.AGENT_NAME, param)
        raw = self.llm.complete(self.SYSTEM_PROMPT, prompt, agent_id=self.AGENT_NAME, temperature=0.4)
        result = parse_json_response(raw)
        log_agent_action(self.db, self.AGENT_NAME, "my_method",
            input_summary=param[:100], output_summary=str(result)[:100])
        try:
            record_task_learning(self.AGENT_NAME, "my_method", str(result)[:300], success=True)
        except Exception:
            pass
        return result
```

---

## LLMClient — intégration compétition automatique

`agents/base.py::LLMClient.chat()` injecte automatiquement `get_competitive_context()` dans le system prompt si `persona["competitive"] == True`. La compétition est donc **transparente** — les agents n'en savent pas plus que ce que le système injecte.

`run_with_learning(agent_id, task, fn, *args)` — wrapper qui :
1. Exécute `fn(*args)`
2. Déclenche apprentissage Mem0
3. Appelle `add_points(agent_id, "task_completed")` automatiquement

---

## Services avancés récemment ajoutés

### `services/llm_router.py` — Routeur LLM dynamique (NadirClaw-inspired)
Auto-sélectionne le tier (fast/standard/premium) selon la complexité de la tâche mesurée dynamiquement. Expose `route_to_model(agent_id, prompt, method_name)` → retourne le model slug optimal.

### `services/adversarial_spec.py` — Spec adversariale (adversarial-spec-inspired)
Fait débattre deux LLMs sur une spec jusqu'à consensus. `debate_spec(spec_text, rounds)` → retourne la spec convergée + les divergences identifiées. Utilisable par Léon (Spec) + Alex (QA).

### `services/parallel_runner.py` — Parallel runner v2 (oh-my-claude + agent-orchestrator)
`run_agents_parallel(tasks)` — asyncio.gather avec semaphore. Nouveautés : retry exponentiel (`max_retries`, cap 3), `depends_on` par tâche, progress tracking (`_TASK_PROGRESS`). `run_with_dependencies(tasks)` pour pipelines mixtes séquentiel/parallèle. `get_progress(run_id)` pour suivi temps réel.

### `services/content_pipeline.py` — Pipeline contenu (content-pipeline-inspired)
`run_pipeline(brief, platforms)` — un brief → formats multi-plateformes en parallèle. Intègre Sofia (Content) + Camille (Marketing).

### `services/trend_monitor.py` — Radar tendances (TrendRadar-inspired)
Agrège HackerNews (Firebase API), Reddit (JSON API), GitHub Search — sans auth. `get_trend_brief(topics, sources, agent_id)` → brief LLM synthétisé par Camille. `get_raw_trends()` pour les données brutes. `TrendItem` / `TrendBrief` dataclasses.

### `services/deep_research.py` — Recherche profonde (deep-research-inspired)
Pipeline multi-rounds : round 1=explore, round 2=deepen, round 3=verify → `_synthesize_all_rounds()`. `run_deep_research(query, rounds=3, agent_id)` — agents : brainstorm, rnd_agent, analyst_business. `quick_research()` pour 1 round. `ResearchRound` / `ResearchReport` dataclasses. Ajoute des points compétition à la fin.

### `services/plan_executor.py` — Executor de plans COO (ralphex-inspired)
`run_coo_plan(objective, context)` — pipeline complet : COO génère le plan JSON → executor le déroule en respectant `depends_on`. `execute_plan(plan, max_concurrent, stop_on_failure)` avec retry 3x + backoff. `ExecutionStep` / `ExecutionPlan` / `StepResult` dataclasses. `parse_coo_plan()` utilise Aria (COO) pour décomposer un objectif en steps avec agents et méthodes.

### `services/code_graph.py` — Graphe codebase (graphify-inspired)
Parse AST Python → graphe nœuds (file, class, function, endpoint, agent, table) + arêtes (imports, defines, exposes, uses). Cache en mémoire 5min. `query_graph(question)` — Axel répond en NL. `get_agent_context(agent_id)` — imports/méthodes/endpoints/tables d'un agent. `get_codebase_summary()` — vue d'ensemble. Rebuild auto via `invalidate_cache()`.

### `skills/skill_agent_learning.py` — Apprentissage + compression (claude-mem-inspired)
Ajout v2 : `compress_agent_memory(agent_id, raw_memories)` — distille N leçons → 3-5 règles durables via LLM, écrit `[DIGEST]` dans Mem0. `auto_compress_if_needed(agent_id, threshold=20)` — compression automatique si la mémoire est trop volumineuse.

### `services/cost_monitor.py` — Suivi coûts LLM (llm-cost-tracker-inspired)
Track tokens × prix par modèle/agent. `record_call(agent_id, model, prompt_tokens, completion_tokens)` → retourne le coût USD. `get_cost_report(agent_id, days)` — rapport agrégé par agent/modèle/jour. `check_budget_alert(daily_budget_usd)` → severity ok|warning|critical. `get_monthly_summary(month)` pour Jules (accounting). Persistance JSON dans `data/cost_log.json` (30 jours).

### `services/a_b_tester.py` — A/B test de prompts/agents (prompt-optimizer-inspired)
`run_ab_test(ABTestConfig)` — exécute variants A et B en parallèle, LLM juge le gagnant. `quick_compare(agent_id, method, kwargs_a, kwargs_b)` pour tester des paramètres. Alex (QA) est le juge par défaut. `ABTestConfig(name, variant_a, variant_b, judge_criteria, runs_per_variant)`. Le gagnant reçoit des points compétition.

### `services/event_bus.py` — Bus d'événements inter-agents (agent-memory-stream-inspired)
Pub/sub léger. `emit(event_type, payload, source_agent)` — déclenche les handlers. `@subscribe("spec_validated")` — décorateur d'abonnement. `register_handler(event_type, fn)` — programmatique. `get_recent_events()` + `get_event_stats()`. Handlers pré-câblés : feature_shipped → points compétition, budget_alert → log warning, task_failed → log error. Store 500 events en mémoire + persistance `data/event_log.json`.

### `services/daily_briefing.py` — Briefing quotidien COO (morning-digest-inspired)
`run_daily_briefing(context, include_trends, include_costs, include_events)` — collecte leaderboard + trends + coûts + events en parallèle → Aria (COO) synthétise en brief exécutif JSON (headline, 3 priorités, alertes, opportunités). Déclenché chaque matin par n8n. `run_quick_briefing()` pour version rapide sans trends.

---

## Système compétition

```python
from services.competition import add_points, get_scores, get_leaderboard

# POINT_VALUES:
# task_completed=10, task_validated=25, feature_shipped=50
# bug_found_critical=30, bug_fixed=20, review_approved=15
# document_produced=10, insight_actioned=35

add_points("dev_app", "feature_shipped", note="Landing v2")
scores = get_scores()       # dict agent_id → int
board  = get_leaderboard()  # list triée + rank + milestone_status
```

Milestones : 100=coffee_break | 200=tier_upgrade_7d | 500=tier_upgrade_30d

---

## Ajouter un nouvel agent — checklist 6 étapes

1. `agents/my_agent.py` — SYSTEM_PROMPT en 5 sections (identité/spécialités/méthode/format/qualité)
2. `config/agent_models.py` — ajouter tier dans `AGENT_TIERS`
3. `config/agent_personas.py` — ajouter dans `AGENT_PERSONAS`, `ROOMS`, `TEAMS` si compétitif
4. `api/schemas.py` — ajouter les Pydantic models
5. `api/routers/agents_pole.py` — ajouter les endpoints
6. `web/src/components/settings/model-settings-view.tsx` — ajouter dans `AGENT_LABELS`

---

## MCP Server — ALNUA comme outil Cursor natif

`fastapi-mcp` est monté via `mount_http()` dans `api/app.py`. Le fichier `.cursor/mcp.json` (project-level) configure 6 MCPs :

```json
{
  "mcpServers": {
    "context7":     { "command": "npx", "args": ["-y", "@upstash/context7-mcp@latest"] },
    "n8n":          { "url": "https://alnua.app.n8n.cloud/mcp-server/http" },
    "github":       { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-github@latest"],
                      "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "${env:GITHUB_TOKEN}" } },
    "browser-tools":{ "command": "npx", "args": ["-y", "@agentdeskai/browser-tools-mcp@latest"] },
    "alnua-hub":    { "url": "http://localhost:8000/mcp", "headers": { "X-Hub-Key": "${env:HUB_API_KEY}" } },
    "godot":        { "command": "npx", "args": ["-y", "godot-mcp@latest"],
                      "env": { "GODOT_PROJECT_PATH": "${env:GODOT_PROJECT_PATH}" } }
  }
}
```

Variables d'env requises : `GITHUB_TOKEN`, `HUB_API_KEY` (optionnel en `ENVIRONMENT=development`), `GODOT_PROJECT_PATH` (optionnel).
Guide de setup complet : `MCP_CURSOR_SETUP.md`

Cursor peut alors appeler directement `POST /agents/analyst-data/sql` etc. comme outils MCP sans passer par HTTP manuellement.

---

## Skills Cursor disponibles (`.claude/skills/`)

| Skill | Usage |
|-------|-------|
| `/alnua-hub` | Architecture complète (à invoquer en début de session) |
| `/alnua-agents` | Cheat sheet 20 agents + endpoints |
| `/alnua-new-agent` | Template + checklist création agent |
| `/alnua-caveman` | Mode compression tokens |
| `/alnua-test` | Patterns Playwright + stratégie tests |
| `/alnua-parallel` | Exécution parallèle agents |
| `/alnua-router` | Routeur LLM dynamique |
| `/alnua-n8n` | Intégration n8n — workflows, webhooks, triggers |
| `/alnua-godot` | Godot 4 + Nova (dev_gaming) + godot-mcp |
| `/alnua-prose` | Règles anti-slop pour Sofia (Content) + Camille (Marketing) |
| `/alnua-prd` | Template PRD complet — brief → Léon → Sam → COO |
| `/alnua-frontend` | Checklist P0/P1/P2 pour Théo (dev_app) — Next.js |
| `/alnua-search` | Protocole recherche pour Idris + Alex — citations + confiance |
| `/alnua-trae` | 11 patterns de code ALNUA — FastAPI, agents, Supabase, Next.js |
| `/alnua-memory` | Guide Mem0 complet — lire/écrire/compresser mémoire agents |
| `/alnua-devops` | Docker + CI/CD + deploy Railway/Render du Hub |

---

## Règles invariantes — NE JAMAIS VIOLER

- **Pas d'UE5** — aucune intégration Unreal Engine dans aucun agent
- `parse_json_response()` sur **tout** output LLM — gère les markdown fences
- `log_agent_action()` obligatoire sur chaque méthode principale
- `@trace_agent("agent_name")` sur chaque méthode publique
- Dégradé silencieux partout (`try/except pass`) sauf l'appel LLM principal
- `from api.route_common import *` — ne jamais dupliquer les imports dans les routers
- `data/agent_scores.json` créé automatiquement — ne jamais le committer avec des données
