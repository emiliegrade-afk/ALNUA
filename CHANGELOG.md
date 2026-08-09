# Changelog — ALNUA Hub

> Reconstitué rétroactivement le 2026-07-25 depuis `git log` (68 commits, historique
> depuis 2026-06-11) lors du bootstrap de gouvernance. Regroupé par date/thème plutôt
> qu'un commit par ligne — le détail exact reste dans `git log`. À partir de
> maintenant, ajouter une entrée par sprint/lot de changement au fur et à mesure,
> pas en dump différé. **Règle (Audit 002 / Phase A) :** tout merge ou commit
> >500 lignes de diff doit avoir au minimum une bullet dans ce fichier le jour même.

## 2026-08-10 — Debt paydown + bible docs (refactor + docs)

- **Type :** refactor + docs
- **Details :**
  - Docs : racine → 8 fichiers vivants ; specs/guides/plans → `docs/` (bible
    `docs/README.md` + classeur).
  - `api/schemas.py` → façade + modules ≤300.
  - `api/routers/rnd.py` éclaté (`rnd_dossiers`, committee, assets, social, ceo,
    product) — tous ≤300.
  - Liens AGENTS / CLAUDE / rules / audit script mis à jour.

## 2026-08-10 — Vague F : hygiène anti-drift post A–E (docs)

- **Type :** docs / chore
- **Details :**
  - Resync comptes : **44** routers, **433** tests collectés, Next 16.3.0,
    Vitest 35, npm audit 0.
  - IMPLEMENTATION_STATUS / ROADMAP Phase 21–28–35 alignés sur A–E.
  - Entrée `DOC_AUDIT.md` Vague F (Audit 005 toujours ≤ 2026-08-30).
  - Purge check : vault library / brand_kits propres ; pas de split >300.

## 2026-08-10 — Vague E : R&D Explorer veille externe (feat)

- **Type :** feat
- **Details :**
  - `rnd_explorer` — scan HN/Reddit/GitHub + brief labo (Idris).
  - `GET /rnd/explorer/signals`, `POST /rnd/explorer/brief`.
  - Onglet Explorer sur `/rnd-v2` (seed → Pipeline).
  - Tests `test_rnd_explorer.py`.

## 2026-08-10 — Vague D : Brand design system (feat)

- **Type :** feat
- **Details :**
  - `brand_design_system` + voice `content_company` ; recipes Review Board.
  - Router `brand_system` : `GET /brand/design-system`, `POST /brand/review`.
  - Marketing Brand Center branché ; tests `test_brand_design_system.py`.
  - Hors scope : persona multi-room Brand, débat LLM.

## 2026-08-10 — Vague C : Finance cockpit forecast (feat)

- **Type :** feat
- **Details :**
  - `finance_cockpit_forecast` + `GET /finances/cockpit-forecast` /
    `POST /finances/forecast/llm` (Rémi + ledgers réels).
  - Onglet Budgets & Fiscal : stats, kind/échéance, spent, panneau forecast.
  - Tests `test_finance_cockpit_forecast.py`. `budget_transfer` toujours reporté.

## 2026-08-10 — Vague B : probes robotique Phase 21 (feat)

- **Type :** feat
- **Details :**
  - `skills/skill_robo_lab.py` — lab tests + builds (vide honnête).
  - Router `robo_phase21` : BOM mech/industrial, lab QA/safety/sim, Pi vision.
  - Console `/robo` : probes Vague B.
  - Tests `test_robo_phase21.py`.

## 2026-08-10 — DEC-020 : agency Gaming = Claude Code sur le PC (feat)

- **Type :** feat
- **Details :**
  - `skills/skill_gaming_agency.py` — Claude Code / coding pipeline sur
    `UE_PROJECT_PATH` (worktree) pour les agents studio.
  - Endpoints `GET/POST /gaming/studio/agency/*` + `POST /gaming/ue58/tools/call`.
  - Console Gaming : statut agency + formulaire « Lancer sur le PC ».
  - `CODING_AGENT_IDS` : + ai_programmer / technical_artist / vfx_artist.
  - DEC-020 : pas de computer-use GUI Windows total.

