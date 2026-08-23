# Implementation Status — ALNUA Hub

> Reconstitué le 2026-07-25 lors du bootstrap de gouvernance. Resynchronisé le
> 2026-08-09 (Phase A remédiation Audit 002 / BUG-011). Vue d'ensemble
> "implémenté vs planifié vs gap" — le détail agent-par-agent exhaustif reste dans
> `CLAUDE.md` (source de vérité pour room/team/tier), pas dupliqué ici.

## Cœur du Hub

| Domaine | Status | Notes |
|---------|--------|-------|
| API FastAPI (**40** routers + `gdd` conditionnel) | ✅ Implémenté | `ALL_ROUTERS` — Phase D `rnd_trees` ; Phase E `trust` |
| **50** agents personas (9 poles, dont 15 rôles Gaming/Robo Phase 13 + Brand) | ✅ Implémenté | Voir tableau complet dans `CLAUDE.md` |
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
| Bus d'événements inter-agents | ✅ Depth+ | `event_bus` + `cross_dept_handlers` + `cross_dept_drain` (Phase 36) |
| Briefing quotidien COO | ✅ Implémenté | `services/daily_briefing.py` |
| Workflow engine (ship/ops/dossier/sav + validation) | ✅ Complete | Phase 30 Vague 2 — UI `/hub` + `/ceo` ; `budget_transfer` hors scope DEC-032 |
| Agent Trust (Phase 31) | ✅ Complete | DEC-032 — MVP `/trust` accepté |
| Review Board + gates (Phase 32) | ✅ Complete | DEC-032 — structural + LLM optionnel |
| Finance Depth+ (Phase 34) | ✅ Complete | sans `budget_transfer` (DEC-032) |
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
| Brand design system (Phase 35) | ✅ Depth+ | tokens + Review Board + débat Élise↔Anouk + Brand Center |
| R&D council agent / router | ✅ Implémenté | `agents/rnd_council_agent.py`, `api/routers/rnd_council.py` |

## Marketing & Finances

| Zone | Status | Notes |
|------|--------|-------|
| Marketing Command Center visuel (Phase 29) | ✅ Implémenté | `/marketing-v2` |
| Campagnes + Content Studio (Phase 33) | ✅ Implémenté | `api/routers/campaigns.py` + UI |
| Mesure perf Reach/Engagement/ROI/Funnel (Phase 37) | ✅ Implémenté | `api/routers/marketing_funnel.py` + saisie manuelle (DEC-014) |
| Finance Cockpit visuel (Phase 29) | ✅ Implémenté | `/finances-v2` (onglets de base) |
| Finance profondeur — invoices / SaaS / Revolut (Phase 34 / DEC-016) | ✅ Backend + UI | API + `SaasInvoicesPanel` + KPI à payer |
| Budgets / obligations fiscales (Phase 34 / Vague 3) | ✅ JSON + UI | Complete DEC-032 — pas de `budget_transfer` |
| Phase 21 skills Gaming/Robo | ✅ Hub Complete | Live UE/Pi = Vague 8 (fin) ; Nwiro legacy DEC-017 |
| Eve sourcing / montage BOM | ✅ | alternatives + assembly-plan + infra-blueprint + UI `/robo` ; Pi = Vague 8 |
| Finance cockpit forecast (Vague C) | ✅ | `GET /finances/cockpit-forecast` ; transfert auto hors scope DEC-032 |
| Review Board LLM (flag) | ✅ Optionnel | `REVIEW_BOARD_LLM` → `review_board_llm.py` ; défaut = structural |
| Daily briefing cross-dept | ✅ Branché | `_collect_cross_dept` dans `daily_briefing.py` |

## Frontend (`web/`)

| Zone | Status | Notes |
|------|--------|-------|
| Dashboard v3 — lobby + bureaux par département | ✅ Implémenté | Next.js 16.3.0 |
| Agent Trust UI (`/trust`) | ✅ Complete | DEC-032 — jauges + Review Board + cross-dept drain |
| Agent Lounge (`/lounge`, ex-OpenRoom) | ✅ Complete | Phase 46 / DEC-031 ; `/openroom` redirect |
| Page Comptabilité — coûts combinés | ✅ Implémenté | 2026-07-24 |
| Jalons à venir (Google Calendar) | ✅ Implémenté | 2026-07-24 |
| Page Admin Costs | 🔄 Implémenté, **désactivé par défaut** | `ADMIN_COSTS_PAGE_ENABLED=false` |
| Page Admin Events | 🔄 Implémenté, **désactivé par défaut** | `ADMIN_EVENTS_PAGE_ENABLED=false` |
| Page Admin A/B Test | 🔄 Implémenté, **désactivé par défaut** | `ADMIN_AB_TEST_PAGE_ENABLED=false` |
| Onglet exécutif COO sur `/briefing` | ✅ Flag on (local/prod example) | `BRIEFING_COO_SECTION_ENABLED=1` dans `.env` / deploy examples ; UI gated via `/admin/flags` |
| GDD Manager (router + endpoints) | 🔄 Implémenté, **désactivé par défaut** | `GDD_MANAGER_ENABLED=false` — `gdd.py` monté conditionnellement |
| Redesign UI départements App/Gaming/Robo | ✅ Implémenté | `web/src/app/{app,gaming,robo}-v2/` — `/app`, `/gaming`, `/robo` ré-exportent vers `-v2` |
| Real-data Gaming/Robo (builds, assets, labo, télémétrie, communauté) | ✅ Hub-side 100 % | Phases 15-21 — last known API ou « — » / Non configuré ; live UE/Pi = env externe |
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

## Planifié (ROADMAP — suite Hub 100 % logiciel, DEC-032)

| Vague | Objectif | Statut |
|-------|---------|--------|
| 0 | DEC-032 critères 100 % | ✅ |
| 1 | Clôture doc ROADMAP / status | ✅ |
| 2 | Phase 30 UI workflows → ✅ | ✅ |
| 3 | Phase 39 idle polish → ✅ | ✅ |
| 4 | Anti-mensonge résiduel | ✅ |
| 5 | Dette fichiers >300 | ✅ |
| 6 | Apps NAÏA/NUAWAY coding | ⏸️ |
| 7 | Audit 005 | ⏸️ |
| 8 (fin) | Pi / UE5.8 / Revolut / ads OAuth | ⏸️ |

## Gap connu (pas un audit exhaustif)

- **Plan 100 % (DEC-032) :** rester = Vagues 6–7 ; fin = Vague 8 (externe).
- **Gouvernance :** Audit 005 dû ≤ 2026-08-30 ; Next 16.3.0.
- **Live studio Gaming/Robo :** Hub-side ✅ ; `UE_PROJECT_PATH` / `PI_HOST` = Vague 8.
- **Academy :** pipeline OK ; risque OpenRouter 402 possible.
- **Dette structurelle :** Python packages **0** fichier ≥300 (Vague 5) ; front TS encore gros (hors critère packages).
- **Revolut / ads OAuth :** code prêt ou hors scope — credentials = Vague 8.
