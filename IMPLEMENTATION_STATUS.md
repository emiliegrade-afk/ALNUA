# Implementation Status — ALNUA Hub

> Reconstitué le 2026-07-25 lors du bootstrap de gouvernance. Vue d'ensemble
> "implémenté vs planifié vs gap" — le détail agent-par-agent exhaustif reste dans
> `CLAUDE.md` (source de vérité pour room/team/tier), pas dupliqué ici.

## Cœur du Hub

| Domaine | Status | Notes |
|---------|--------|-------|
| API FastAPI (35 routers) | ✅ Implémenté | `api/routers/__init__.py::ALL_ROUTERS` |
| 27 agents personas (9 poles) | ✅ Implémenté | Voir tableau complet dans `CLAUDE.md` |
| Orchestration CrewAI | ✅ Implémenté | Tâches multi-agents complexes |
| Système compétition (points/leaderboard) | ✅ Implémenté | `services/competition.py` |
| Routeur LLM dynamique (tier fast/standard/premium) | ✅ Implémenté | `services/llm_router.py` |
| Spec adversariale (debate LLM) | ✅ Implémenté | `services/adversarial_spec.py` |
| Parallel runner v2 (retry, depends_on, progress) | ✅ Implémenté | `services/parallel_runner.py` |
| Pipeline contenu multi-plateformes | ✅ Implémenté | `services/content_pipeline.py` |
| Radar tendances (HN/Reddit/GitHub) | ✅ Implémenté | `services/trend_monitor.py` |
| Recherche profonde multi-rounds | ✅ Implémenté | `services/deep_research.py` |
| Executor de plans COO | ✅ Implémenté | `services/plan_executor.py` |
| Graphe codebase (AST Python) | ✅ Implémenté | `services/code_graph.py` |
| Apprentissage + compression mémoire (Mem0) | ✅ Implémenté | `skills/skill_agent_learning.py` |
| Suivi coûts LLM | ✅ Implémenté | `services/cost_monitor.py`, étendu à ElevenLabs + hosting (2026-07-24) |
| A/B test prompts/agents | ✅ Implémenté | `services/a_b_tester.py` |
| Bus d'événements inter-agents | ✅ Implémenté | `services/event_bus.py` |
| Briefing quotidien COO | ✅ Implémenté | `services/daily_briefing.py` |
| MCP Server (`fastapi-mcp` sur `/mcp`) | ✅ Implémenté | Protégé par `X-Hub-Key` |

## Centre R&D (dossier hub)

| Phase | Status | Référence |
|-------|--------|-----------|
| Idées auto-scorées (Centre R&D initial) | ✅ Implémenté | `services/rnd_pipeline.py` |
| Dossier structuré (sections, statuts, business case) | ✅ Implémenté | `services/rnd_repository.py`, `rnd_schemas.py` |
| Comité multi-agents en langage naturel | ✅ Implémenté | `agents/rnd_committee_agent.py` + prompts |
| Dossier visuel illustré + deck PDF | ✅ Implémenté | `services/rnd_deck_generator.py`, `rnd_visual_generator.py` |
| Pipeline social teasers → posts | ✅ Implémenté | `agents/rnd_social_agent.py` |
| Validation CEO → dispatch multi-pôles | ✅ Implémenté | `services/rnd_dispatch_executor.py`, `rnd_dispatch_playbooks.py` |
| Fiche produit / waitlist | ✅ Implémenté | `agents/rnd_product_agent.py`, `services/waitlist.py` |
| Estimation finance/pricing | ✅ Implémenté | `services/rnd_finance_estimate.py`, `rnd_pricing_model.py` |
| Arbre d'hypothèses | ✅ Implémenté | `services/rnd_hypothesis_tree.py` |

## Frontend (`web/`)

| Zone | Status | Notes |
|------|--------|-------|
| Dashboard v3 — lobby + bureaux par département | ✅ Implémenté | Next.js 14 |
| OpenRoom (war room visuelle, avatars live) | ✅ Implémenté | |
| Page Comptabilité — coûts combinés | ✅ Implémenté | 2026-07-24 |
| Jalons à venir (Google Calendar) | ✅ Implémenté | 2026-07-24 |
| Page Admin Costs | 🔄 Implémenté, **désactivé par défaut** | `ADMIN_COSTS_PAGE_ENABLED=false` |
| Page Admin Events | 🔄 Implémenté, **désactivé par défaut** | `ADMIN_EVENTS_PAGE_ENABLED=false` |
| Page Admin A/B Test | 🔄 Implémenté, **désactivé par défaut** | `ADMIN_AB_TEST_PAGE_ENABLED=false` |
| Onglet exécutif COO sur `/briefing` | 🔄 Implémenté, **désactivé par défaut** | `BRIEFING_COO_SECTION_ENABLED=false` |
| GDD Manager (router + endpoints) | 🔄 Implémenté, **désactivé par défaut** | `GDD_MANAGER_ENABLED=false` — c'est pourquoi `gdd.py` est monté conditionnellement |

> Ces 5 fonctionnalités sont codées et testées (flags forcés à `1` dans le job e2e de
> la CI) mais restent **éteintes par défaut** en prod tant que non activées
> explicitement — à vérifier avec Emilie si c'est intentionnel (rollout progressif) ou
> un oubli d'activation.

## Intégrations externes

| Intégration | Status | Notes |
|-------------|--------|-------|
| Supabase (DB + auth + RLS) | ✅ Implémenté | |
| OpenRouter (LLM) | ✅ Implémenté | |
| Mem0 (mémoire agents) | ✅ Implémenté | |
| Langfuse (tracing) | ✅ Implémenté | |
| n8n (workflows externes) | ✅ Implémenté | |
| Composio (OAuth 250+ APIs) | ✅ Implémenté | TWITTER/WORDPRESS retirés de la app map (commit `cf9e9f9`) |
| Discord / Telegram bots | ✅ Implémenté | Fallback gracieux si token/channel absent |
| ElevenLabs (voix, coûts) | ✅ Implémenté | |
| Godot 4 (`godot-mcp`) | ✅ Implémenté | Skill `.claude/skills/alnua-godot/` |
| Nwiro/UE5 (`skill_nwiro.py`) | ⚠️ Code présent, **statut produit non tranché** | Contredit la règle "Pas d'UE5" de `CLAUDE.md` — voir `DECISIONS.md` DEC-009 |

## Gap connu (pas un audit exhaustif — juste ce qui saute aux yeux)

- **Gouvernance** : jusqu'au 2026-07-25, aucun des 8 fichiers de gouvernance standard
  n'existait pour ce projet (contrairement à `NAÏA/`, `NUAWAY/`, `RESONANCE/`) — comblé
  par ce bootstrap.
- **Nwiro/UE5** : voir ci-dessus, décision produit en attente.
- Le reste des gaps potentiels (sécurité, qualité de code) est dans `BUGS.md`, alimenté
  par l'audit mené en parallèle de ce bootstrap.