## 2026-08-09 — Vague A : pont Hub ↔ UE5.8 (feat)

- **Type :** feat
- **Details :**
  - `SPEC_UE58_BRIDGE.md` + `skills/skill_ue58.py` (health, caps filtrées, chat, GDD).
  - Router `ue58_bridge` : status, probes Kenji/Otto/Diego, chat, gdd/sync.
  - Console Gaming : badge Nwiro → statut UE5.8 via Hub.
  - Tests `test_ue58_bridge.py` ; Nwiro resté legacy.

## 2026-08-09 — P0 décisions : UE5.8, Pi, UI *-v2 (docs)

- **Type :** docs
- **Details :**
  - **DEC-017** — pont Gaming = serveur UE5.8 (chat + GDD + outils) ; Nwiro
    abandonné (DEC-009 superseded) ; Godot reste optionnel.
  - **DEC-018** — Eve Pi différé ; agents via Hub SSH ; WinSCP = humain.
  - **DEC-019** — Finance/Marketing restent `*-v2` ; stash BUG-019 jeté.
  - `budget_transfer` toujours reporté (note DEC-016).
  - `CLAUDE.md` + skill `/alnua-godot` + Phase 21 ROADMAP alignés.

## 2026-08-09 — BUG-004 : split specs / personas / rnd_center (refactor)

- **Type :** refactor
- **Details :**
  - `config/agent_specs_registry.py` et `config/agent_personas.py` → façades +
    modules par pôle (`agent_specs_*.py`, `personas_*.py`) — tous ≤300 lignes.
  - `agents/rnd_center.py` → façade + `rnd_center_{llm,store,observe,pipeline,library}.py`.
  - Tests `test_rnd_library_develop` patchent les modules d’implémentation.
  - BUG-004 fermé (hotspots) ; dette >300 ailleurs notée en backlog hygiène.
  - `ruff` + `pytest` 401 passed / 6 skipped.

## 2026-08-09 — Eve robotics : BOM IA (alternatives, montage, rôles) (feat)

- **Type :** feat
- **Details :**
  - `services/eve_sourcing.py` + endpoints electronics/mechanical/hardware ;
    `GET /robo/pi-bridge` (SSH agents, Pi plus tard OK ; WinSCP = fichiers manuels).
  - UI `/robo` : panneau BOM clair + Alternatives / Plan montage / Qui build quoi.
  - Clarifie : robot physique ≠ app compagnon (`dev_app` comme Naïa).
  - Tests `test_eve_sourcing.py`.

## 2026-08-09 — Vague 4 durabilité : purge orphans + habitudes (chore + docs)

- **Type :** chore + docs + test
- **Details :**
  - Untrack **338** notes vault library (hors `_index/`) + `brand_kits/migration-test`
    déjà gitignorés — plus de dumps dans git.
  - Supprime `skills/coding_facade.py` orphelin ; DEC-008 / BUG-015 mis à jour.
  - Checklist **Habitudes durabilité** dans `AGENTS.md` (audit ≤3 sem., purge,
    ratio tests, vault, worktrees).
  - Tests HTTP budgets/fiscal (`test_finance_budgets_api.py`) — ratio surface Vague 3.
  - Prochain audit santé planifié ≤ **2026-08-30** (après Audit 004).

## 2026-08-09 — Vague 3 produit derrière l'UI : Finance + Phase 21 + MVP honesty (feat)

- **Type :** feat + docs
- **Details :**
  - **3A Finance :** ledgers JSON budgets + fiscal_obligations ; API CRUD ;
    onglet « Budgets & Fiscal » ; `budget_transfer` **reporté** (pas stubbé).
  - **3B Phase 21 :** 3 skills — `ai_programmer`/Nwiro probe, `firmware`/Pi probe,
    `electronics`/`skill_bom` ; endpoints + tests.
  - **3C :** briefing COO lit `cross_dept` queue ; Review Board LLM derrière
    `REVIEW_BOARD_LLM` (off par défaut) ; ROADMAP sans MVP ambigu.
  - Vérifié : pytest ciblés + suite ; Vitest / tsc.

