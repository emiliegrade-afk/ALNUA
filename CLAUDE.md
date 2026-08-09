# ALNUA Hub — Cursor Briefing Complet

> Lis ce fichier en entier avant de toucher au code. Il décrit l'état exact du projet, ce qui a été construit récemment, et les patterns à respecter absolument.

---

## Stack technique

| Couche | Tech |
|--------|------|
| API REST | FastAPI — entry: `api/main.py` → `api/app.py` → `api/routers/` |
| Frontend | Next.js **16** (`web/`) — `npm run build:safe` si `next dev` écrit déjà `.next` ; lint via `eslint .` (plus de `next lint`) |
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
    agents_pole.py    ← endpoints agents (secretary, dev-backend, level-designer,
                         controller, analyst-business, analyst-data + anciens) —
                         entrées libres passées aux LLM assainies via
                         services/input_sanitizer.py (services/input_sanitizer.py::sanitize_user_input,
                         PII redaction désactivée ici — ces endpoints véhiculent
                         volontairement des données business réelles)
    competition.py    ← GET/POST /agents/scores, /agents/leaderboard
    advanced_services.py ← endpoints LLM router, adversarial spec, parallel runner
    core.py           ← endpoints principaux (COO, PM, QA, spec...)
    [+ routers supplémentaires (**41** au total dans ALL_ROUTERS + `gdd.py` conditionnel, dont `ue58_bridge`) — cf. `api/routers/__init__.py::ALL_ROUTERS` pour la liste exhaustive à jour]
