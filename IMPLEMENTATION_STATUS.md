# Implementation Status — ALNUA Hub

> Reconstitué le 2026-07-25 lors du bootstrap de gouvernance. Resynchronisé le
> 2026-08-09 (Phase A remédiation Audit 002 / BUG-011). Vue d'ensemble
> "implémenté vs planifié vs gap" — le détail agent-par-agent exhaustif reste dans
> `CLAUDE.md` (source de vérité pour room/team/tier), pas dupliqué ici.

## Cœur du Hub

| Domaine | Status | Notes |
|---------|--------|-------|
| API FastAPI (**40** routers + `gdd` conditionnel) | ✅ Implémenté | `ALL_ROUTERS` — Phase D `rnd_trees` ; Phase E `trust` |
| **49** agents personas (9 poles, dont 15 rôles Gaming/Robo Phase 13) | ✅ Implémenté | Voir tableau complet dans `CLAUDE.md` |
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
| Bus d'événements inter-agents | ✅ Implémenté + fan-out MVP | `event_bus` + `cross_dept_handlers` (Phase 36 MVP) ; briefing cross-dept encore à faire |
| Briefing quotidien COO | ✅ Implémenté | `services/daily_briefing.py` |
| Workflow engine (ship/ops/dossier/sav + validation) | ✅ MVP Phase 30 | `workflow_engine` + `workflow_validation_recipes` ; `budget_transfer` encore absent |
| MCP Server (`fastapi-mcp` sur `/mcp`) | ✅ Implémenté | Protégé par `X-Hub-Key` |

## Centre R&D (dossier hub + v2)

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
| R&D v2 — coquille `/rnd-v2` (Phases 22-27) | ✅ Implémenté | Pipeline, Incubateur, Conseil (réceptacle), Arbres, Dossiers |
| R&D v2 — Explorer veille externe (Phase 28) | ✅ Vague E | `rnd_explorer` + onglet Explorer `/rnd-v2` |
| Brand design system (Phase 35) | 🔄 MVP Slice Vague D | tokens + Review Board brand + Brand Center |
| R&D council agent / router | ✅ Implémenté | `agents/rnd_council_agent.py`, `api/routers/rnd_council.py` |

## Marketing & Finances

| Zone | Status | Notes |
|------|--------|-------|
| Marketing Command Center visuel (Phase 29) | ✅ Implémenté | `/marketing-v2` |
| Campagnes + Content Studio (Phase 33) | ✅ Implémenté | `api/routers/campaigns.py` + UI |
| Mesure perf Reach/Engagement/ROI/Funnel (Phase 37) | ✅ Implémenté | `api/routers/marketing_funnel.py` + saisie manuelle (DEC-014) |
| Finance Cockpit visuel (Phase 29) | ✅ Implémenté | `/finances-v2` (onglets de base) |
| Finance profondeur — invoices / SaaS / Revolut (Phase 34 / DEC-016) | ✅ Backend + UI | API + `SaasInvoicesPanel` + KPI à payer |
| Budgets / obligations fiscales (Phase 34 / Vague 3) | ✅ JSON + UI | `/finances/budgets` + `/finances/fiscal-obligations` + onglet « Budgets & Fiscal » ; pas de paiement/transfert auto ; `budget_transfer` reporté |
| Phase 21 skills Gaming/Robo | 🔄 In progress | Vague A/B + DEC-020 : UE5.8, agency Claude Code, probes robo ; Nwiro = legacy DEC-017 |
| Eve sourcing / montage BOM | ✅ | alternatives + assembly-plan + infra-blueprint + UI `/robo` ; Pi différable (DEC-018) |
| Finance cockpit forecast (Vague C) | ✅ | `GET /finances/cockpit-forecast` + UI Budgets/Fiscal ; `budget_transfer` reporté |
| Review Board LLM (flag) | ✅ Optionnel | `REVIEW_BOARD_LLM` → `review_board_llm.py` ; défaut = structural |
| Daily briefing cross-dept | ✅ Branché | `_collect_cross_dept` dans `daily_briefing.py` |

## Frontend (`web/`)