## 2026-08-09 — Vague 2 dette structurelle BUG-004 : MissionsTab + split COO (refactor)

- **Type :** refactor + docs
- **Details :**
  - **FE :** `DeptMissionsTab` partagé (`web/src/components/shared/dept-missions-tab.tsx`) ;
    wrappers fins app / gaming / robo (`*-v2/missions-tab.tsx`).
  - **COO :** `coo_agent.py` façade **~576** lignes (était ~1476) — modules
    `coo_constants` / `coo_intents` / `coo_routing` / `coo_composio_tools` /
    `coo_project` / `coo_briefing` / `coo_delegates` / `coo_plan` / `coo_handlers` ;
    re-exports compat (tests, telegram_ack, secretary).
  - **BUG-004** mis à jour (mitigé, pas fermé — specs_registry / personas / rnd_center).
  - Vérifié : ruff OK ; pytest **386** passed / 6 skipped ; Vitest **35**/35 ; `tsc` OK.

## 2026-08-09 — Vague 1 hygiène bloquante : Next 16 + Trust UI (feat + fix + docs)

- **Type :** feat + fix + docs
- **Details :**
  - **BUG-017 fermé :** Next **15.5.23 → 16.3.0**, eslint **9**, `eslint.config.mjs`
    (plus de `next lint`), override `dompurify@3.4.13` → `npm audit` **0** vulns.
  - **Phase 31 UI :** `/trust` + `AgentTrustView` + `trust-api` (bandes DEC-011) ;
    lien depuis `/hub` ; Vitest helpers.
  - Docs sync Next 16 (README / ARCHITECTURE / CLAUDE / TESTING / ROADMAP).
  - Vérifié : `tsc` / `eslint` / Vitest **35**/35 / `build:safe` verts.
  - Note : règles hooks React Compiler v6 nouvelles laissées `off` (dette lint
    progressive, pas un silence produit).

## 2026-08-09 — Vague 0 garde-fous code sain — clôture 100 % (docs + chore)

- **Type :** docs + chore
- **Details :** checklist fin de lot dans `AGENTS.md` ; `ALNUA_OVERVIEW.md` tracké ;
  Next 15 + `build:safe` dans `CLAUDE.md` ; prune `feat/rnd-dossier-hub` +
  `fix/auto…` ; **BUG-019 fermé** (WIP pole-dashboard stashé, HEAD `*-v2` live) ;
  DOC_AUDIT Vague 0 100 % ; working tree clean ; `main` sync `origin`.

## 2026-08-09 — Sprint REM-002 close-out analysis (docs)

- **Type :** docs
- **Sprint commit produit :** `7dfad6f` (Next 15 + workflow split + hub/analytics).
- **Details :** analyse 14 sections (code review + intégrité + gouvernance) —
  remédiation Audit 002 A–E + clean suite. Integrity : `tsc`/`eslint`/`build:safe`
  OK ; Vitest **33**/33 ; pytest **386** passed / 6 skipped (**392** collected) ;
  ruff OK. DoD remédiation ~**90%** (MVP Phases 30/31/32/36 assumé). Ouverture
  **BUG-019** (WIP local mockup `/finances`/`/marketing`). Voir `DOC_AUDIT.md`
  Sprint REM-002. Ouverts : BUG-004, BUG-017, BUG-019.

## 2026-08-09 — Audit 004 health check (docs)

- **Type :** docs
- **Details :** second health check 10 dimensions le même soir (post Next 15 /
  remédiation A–E). Verdict 🟢 Good (était 🟡 Concerning en Audit 002).
  BUG-018 ouvert+fermé (micro-drift Next 14 / comptes tests / ROADMAP).
  Resync README, ARCHITECTURE, TESTING, IMPLEMENTATION_STATUS, ROADMAP,
  BUGS stats. Canvas `project-health-audit-004-2026-08-09.canvas.tsx`.
  Ouverts restants : BUG-004, BUG-017.

## 2026-08-09 — Bugs + clean : Next 15, workflow split, FE tooling, hub/analytics live (fix + refactor)