```

**Règle invariante :** chaque router commence par `from api.route_common import *` — ne jamais dupliquer les imports.

**Montage unique :** `register_routers()` monte chaque router **une seule fois** (pas de préfixe `/v1` en plus — ça dupliquait les `operation_id` OpenAPI et risquait des collisions d'outils `fastapi-mcp`). Ne pas réintroduire un double montage.

---

## 49 agents ALNUA (34 existants + 15 rôles spécialisés Gaming/Robotique — Phase 13, ROADMAP.md)

> Source de vérité pour room/team/tier : `config/agent_personas.py` (`AGENT_PERSONAS`, `ROOMS`, `TEAMS`) + `config/agent_models.py` (`AGENT_TIERS`). Cette table est une vue de lecture — en cas de divergence, ce sont ces deux fichiers qui font foi, pas ce document.

### Direction (`direction`)
| Agent ID | Fichier | Persona | Tier |
|----------|---------|---------|------|
| `coo` | `agents/coo_agent.py` | Aria Voss — COO | premium |
| `spec` | `agents/spec_agent.py` | Léon Marchand — Spec | fast |
| `qa` | `agents/qa_agent.py` | Alex Okafor — QA | standard |
| `pm` | `agents/pm_agent.py` | Sam Rivera — PM | standard |

> Note : `agents/coo_agent.py` a `AGENT_NAME = "coo_agent"` en interne (pas `"coo"`), sans alias dans `AGENT_ID_ALIASES` (`config/agent_models.py`) contrairement aux autres agents en `_agent`. Historique connu, pas encore corrigé — vérifier avant de router dynamiquement sur cet agent_id.

### App Office (`app_office`) — Équipe `app`
| Agent ID | Fichier | Persona | Tier |
|----------|---------|---------|------|
| `dev_app` | `agents/dev_app_agent.py` | Théo Laurent | standard |
| `dev_backend` | `agents/dev_backend_agent.py` | Hao Chen | standard |
| `dev_frontend` | `agents/dev_frontend_agent.py` | Inès Moreau — UI Hub | standard |
| `dev_integrator` | `agents/dev_integrator_agent.py` | Rayan Kone — merge & integration | standard |
| `coding_coach` | `agents/coding_coach_agent.py` | Luca Bernard — mentor CEO, non compétitif | fast |
| `rnd_product` | `agents/rnd_product_agent.py` | Naïm Tessier — fiche produit R&D | standard |

### Gaming Studio (`gaming_studio`) — Équipe `gaming`
| Agent ID | Fichier | Persona | Tier |
|----------|---------|---------|------|
| `game_director` | `agents/game_director_agent.py` | Mira Chen | premium |
| `dev_gaming` | `agents/dev_gaming_agent.py` | Nova Fischer | standard |
| `level_designer` | `agents/level_designer_agent.py` | Finn Larsen | fast |
| `ai_programmer` | `agents/ai_programmer_agent.py` | Kenji Sato — IA comportementale | standard |
| `environment_artist` | `agents/environment_artist_agent.py` | Priya Nandan | standard |
| `technical_artist` | `agents/technical_artist_agent.py` | Otto Reindl | standard |
| `narrative_designer` | `agents/narrative_designer_agent.py` | Sable Winters | standard |
| `vfx_artist` | `agents/vfx_artist_agent.py` | Diego Salas | standard |
| `sound_designer` | `agents/sound_designer_agent.py` | Ingrid Halvorsen | standard |
| `qa_gaming` | `agents/qa_gaming_agent.py` | Tomás Freitas — QA gameplay | standard |

### R&D Lab (`rnd_lab`) — Équipe `innovation`
| Agent ID | Fichier | Persona | Tier |
|----------|---------|---------|------|
| `brainstorm` | `agents/brainstorm_agent.py` | Idris Okonkwo | premium |
| `rnd_agent` | `agents/rnd_agent.py` | Alex Mercer | premium |
| `rnd_dossier` | `agents/rnd_dossier_agent.py` | Iris Coste — assemblage dossier | premium |
| `rnd_ceo` | `agents/rnd_ceo_agent.py` | Noé Fabre — package CEO | premium |
| `rnd_committee` | `agents/rnd_committee_agent.py` | Cléo Vasseur — facilite le comité, non compétitive | premium |

### Comms Hub (`comms_hub`) — Équipe `business`
| Agent ID | Fichier | Persona | Tier |
|----------|---------|---------|------|
| `marketing` | `agents/marketing_agent.py` | Camille Rousseau | standard |
| `content` | `agents/content_agent.py` | Sofia Reyes | standard |
| `content_app` | `agents/content_app_agent.py` | Esmée Diallo — contenu App | standard |
| `content_gaming` | `agents/content_gaming_agent.py` | Kael Vex — contenu Gaming | standard |
| `content_robo` | `agents/content_robo_agent.py` | Mira Solberg — contenu Robotique | standard |
| `content_company` | `agents/content_company_agent.py` | Anouk Gerard — marque ALNUA | standard |
| `rnd_social` | `agents/rnd_social_agent.py` | Léa Fontaine — stratégie sociale dossier | standard |
| `rnd_visual` | `agents/rnd_visual_agent.py` | Max Delacroix — moodboard & brand dossier | standard |
| `ads` | `agents/ads_agent.py` | Léo Morel — publicité payante (Meta, Google, TikTok) | standard |

### Accounting Office (`accounting_office`) — Équipe `finance`
| Agent ID | Fichier | Persona | Tier |
|----------|---------|---------|------|
| `accounting` | `agents/accountant_agent.py` | Jules Bernard | fast |
| `controller` | `agents/controller_agent.py` | Rémi Chassagne | fast |

### Hardware Workshop (`hardware_workshop`) — Équipe `robo`
| Agent ID | Fichier | Persona | Tier |
|----------|---------|---------|------|
| `hardware` | `agents/hardware_agent.py` | Yuki Tanaka | fast |
| `embedded_dev` | `agents/embedded_dev_agent.py` | Zara Singh | fast |
| `vision_ai` | `agents/vision_ai_agent.py` | Sana Okoye — perception embarquée | standard |
| `electronics` | `agents/electronics_agent.py` | Marco Ferreira | standard |
| `firmware` | `agents/firmware_agent.py` | Petra Vogel | standard |
| `mechanical` | `agents/mechanical_agent.py` | Ravi Chandrasekaran | standard |
| `industrial_design` | `agents/industrial_design_agent.py` | Elin Bergström | standard |
| `qa_robot` | `agents/qa_robot_agent.py` | Bilal Nasser | standard |
| `safety` | `agents/safety_agent.py` | Clara Dubois | standard |
| `simulation` | `agents/simulation_agent.py` | Haruto Ishikawa | standard |

### Analytics Room (`analytics_room`) — Équipe `analytics`
| Agent ID | Fichier | Persona | Tier |
|----------|---------|---------|------|
| `analyst_business` | `agents/analyst_business_agent.py` | Layla Hassan | standard |
| `analyst_data` | `agents/analyst_data_agent.py` | Axel Roux | standard |

### Sans room fixe
| Agent ID | Fichier | Persona | Tier |
|----------|---------|---------|------|
| `secretary` | `agents/secretary_agent.py` | Nadia Faure | standard |

Agents infra/orchestrateurs sans `AGENT_NAME` persona (pas dans `AGENT_PERSONAS`, pas de compétition) : `agents/rnd_center.py` (orchestrateur Centre R&D), `agents/bug_watchdog.py` (boucle de surveillance, délègue à `agents/fix_pipeline.py`), `agents/project_scanner.py`, `agents/skill_synthesizer.py`, `agents/brand_agent.py`.

---

## Pattern agent — règle de création

Depuis la migration "9-layer operating specs" (commit `1a46408`), les agents héritent de `agents/agent_base.py::AgentBase` (18+ agents) plutôt que de gérer `db`/`llm` à la main. `AgentBase.__init__` fixe déjà `self.db` et `self.llm` — **si une sous-classe redéfinit `__init__`, elle doit appeler `super().__init__()`** (oubli réel corrigé sur `rnd_dossier_agent`/`rnd_committee_agent` : `self.db` restait `None`, `self._log()` aurait levé `AttributeError` au premier appel).

```python
"""[Role] Agent — [Prénom Nom], [Titre] ALNUA."""
from __future__ import annotations
from agents.agent_base import AgentBase