| Zone | Status | Notes |
|------|--------|-------|
| Dashboard v3 — lobby + bureaux par département | ✅ Implémenté | Next.js 16.3.0 |
| Agent Trust UI (`/trust`) | ✅ MVP | Vague 1 — `GET /agents/trust` + jauges DEC-011 |
| OpenRoom (war room visuelle, avatars live) | ✅ Implémenté | |
| Page Comptabilité — coûts combinés | ✅ Implémenté | 2026-07-24 |
| Jalons à venir (Google Calendar) | ✅ Implémenté | 2026-07-24 |
| Page Admin Costs | 🔄 Implémenté, **désactivé par défaut** | `ADMIN_COSTS_PAGE_ENABLED=false` |
| Page Admin Events | 🔄 Implémenté, **désactivé par défaut** | `ADMIN_EVENTS_PAGE_ENABLED=false` |
| Page Admin A/B Test | 🔄 Implémenté, **désactivé par défaut** | `ADMIN_AB_TEST_PAGE_ENABLED=false` |
| Onglet exécutif COO sur `/briefing` | 🔄 Implémenté, **désactivé par défaut** | `BRIEFING_COO_SECTION_ENABLED=false` |
| GDD Manager (router + endpoints) | 🔄 Implémenté, **désactivé par défaut** | `GDD_MANAGER_ENABLED=false` — `gdd.py` monté conditionnellement |
| Redesign UI départements App/Gaming/Robo | ✅ Implémenté | `web/src/app/{app,gaming,robo}-v2/` — `/app`, `/gaming`, `/robo` ré-exportent vers `-v2` |
| Real-data Gaming/Robo (builds, assets, labo, télémétrie, communauté) | ✅ Implémenté (réceptacle) | Phases 15-20 — pas de pipeline UE5/Steam/robot physique derrière |
| Harmonisation visuelle MockupShell (Phase 38) | ✅ Rendu + routes reconnectées | Toutes routes primaires live (dont `/hub` `/analytics` `/ceo` `/secretary` `/brand`). Mockups sous `components/mockup/` pour preview design uniquement. |

> Les 5 features admin/GDD/briefing COO sont codées et testées (flags forcés à `1`
> dans le job e2e CI) mais restent **éteintes par défaut** en prod tant que non
> activées explicitement.

## Intégrations externes

| Intégration | Status | Notes |
|-------------|--------|-------|
| Supabase (DB + auth + RLS) | ✅ Implémenté | |
| OpenRouter (LLM) | ✅ Implémenté | Prompt cache + retries (DEC-015) |
| Mem0 (mémoire agents) | ✅ Implémenté | |
| Langfuse (tracing) | ✅ Implémenté | |
| n8n (workflows externes) | ✅ Implémenté | |
| Composio (OAuth 250+ APIs) | ✅ Implémenté | TWITTER/WORDPRESS retirés de la app map (commit `cf9e9f9`) |
| Discord / Telegram bots | ✅ Implémenté | Fallback gracieux si token/channel absent |
| ElevenLabs (voix, coûts) | ✅ Implémenté | |
| Godot 4 (`godot-mcp`) | ✅ Implémenté | Skill `.claude/skills/alnua-godot/` |
| Pont Gaming UE5.8 (`skill_ue58` + agency) | ✅ Vague A + DEC-020 | Nwiro = legacy (`skill_nwiro`) ; Godot optionnel (DEC-017) |
| Sentry / security-ingest (Résonance) | ✅ Implémenté | Ops 2026-08-08 |
| Revolut Business (lecture) | 🔄 Branché API | DEC-016 — credentials requis |

## Planifié (ROADMAP — suite MVP / hygiène)

| Phase | Objectif |
|-------|---------|
| 21 | Suite skills Gaming/Robo (UE_PROJECT_PATH + Pi + serveur UE5.8 studio) |
| 30 | Suite : `budget_transfer` (reporté DEC-016) + UI workflows |
| 32 | Suite : débat LLM Review Board multi-personas (flag `REVIEW_BOARD_LLM` ✅) |
| 35 | Suite Brand : persona multi-room + débat LLM (MVP Vague D ✅) |
| Audit 005 | Santé 10 dimensions ≤ **2026-08-30** |

## Gap connu (pas un audit exhaustif)

- **Gouvernance drift** : resync Vague F (2026-08-10) — 44 routers, 433 tests
  collectés, Next 16.3.0 ; Audit 005 toujours dû ≤ 2026-08-30.
- **Real-data Gaming/Robo (Phases 15-20)** : réceptacle honnête ; pont UE5.8 /
  agency prêts, dépendent de la config studio / `UE_PROJECT_PATH`.
- **Academy** : pipeline corrigé (BUG-008) ; risque OpenRouter 402 (crédits) toujours
  possible.
- **Dette structurelle :** ~74 fichiers Python >300 lignes (hotspots
  `api/schemas.py`, `rnd.py`, `skill_coding_agent.py`…) — split ciblé seulement
  si on y touche ; BUG-004 façades fermé.