- **BUG-004 :** `workflow_engine` découpé (dossier/ops/ship handlers, fichiers ≤300 sauf engine 447).
- **BUG-017 :** Next **15.5.23** (mitigation partielle ; reste 3 high → Next 16).
- FE : `tsc` 0 erreur ; Vitest 33/33 via `@vitejs/plugin-react-swc`.
- `/hub` + `/analytics` shells live (plus de mockup primary).
- **Build :** `next build` corrompu si `next dev` écrit `.next` en parallèle →
  `npm run build:safe` (`NEXT_DIST_DIR=.next-build`) ; lockfile racine vide retiré.

## 2026-08-09 — Clean suite : DeptV2 chrome + live CEO/Secretary/Brand (refactor + fix)

- Shared `DeptV2PageShell` on all `*-v2` pages (dead local header/sidebar removed).
- `/ceo` → `CeoCockpitPanel` ; `/secretary` → Nadia + console ; `/brand` déjà `BrandView`.
- Residual mockup : `/hub` + `/analytics` only. Vitest routes live étendu.

## 2026-08-09 — Audit 003 : vérification A–E + nettoyage docs/hygiène (docs + chore)

- Verdict : code Phases B–E conforme MVP ; docs ROADMAP/README/IMPLEMENTATION_STATUS
  resync (40 routers, Phases 30/31/32/36 MVP) ; tmp screenshots supprimés ;
  `tmp-mockup-refs/` gitignoré ; suppressions `skill_aider`/`skill_openhands` stagées.
- Tests rejoués : 29 pytest + 12 vitest + ruff OK.

## 2026-08-09 — Phase E remédiation : MVP Phases 30/31/32/36 (feat + test + docs)

- **Phase 30 :** recettes `content_validation` / `campaign_validation` + autonomie
  0–3 (`services/workflow_validation_recipes.py`) ; emit `workflow_step_completed`
  à chaque étape du moteur (DEC-012).
- **Phase 31 :** `services/agent_trust.py` + `GET /agents/trust` (DEC-011).
- **Phase 32 :** `config/quality_gates.py` + `services/review_board.py` +
  `POST /review-board/evaluate` (score structurel MVP, DEC-013).
- **Phase 36 :** handlers cross-dept → `data/cross_dept_queue.json` +
  `GET /cross-dept/queue`.
- Tests : `tests/test_phase_e_mvp.py` ; router `api/routers/trust.py` (40e).

## 2026-08-09 — Phase D remédiation : orphans, façades, split rnd_trees, aliases (refactor + docs)

- **Type :** refactor + docs + chore
- **Details :**
  - **BUG-014 :** suppression `skills/skill_aider.py` + `skills/skill_openhands.py`
    (jamais importés runtime). `brand_agent` **conservé** (Phase 35 / SPEC / tests).
  - **BUG-015 :** `skills/coding_facade.py` (entry Hub vs watchdog) ;
    `services/facades/briefing_facade.py` documente les 3 chemins briefing.
  - **BUG-004 (1er cut) :** routes arbres + benchmark extraites vers
    `api/routers/rnd_trees.py` (~158 lignes) ; `rnd.py` allégé ; **39** routers.
  - **BUG-005 :** aliases `rnd_*_agent` → ids courts ajoutés (`coo_agent` était
    déjà aliasé). MissionsTab partagé **reporté** (trop large pour ce lot).
  - DEC-008 addendum (Aider reste backend de `skill_coding_agent`).

## 2026-08-09 — Phase C remédiation : deps npm, vault policy, hygiène git (fix + chore + docs)

- **Type :** fix + chore + docs
- **Details :**
  - **BUG-012 :** `npm audit fix` + `vitest@4.1.10` (critical fermée) + `postcss@8.5.26`
    (+ overrides). Reste **8** vulns (0 critical, 5 high) — surtout Next 14.2.35,
    acceptées jusqu’à migration Next 15/16 (pas de `--force`).
  - **BUG-016 :** policy `vault/obsidian/library/_index/RETENTION.md` + gitignore des
    corps `library/**` (sauf `_index/`).
  - **BUG-002 :** `git rm --cached data/agent_models.json` (fichier local conservé).
  - **BUG-003 :** `fastapi-mcp==0.4.0` ajouté à `requirements.lock.txt` (venv).
  - Branches locales juin 2026 supprimées (`feat/issue-*`, `fix/auto…`).
    `feat/rnd-dossier-hub` conservée (active / remote).