from typing import Any
from agents.base import log_agent_action, parse_json_response
from config.agent_operating_spec import get_system_prompt
from skills.skill_agent_learning import inject_learning_context, record_task_learning
from skills.skill_langfuse import trace_agent

class MyAgent(AgentBase):
    AGENT_NAME = "my_agent"

    SYSTEM_PROMPT = get_system_prompt("my_agent")  # 9-layer spec — config/agent_operating_spec.py

    # Si __init__ est redéfini (ex: pour injecter un repo), appeler super().__init__() en premier :
    # def __init__(self, repo=None) -> None:
    #     super().__init__()
    #     self.repo = repo or get_my_repository()

    @trace_agent("my_agent")
    def my_method(self, param: str) -> dict[str, Any]:
        prompt = inject_learning_context(f"...", self.AGENT_NAME, param)
        raw = self._complete(prompt, temperature=0.4)  # self.llm_agent_id résolu automatiquement
        result = parse_json_response(raw)
        log_agent_action(self.db, self.AGENT_NAME, "my_method",
            input_summary=param[:100], output_summary=str(result)[:100])
        try:
            record_task_learning(self.AGENT_NAME, "my_method", str(result)[:300], success=True)
        except Exception:
            pass
        return result
```

`AgentBase` fournit aussi `_complete_async`, `llm_agent_id` (normalise `xxx_agent`→`xxx` pour le routage modèle/coûts), `memory_agent_id` (clé Mem0), et `_log(...)` (wrapper `log_agent_action`, actuellement non utilisé par les agents existants qui appellent encore `log_agent_action(...)` directement — les deux sont valides, `_log` est juste plus court).

Le SYSTEM_PROMPT en 5 sections inline (identité/spécialités/méthode/format/qualité) reste valide pour un agent simple, mais la majorité des agents actuels le génèrent via `get_system_prompt(agent_id)` (`config/agent_operating_spec.py`) — un système de spec en 9 couches plus riche. Vérifier lequel des deux patterns est déjà utilisé par les agents voisins avant d'en créer un troisième.

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
`get_library_context` injecte le **catalogue de sujets** (pas des résumés tronqués) et peut `learn_topic` automatiquement pour les hits `now`.

### `skills/skill_library_memory.py` + vault Obsidian — Mémoire bibliothèque hybride
- Export : `python scripts/export_library_to_vault.py` → notes `library/{bureau}/*.md` + `data/topic_catalog.json` + `library/_index/TOPICS.md`
- `scan_library_topics` / `learn_topic` / `ensure_topic_digest` — apprentissage à la demande
- API : `GET /library/topics`, `POST /library/topics/{slug}/learn`, `POST /library/vault/sync`
- Chroma collection `alnua_library` ; knowledge skills dans `skills/knowledge/` si sujet récurrent
- Doc vault : `_index/LIBRARY_MEMORY.md`

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

## Ajouter un nouvel agent — checklist 7 étapes

1. `agents/my_agent.py` — hérite de `agents/agent_base.py::AgentBase`, `SYSTEM_PROMPT` via `get_system_prompt(agent_id)` (`config/agent_operating_spec.py`) ou 5 sections inline
2. `config/agent_specs_registry.py` — si `SYSTEM_PROMPT` utilise `get_system_prompt(agent_id)`, ajouter l'`AgentOperatingSpec` correspondant — **sans cette étape, `get_system_prompt()` lève `KeyError` au premier appel** (le fallback "5 sections inline" de l'étape 1 n'a pas ce problème)
3. `config/agent_models.py` — ajouter tier dans `AGENT_TIERS` + alias `mon_agent_agent` → `mon_agent` dans `AGENT_ID_ALIASES`
4. `config/agent_personas.py` — ajouter dans `AGENT_PERSONAS`, `ROOMS`, `TEAMS` si compétitif — **sans cette étape, `get_competitive_context()` ne s'applique jamais à l'agent** (arrivé aux 6 agents R&D dossier hub, resté non détecté plusieurs semaines)
5. `api/route_common.py` (import de la classe) + `api/schemas.py` (Pydantic models) + `api/routers/agents_pole.py` (ou routeur dédié, endpoints) — toute entrée texte libre destinée à un LLM passe par `services/input_sanitizer.py::sanitize_user_input` côté router
6. Rien à faire côté `web/src/components/settings/model-settings-view.tsx` — il lit déjà `display_name`/`role_label` depuis `GET` du backend (`config/agent_models.py::get_all_agent_models()` → `_agent_display()` → `AGENT_PERSONAS`), donc l'étape 3 suffit à le peupler (vérifié Phase 13, ROADMAP.md — l'ancienne référence à un `AGENT_LABELS` frontend codé en dur ne correspond plus au code)
7. `web/src/lib/agent-bureau.ts::BUREAU_AGENTS` — ajouter l'agent si un roster de département (`/app`, `/gaming`, `/robo`...) doit l'afficher comme carte réelle plutôt que "poste vacant"

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

Variables d'env requises : `GITHUB_TOKEN`, `HUB_API_KEY` (obligatoire dans tous les environnements depuis SEC-002, voir `BUGS.md`/`DECISIONS.md` — plus de mode dev ouvert), `GODOT_PROJECT_PATH` (optionnel).
Guide de setup complet : `MCP_CURSOR_SETUP.md`

Cursor peut alors appeler directement `POST /agents/analyst-data/sql` etc. comme outils MCP sans passer par HTTP manuellement.

---

## Skills Cursor disponibles (`.claude/skills/`)

| Skill | Usage |
|-------|-------|
| `/alnua-hub` | Architecture complète (à invoquer en début de session) |
| `/alnua-agents` | Cheat sheet 49 agents + endpoints |
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
| `/alnua-content` | Skills content sectoriel + scheduler social + ads |
| `/alnua-ads` | Publicité payante — Meta/Google/TikTok Ads via Léo |
| `/alnua-devops` | Docker + CI/CD + deploy Railway/Render du Hub |

---

## Règles invariantes — NE JAMAIS VIOLER

- **UE5.8 serveur + agency PC** — pont éditeur = serveur UE5.8 (DEC-017) ; agents Gaming agissent sur le PC via Claude Code / coding pipeline sur `UE_PROJECT_PATH` (DEC-020, `skill_gaming_agency`). Godot optionnel. `skill_nwiro` = legacy. Pas de computer-use GUI Windows total sans nouvelle DEC.
- `parse_json_response()` sur **tout** output LLM — gère les markdown fences
- `log_agent_action()` obligatoire sur chaque méthode principale
- `@trace_agent("agent_name")` sur chaque méthode publique
- Dégradé silencieux partout (`try/except pass`) sauf l'appel LLM principal
- `from api.route_common import *` — ne jamais dupliquer les imports dans les routers
- Chaque router monté **une seule fois** dans `register_routers()` — pas de double-montage `/v1`
- `data/agent_scores.json` créé automatiquement — ne jamais le committer avec des données
- Toute sous-classe de `AgentBase` qui redéfinit `__init__` doit appeler `super().__init__()` en premier (sinon `self.db` reste `None`)
- Nouvel agent compétitif → enregistrement obligatoire dans `config/agent_personas.py` (room/team/persona), sinon la compétition ne s'applique jamais silencieusement
- `ruff check agents/ services/ api/ config/ database/ bots/ skills/` doit passer (bloquant en CI, config `ruff.toml`) — voir ce fichier pour la liste des règles volontairement ignorées (star-imports, style pré-existant) et pourquoi
- Dépendances Python figées en `==` dans `requirements.txt` ; `requirements.lock.txt` = snapshot pip freeze complet pour reproductibilité — mettre à jour les deux en cas d'ajout/upgrade de dépendance