## 2026-08-09 — Phase B remédiation : routes live + Finance factures (fix + feat)

- **Type :** fix + feat
- **Details :**
  - **BUG-013 :** `/finances`, `/marketing`, `/app`, `/gaming`, `/robo` ré-exportent
    leurs shells `*-v2` (plus de `MockupDepartmentPage` sur la nav primaire).
  - **`/rd` :** shell `rnd-v2` par défaut ; deep-links `?dossier=` / `?tab=` /
    `?tree=` / `?view=` restaurent `RdPageContent` (éditeur legacy).
  - **Finance DEC-016 UI :** onglet renommé « Coûts & Factures » (panel SaaS /
    factures / Revolut déjà branché) + KPI « Factures à payer » sur Vue globale.
  - Tests Vitest : `department-routes-live`, `finances-api` helpers.

## 2026-08-09 — Audit santé + catch-up gouvernance Phases 22-38 / Finance / Ops (docs + feat + ops)

- **Type :** docs + feat + ops + fix (catch-up rétroactif — le CHANGELOG avait
  décroché au 2026-07-31, voir BUG-011)
- **Commits clés :** `f1f6f7a` / `590f5f6` (ops Sentry + security-ingest Résonance),
  `f1a1224` (department v2 UI, finance SaaS, marketing funnel, R&D council —
  ~352 fichiers / +25k lignes), `6dc1b29` (nettoyage panels mockup marketing),
  `c84ec7d` (Audit 002 health check)
- **Details :**
  - **Phases 22-27 (R&D v2) :** coquille `/rnd-v2`, Innovation Pipeline, Incubateur
    Kanban, Moteur Conseil (réceptacle), Arbres mindmap, table Dossiers — marquées
    Complete dans `ROADMAP.md`.
  - **Phase 28 (Explorer veille) :** toujours ⏸️ Not started.
  - **Phases 29 / 33 / 37 (Marketing) :** Command Center visuel, Campagnes + Content
    Studio, mesure Reach/Engagement/ROI/Funnel — Complete ; funnel marketing API
    (`marketing_funnel`) dans le lot `f1a1224`.
  - **Phase 34 (Finance) :** 🔄 In progress — DEC-016 : ledger factures JSON, catalogue
    SaaS spend, Revolut lecture seule (API) ; UI `/finances-v2` et tables
    budgets/fiscalité encore en retard (Phase B du plan de remédiation).
  - **Phase 38 (harmonisation visuelle MockupShell) :** Complete côté rendu, avec
    caveat : routes primaires `/finances` `/marketing` `/rd` encore sur mockup —
    UI live sous `*-v2` (BUG-013, Phase B).
  - **Phases 30-32 / 35-36 :** toujours Not started (workflow validation recipes,
    Trust, Review Board, Brand transversal, event bus cross-dept) — bus
    `event_bus.py` existe déjà, wiring Phase 36 non fait.
  - **DEC-011–016 :** Trust séparé compétition, workflow générique unique, Review
    Board, stats Marketing manuelles, OpenRouter prompt cache, Comptabilité
    SaaS/factures/Revolut.
  - **Ops :** mapping Résonance dans Sentry hotfix + bug_watchdog ; security-ingest
    fortress alerts.
  - **BUG-009 / BUG-010 :** rate-limit authentifié + loader dossier R&D (corrigés
    fin juillet, absents du CHANGELOG jusqu’ici).
  - **Audit 002 (2026-08-09) :** verdict 🟡 Concerning — ouverture BUG-011…016 ;
    Phase A = ce catch-up gouvernance.

## 2026-07-31 — Roster Gaming/Robo, redesign UI départements, real-data Phases 15-20, fix Academy (feat + fix + chore)

- **Type :** feat + fix + chore
- **Commits :** `b071f5c` (roster 15 agents spécialisés Gaming/Robo, Phase 13),
  `7ff87a7` (redesign UI département — missions, backlog, docs, équipe, modules),
  `0b78386` (infra real-data builds/assets/télémétrie/communauté Gaming+Robo,
  Phases 15-20 + BUG-006/007/008), `b5fe7c3` (refresh export vault bibliothèque)
- **Details :**
  - **Phase 13 (agents) :** complète le roster App/Gaming/Robo avec les 15 rôles
    spécialisés déjà documentés dans `CLAUDE.md` (level designers, artistes,
    QA, safety, simulation) — endpoints MCP + specs opérationnelles inclus.
  - **Redesign UI départements :** nouveau shell (équipe/mission/chat), missions
    kanban + analytics, backlog, documentation, modules projet, déployé sur
    App/Gaming/Robo (`app-v2`/`gaming-v2`/`robo-v2`) + page détail projet. Détail
    complet dans `PLAN_DEPARTMENTS_UI_REDESIGN.md`/`TEST_PLAN_DEPARTMENTS_UI_REDESIGN.md`,
    suivis différés dans `TODOS.md`.
  - **Phases 15-20 (ROADMAP.md) :** remplace les données mock de builds/assets/
    labo/télémétrie/communauté Gaming+Robo par de vraies tables Supabase +
    endpoints + scripts rapporteurs + rendu réel, avec réceptacle honnête
    (pas de fake data) là où l'infra externe manque réellement (pipeline UE5,
    Steam Wishlist API, accès physique au robot Eve).
  - **BUG-006 :** connexions Supabase HTTP/2 périmées jamais retentées.
  - **BUG-007 :** dérive schéma `roadmap` (CHECK priority/status, colonnes
    `updated_at`/`linked_ticket_id` absentes) qui cassait silencieusement
    `POST /roadmap` et `/roadmap/from-ticket/{id}`.
  - **BUG-008 :** `agent_wake.py::get_pipeline_status()` annonçait le pipeline
    Academy "en cours" sur la seule base des labels GitHub, sans vérifier que
    le clone local existe — corrigé, puis le repo `alnua-academy` a été cloné
    dans `C:\Dev\alnua-academy` et les 5 issues bloquées relancées.
  - **Fix UI (non commité séparément) :** carte "Mission en cours" (Théo,
    `app-v2/team.tsx`) plafonnée + scrollable — un message d'erreur long
    (ex. `OpenRouter 402`) faisait exploser toute la rangée équipe.

## 2026-07-25 — Gouvernance, audit sécurité/qualité, méthode de travail (docs + fix)

- **Type :** docs + fix
- **Details :**
  - Bootstrap gouvernance : création de `ARCHITECTURE.md`, `ROADMAP.md`,
    `DECISIONS.md`, `BUGS.md`, `CHANGELOG.md` (ce fichier), `IMPLEMENTATION_STATUS.md`,
    `TESTING.md`, `DOC_AUDIT.md` — ALNUA Hub était le seul des 4 projets du workspace
    `C:\Dev` sans cette couche.
  - Audit sécurité + qualité de code (2 agents en parallèle) : correctifs SEC-001
    (injection shell critique sur `/ide/run`), SEC-004/005/006 (sanitization manquante
    sur `/sav/ask`, `/agents/brainstorm*`, `trend_monitor`), BUG-001 (violations
    `AgentBase.__init__`).
  - Décisions tranchées par Emilie : SEC-002/DEC-010 (`HUB_API_KEY` obligatoire dans
    tous les environnements, plus de mode dev ouvert) et DEC-009 (Nwiro/UE5 confirmé
    comme choix assumé, règle "Pas d'UE5" retirée de `CLAUDE.md`).
  - Méthode de travail agents IA : `AGENTS.md` (point d'entrée universel) +
    `.cursor/rules/agent-orchestration.mdc`, `ai-agent-survival.mdc`, `async-jobs.mdc`.
  - Suite complète (`pytest tests/ -q`) et `ruff` vérifiés verts après chaque étape.
    Détail complet dans `DOC_AUDIT.md` (Audit 001 + addendum).

## 2026-07-24 — Coûts & jalons (feat + fix)

- **Type :** feat + fix
- **Commits :** `013a04e`, `a3d33e2`, `8113af3`, `2ec99d2`, `3401e34`, `aa7b39d`, `8b366a5`
- **Details :** suivi combiné des coûts API (ElevenLabs auto + hosting manuel) sur la
  page Comptabilité ; "Jalons à venir" branché sur Google Calendar via Nadia ; fixes
  UI R&D (scroll, flexbox) ; vérification `library` corrigée pour checker la leçon
  apprise réelle plutôt que la seule source.

## 2026-07-23 — Centre R&D dossier hub + polish design (feat + fix + style)

- **Type :** feat + fix + style + chore
- **Commits :** `16c84c2`, `cbb9169`, `fd769c2`, `7f8061c`, `1a9d96f`, `c42e81f`,
  `7ae0798`, `617ab07`, `ddb979e`, `4dec459`, `ab36242`, `2ff02dc`, `7fcd614`,
  `d9880cd`, `b2e7a19`, `de90d83`, `8b05cd7`
- **Details :** complétion du pipeline Centre R&D dossier hub + extensions
  plateforme ; correctifs findings design (FINDING-001 à 006 : topbar, sparklines,
  hydratation SSR, contraste) ; retrait CreatorFlow/NUAWAY ops/media pipeline studio ;
  lint F401 enforced en CI ; noms d'agents réels dans le graphe de comm.

## 2026-07-23 — Audits P0/P1/P2 (fix)

- **Type :** fix
- **Commits :** `4b8f984` (P0 — agents R&D, montage routers), `e1a4f38` (P1 — auth
  bots, sanitizing input, résilience LLM, lint), `84e5664` (P2 — error boundaries web,
  routes comme source de vérité, couverture e2e), `5497218` (écarts restants —
  migrations, imports routers, openroom, pi-command)
- **Details :** série d'audits internes successifs fermant des écarts de sécurité et
  de robustesse identifiés en amont.

## 2026-06-24 — Migration 9-layer operating specs (feat)

- **Type :** feat
- **Commit :** `1a46408`
- **Details :** tous les personas migrés d'un `SYSTEM_PROMPT` 5-sections inline vers
  génération via `config/agent_operating_spec.py::get_system_prompt()`.

## 2026-06-13 → 2026-06-15 — Extension API + Centre R&D + assainissement (feat)

- **Type :** feat + chore
- **Commits :** `5c0447a` (Centre R&D dossier pipeline phases 0-8), `02fdba3`
  (extension architecture API Hub, services avancés au runtime), `10989d3`
  (assainissement Hub phases 0-6, perf lobby-bureau, extensions plateforme)

## 2026-06-12 — Durcissement sécurité + fallbacks robustesse (feat + fix)

- **Type :** feat + fix
- **Commits :** `7c86370` (X-Hub-Key obligatoire sur routes Hub API), `2df9669` (RLS
  anon restreinte à SELECT sur tables sensibles), `d094203` (restriction `/brand/assets`
  au dossier `brand_kits`), `cf9e9f9`/`f9054d0`/`831c2bf`/`c890f778`/`4656289`
  (fallbacks gracieux : Composio, Discord, Nwiro/UE5, SSH embedded, hardware BOM),
  `0cd7c53` (fix tests Windows + COO API), `41790b3`, `716767a`, `7c41e94`,
  `824a0ab`, `137a752`

## 2026-06-11 — Fondation du Hub (feat)

- **Type :** feat (burst initial)
- **Commits :** `e995186` (first commit) → `137a752`
- **Details :** mise en place initiale — API FastAPI, agents CrewAI, dashboard v3
  (siège social virtuel : lobby + bureaux par département), OpenRoom (war room
  visuelle), intégrations Mem0 (mémoire persistante), Langfuse (tracing LLM),
  Composio (OAuth gateway), Chroma (base de connaissances), OpenHands + Aider
  (pipeline codage autonome), skill Nwiro (UE5, port 5353 — choix confirmé assumé le
  2026-07-25, voir `DECISIONS.md` DEC-009).
