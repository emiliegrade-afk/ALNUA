# Documentation Audit Log — ALNUA Hub

Historique des audits de gouvernance effectués.

---

## Audit 001 — Bootstrap gouvernance + audit sécurité/qualité

- **Date :** 2026-07-25
- **Scope :** ALNUA_HUB était le seul des 4 projets de `C:\Dev` (`NAÏA`, `NUAWAY`,
  `RESONANCE`, `ALUNA_HUB`) sans couche de gouvernance (`ARCHITECTURE.md`,
  `ROADMAP.md`, `DECISIONS.md`, `BUGS.md`, `CHANGELOG.md`, `IMPLEMENTATION_STATUS.md`,
  `TESTING.md`, `DOC_AUDIT.md`). Bootstrap complet des 8 fichiers + audit sécurité et
  audit qualité de code menés en parallèle par deux agents dédiés, sur demande
  explicite ("tout ce qui est security, gouvernance et tout le reste").
- **Méthode :** reconstitution rétroactive depuis `git log` (68 commits, historique
  depuis 2026-06-11), `CLAUDE.md`, `ruff.toml`, `.github/workflows/ci.yml`, les
  fichiers `SPEC_*.md`, et lecture directe du code (routers, agents, services). Pas
  de contenu inventé — tout ce qui n'était pas vérifiable a été marqué explicitement
  comme non tranché plutôt que deviné (voir DEC-009, SEC-002, BUG-003 dans
  `DECISIONS.md`/`BUGS.md`).
- **Audit sécurité — findings :**
  - 🔴 1 critique (SEC-001, injection shell sur `/ide/run`) — **corrigé**
  - 🟠 2 hautes (SEC-002 mode dev ouvert par défaut, SEC-003 RCE SSH Pi qui en dépend)
    — **laissées ouvertes**, décision produit/déploiement à trancher avec Emilie
  - 🟡 3 moyennes (SEC-004/005/006, sanitization manquante sur `/sav/ask`,
    `/agents/brainstorm*`, `trend_monitor`) — **corrigées**
  - ✅ Vérifié sans anomalie : secrets en dur, `.env` commité, injection SQL, CORS,
    path traversal, logs, contrôle d'accès `/mcp`
- **Audit qualité de code — findings :**
  - ruff : 0 erreur avant et après corrections
  - tests : 354 passed / 6 skipped (skips justifiés par dépendances d'environnement
    absentes — Hermes local, disque D, clé Composio) avant et après corrections
  - 2 violations de la règle `AgentBase.__init__` (`rnd_agent.py`, `rnd_social_agent.py`)
    — **corrigées** (BUG-001)
  - Montage routers, imports `route_common`, `agent_scores.json` non tracké,
    enregistrement `AGENT_PERSONAS` : conformes, aucune anomalie
  - Fichiers >300 lignes (15 fichiers, jusqu'à 1475 lignes) : dette pré-existante,
    non traitée (BUG-004) — refactor hors périmètre d'un audit sécurité/gouvernance
- **Trouvaille hors périmètre initial :** `skills/skill_nwiro.py` (intégration
  Unreal Engine 5, référencée par 3 agents) contredit la règle invariante "Pas d'UE5"
  de `CLAUDE.md`. Ni supprimé ni "gardé" par défaut — documenté comme décision
  ouverte (`DECISIONS.md` DEC-009) précisément parce que les deux lectures (règle
  obsolète vs. code à corriger) sont plausibles depuis le code seul.
- **Findings corrected :** SEC-001, SEC-004, SEC-005, SEC-006, BUG-001 (voir `BUGS.md`
  section "Corrigés"). Tests + ruff vérifiés verts après chaque correction, suite
  complète revérifiée à la fin.
- **Findings deferred :** SEC-002, SEC-003, DEC-009, BUG-002, BUG-003, BUG-004,
  BUG-005 (voir `BUGS.md` section "Ouverts") — tous nécessitent soit une décision
  produit (Nwiro/UE5), soit une décision de déploiement/sécurité qui change un
  comportement documenté (mode dev ouvert), soit un refactor de taille non demandé
  (fichiers volumineux) : volontairement non résolus en autonome.
- **Next audit planned :** pas de date fixée — à relancer après la décision SEC-002 /
  DEC-009, ou au prochain sprint significatif, pour garder ce cycle vivant plutôt que
  de le laisser retomber en retard comme avant ce bootstrap.

## Audit 001 — addendum : méthode de travail agents IA

- **Date :** 2026-07-25
- **Scope :** sur demande explicite, ajout des artefacts "méthode de travail" du guide
  de gouvernance (Parties 9 "tâches async" et 10 "travailler avec des agents IA"),
  absents des 4 fichiers de gouvernance créés plus tôt le même jour.
- **Créés :** `AGENTS.md` (point d'entrée universel — absent des 4 projets de
  `C:\Dev`), `.cursor/rules/agent-orchestration.mdc` (hiérarchie de fiabilité, règle
  des 3 axes, Bootstrap→Fan-out→Merge), `.cursor/rules/ai-agent-survival.mdc` (stubs,
  taille de fichier, ripple effect, données externes non fiables), `.cursor/rules/async-jobs.mdc`
  (persistance par étape, revérification d'état, dégradation gracieuse — scopé par
  `globs` aux fichiers workflow/dispatch/bots).
- **Méthode :** chaque règle citée est ancrée dans du code réel de ce repo, vérifié par
  grep/lecture directe (pas un copier-coller générique du guide) — `services/parallel_runner.py`,
  `services/plan_executor.py`, `services/rnd_dispatch_executor.py`,
  `services/workflow_engine.py`, `skills/skill_discord_wyrdheim.py`, et les findings
  SEC-001/SEC-006/BUG-001/BUG-004 de l'audit du même jour. Une citation initiale
  incorrecte (`bots/discord_bot.py` au lieu de `skills/skill_discord_wyrdheim.py` pour
  le pattern de dégradation gracieuse Discord) a été corrigée après vérification du
  code réel plutôt que laissée telle quelle.
- **Findings deferred :** aucun — tâche de création pure, pas d'audit de code
  supplémentaire mené dans cet addendum.

---

## Audit 002 — Health check 10 dimensions

- **Date :** 2026-08-09
- **Scope :** audit santé projet complet (gouvernance, structure, deps, types,
  tests, config/secrets, perf, drift doc, git hygiene, risques forward) —
  **aucun changement de code produit**, uniquement tracker bugs + ce log.
- **Méthode :** lecture des 8 fichiers de gouvernance + README ; `git log -30` ;
  mesures fichiers >300/1000 lignes ; `pytest --collect-only` ; `npm audit` ;
  grep TypeScript `any`/`@ts-ignore` ; inventaire routers (`ALL_ROUTERS` = 38) ;
  personas (49) ; spot-check Phase 34 Finance / Phase 36 event bus / orphans.
- **Verdict :** 🟡 **Concerning** — le produit avance vite et les hard gates
  sécurité d'Audit 001 tiennent, mais la gouvernance et la dette structurelle
  ont décroché du code.
- **Findings majeurs :**
  - 🔴 CHANGELOG / IMPLEMENTATION_STATUS / chiffres ARCHITECTURE désynchronisés
    (BUG-011) — CHANGELOG figé au 2026-07-31
  - 🔴 Routes primaires encore sur MockupShell vs `*-v2` (BUG-013)
  - 🟠 `npm audit` 21 vulns dont 1 critical (BUG-012)
  - 🟠 BUG-004 empiré (~10 fichiers Python >1000 lignes, nouveaux monolithes
    `agent_specs_registry` / `schemas` / `personas`)
  - 🟠 Phase 34 Finance : backend partiel (DEC-016) sans UI client
  - 🟡 Orphans `brand_agent` / `skill_aider` / `skill_openhands` (BUG-014)
  - 🟡 Dual coding + triple briefing (BUG-015)
  - 🟡 Vault library ~988 notes quasi-doublons (BUG-016)
  - ✅ TypeScript : 0 `as any` / 0 `: any` / 0 `@ts-ignore`
  - ✅ SEC-002 toujours tenu ; `.env` non tracké ; pas de `VITE_` secrets
  - ✅ Suite tests : 381 collected / 66 `test_*.py` (était ~354 / 63 docs)
- **Ouverts :** BUG-011 … BUG-016 (+ mise à jour BUG-004/005) — voir `BUGS.md`
- **Vs Audit 001 :** sécurité mieux (SEC-002/003 fermés) ; tests + types OK ;
  gouvernance et taille de fichiers **pire** ; surface produit beaucoup plus
  large sans resync docs.
- **Next sprint suggested :** (1) resync CHANGELOG + IMPLEMENTATION_STATUS +
  comptes agents/routers ; (2) reconnecter routes mockup → `*-v2` ; (3) npm
  audit ciblé ; (4) Phase 34 UI Finance ; (5) un découpage BUG-004 (coo/rnd).
- **Next audit planned :** après resync gouvernance + Phase 34 UI, ou au plus
  tard dans 4 semaines — ne pas laisser 2 mois sans audit comme entre 001 et 002.

### Audit 002 — addendum Phase A (resync gouvernance)

- **Date :** 2026-08-09
- **Scope :** exécution Phase A du plan de remédiation — docs only, BUG-011 fermé.
- **Fait :** CHANGELOG catch-up 2026-08-01→09 ; IMPLEMENTATION_STATUS Phases 22-38 /
  Marketing / Finance ; ARCHITECTURE / AGENTS / TESTING / README / CLAUDE skill
  table / ROADMAP compte routers ; SPEC_WORKFLOW_ENGINE `sav_lite`/`ship_*`/`semaine`
  alignés ; règle anti-drift >500 lignes dans CHANGELOG + AGENTS.md.
- **Restant (Phases B–E) :** BUG-012…016, routes mockup, npm, vault, splits.

### Audit 002 — addendum Phase B (routes live + Finance UI)

- **Date :** 2026-08-09
- **Scope :** BUG-013 + branchement visible DEC-016 (factures/SaaS déjà dans
  `SaasInvoicesPanel` / `CoutsTab`).
- **Fait :** ré-exports `/finances` `/marketing` `/app` `/gaming` `/robo` → `*-v2` ;
  `/rd` → `rnd-v2` + legacy deep-links ; KPI factures Vue globale ; onglet
  « Coûts & Factures » ; Vitest 12 tests verts ; BUG-013 fermé.
- **Restant mockup :** `/analytics` `/brand` `/secretary` `/ceo` `/hub` si encore
  sur MockupShell — hors Phase B stricte, à traiter en suivi.
- **Suite :** Phase C (npm audit, vault, branches).

### Audit 002 — addendum Phase C (deps + vault + git hygiene)

- **Date :** 2026-08-09
- **Fait :** vitest 4.1.10 (0 critical) ; postcss 8.5.26 + overrides ; npm 21→8
  vulns ; RETENTION vault + gitignore library dumps ; `git rm --cached`
  `data/agent_models.json` ; `fastapi-mcp` dans lock ; 3 branches juin
  supprimées ; BUG-002/003/012/016 fermés ; BUG-017 ouvert (reste Next 14).
- **Note :** pages `*/page.tsx` départements ont été réécrites en mockup par un
  autre process pendant C — **re-restaurées** vers `*-v2` avant fin de phase ;
  Vitest routes live 12/12 verts.
- **Suite :** Phase D (orphelin skills, façades, 1er split BUG-004).

### Audit 002 — addendum Phase D (structure)

- **Date :** 2026-08-09
- **Fait :** delete `skill_aider`/`skill_openhands` ; `coding_facade` ;
  briefing facade doc ; split `rnd_trees` (alors 39 routers) ; aliases
  `rnd_*_agent` ; BUG-005/014/015 fermés ; BUG-004 mitigé (1er cut).
  MissionsTab reporté.
- **Tests :** 21 passed (`workflow_engine`, `facades_phase0`, `pole_services`).
- **Suite :** Phase E (ROADMAP 30–32/36 MVP) ou Audit 003.

### Audit 002 — addendum Phase E (MVP Phases 30/31/32/36)

- **Date :** 2026-08-09
- **Fait :** `workflow_validation_recipes` (`content_validation`,
  `campaign_validation`, autonomie 0–3) ; `agent_trust` + `quality_gates` +
  `review_board` ; handlers cross-dept + queue ; router `trust` (**40**e) ;
  emit `workflow_step_completed` ; tests `test_phase_e_mvp.py`.
- **Honnêteté MVP :** pas de débat LLM Review Board, pas de jauge frontend
  trust, pas de `budget_transfer`, pas de daily_briefing cross-dept.
- **Tests :** 16 passed (`test_phase_e_mvp` + `test_workflow_engine`).
- **Suite :** Audit 003 ou profondeur Phases 31/32/34.

## Audit 003 — Vérification post-remédiation A–E + nettoyage

- **Date :** 2026-08-09
- **Verdict :** remédiation **pas 100 %** avant nettoyage (dérive docs +
  hygiène) ; **code Phases B–E OK** ; après nettoyage docs/hygiène →
  **conforme MVP** (suites produit hors scope : BUG-004, BUG-017, mockup
  analytics/brand/secretary/ceo/hub, profondeur 31/32/34/35).
- **Vérifié vert :** routes live BUG-013 ; recettes/trust/gates/cross-dept ;
  orphans skills absents disque ; vitest 4.1.10 ; fastapi-mcp lock ;
  agent_models untracked ; RETENTION vault ; ruff OK ; **29** pytest cible +
  **12** vitest routes/finances.
- **Écarts corrigés dans cet audit :** table ROADMAP 30/31/32/36 + blurb
  « Current phase » ; comptes routers **40** (README / IMPLEMENTATION_STATUS /
  ROADMAP historique / DOC_AUDIT) ; lignes IMPLEMENTATION_STATUS encore ⏸️
  pour 30/36 ; gitignore `tmp-mockup-refs/` ; suppression `tmp-audit-*.png` /
  `tmp-live-*.png` ; stage suppressions `skill_aider` / `skill_openhands`.
- **Canvas :** `project-health-audit-003-2026-08-09.canvas.tsx`

---

## Audit 004 — Health check 10 dimensions (soirée post-Next 15)

- **Date :** 2026-08-09 (soir)
- **Scope :** second full health check le même jour, **après** remédiation A–E,
  Audit 003, DeptV2 chrome, CEO/Secretary/Brand/hub/analytics live, et upgrade
  Next **15.5.23**. Aucun changement de code produit — tracker + docs only.
- **Méthode :** relecture gouvernance ; `git log -30` ; line counts ; `pytest
  --collect-only` (392) ; `npm audit` (6 vulns) ; grep TS `any`/`@ts-ignore` ;
  `AGENT_PERSONAS`=49 / `ALL_ROUTERS`=40 ; spot-check routes mockup ; branches.
- **Verdict :** 🟢 **Good** — remédiation tient (routes live, SEC-002, types,
  tests ↑), mais pas Excellent : dette structurelle BUG-004 + micro-drift docs
  déjà réapparu en heures (Next 14 encore dans README/ARCHITECTURE avant ce
  correctif) + 3 high npm (sharp → Next 16).
- **Findings majeurs :**
  - 🟡 BUG-018 — micro-drift gouvernance post-003 (Next 14 vs 15.5.23 ; tests
    381→392 ; ROADMAP « or Audit 003 » ; DOC_AUDIT 003 residual mockup obsolète)
    — **fermé dans cet audit** (resync docs)
  - 🟠 BUG-004 — toujours ouvert : 4 fichiers Python >1000 lignes
    (`agent_specs_registry` 1411, `coo_agent` 1289, `agent_personas` 1110,
    `rnd_center` 1042) ; MissionsTab tripliqué (~600 lignes ×3)
  - 🟠 BUG-017 — mitigé Next 15 (8→6 vulns) ; **reste 3 high** (sharp/libvips
    via Next — fermeture = Next 16)
  - 🟡 Phase 21 non démarrée — 15 personas Gaming/Robo sans skills réels
  - 🟡 `ALNUA_OVERVIEW.md` non tracké ; `origin/fix/auto…` (2026-06-12) stale
    — **résolu Vague 0** (`8cee105` + prune remote)
  - ✅ TypeScript : toujours 0 `any` / 0 `@ts-ignore`
  - ✅ Routes primaires : 0 `MockupDepartmentPage` (Vitest guard)
  - ✅ Secrets : `.env` non tracké ; pas de `VITE_` secrets ; `.env.example` OK
- **Ouverts après audit :** BUG-004, BUG-017 *(BUG-019 ajouté puis fermé en Vague 0)*
- **Vs Audit 002 :** Concerning → Good ; mockup routes et critical npm fermés
- **Vs Audit 003 :** code MVP confirmé + suite clean (hub/analytics/ceo/…) ;
  docs avaient déjà redérivé — anti-drift pas encore une habitude
- **Canvas :** `project-health-audit-004-2026-08-09.canvas.tsx`
- **Next sprint suggested :** (1) 1–2 splits BUG-004 ; (2) Phase 34 budgets ;
  (3) Next 16 / BUG-017 ; (4) Phase 21 skills Gaming/Robo ; (5) profondeur
  Review Board LLM / trust UI
- **Next audit planned :** après Phase 34 depth ou Next 16, **≤ 3 semaines**
  (ne pas retomber dans le trou 001→002 de ~2 semaines)

---

## Vague 0 — Garde-fous code sain (clôture 100 %)

- **Date :** 2026-08-09 (soir)
- **Commit :** `8cee105` (+ docs clôture ci-dessous)
- **Scope :** checklist anti-drift + CI mentale opérationnelle ; OVERVIEW tracké ;
  prune branches ; working tree clean (WIP FE stashed, HEAD live).
- **Done criteria (tous verts) :**
  - [x] Checklist fin de lot dans `AGENTS.md` (anti-drift + ruff/pytest + tsc/vitest + `build:safe`)
  - [x] `ALNUA_OVERVIEW.md` tracké + ordre de lecture
  - [x] Next 15 + `build:safe` dans stack `CLAUDE.md`
  - [x] Branches mortes supprimées local + remote (`feat/rnd-dossier-hub`, `fix/auto…`) — seul `main` reste
  - [x] CHANGELOG Vague 0
  - [x] Working tree clean : WIP pole-dashboard `/finances`/`/marketing` **stashé**
    (`git stash list` — message `WIP BUG-019…`) ; HEAD garde ré-exports `*-v2`
  - [x] BUG-019 fermé (arbre propre, live conservé)
  - [x] `main` poussé sur `origin` (sync remote)
- **Ouverts restants (hors Vague 0) :** BUG-004, BUG-017
- **Suite plan code sain :** Vague 1 (BUG-017 / trust) ou Vague 2 (MissionsTab)

---

## Sprint REM-002 — Close-out analysis (remédiation A–E + clean Next 15)

- **Date :** 2026-08-09 (soir)
- **Sprint ID :** REM-002 — Remédiation Audit 002 (Phases A–E) + Clean suite
- **Sprint commit produit :** `7dfad6f` (`fix(web): Next 15 upgrade, safe build,
  workflow split, live hub/analytics`)
- **Health check associé :** Audit 004 (`0ad3f9b`) — déjà passé ; ce close-out
  ajoute l’analyse 14 sections + BUG-019 (WIP).
- **Scope :** code review + intégrité (tsc / lint / vitest / pytest / ruff /
  `build:safe`) + sync gouvernance. **Aucun code produit** dans ce close-out.
- **Verdict global (après Vague 0) :** ✅ **DoD remédiation + Vague 0 à 100 %**
  — BUG-019 tranché (WIP stashé, HEAD live). Suites produit hors scope restent
  BUG-004 / BUG-017.
- **DoD remédiation :** ~**90%** produit MVP (A–E + clean) ; **Vague 0 hygiene = 100 %**.
- **Integrity (rejoué 2026-08-09 soir) :**
  - `npx tsc --noEmit` (web) ✅
  - `npm run lint` ✅ (0 warnings)
  - `npm test` ✅ **33**/33
  - `npm run build:safe` ✅ Next 15.5.23
  - `ruff check agents/ services/ api/ config/ database/ bots/ skills/` ✅
  - `pytest tests/ -q` ✅ **386** passed / **6** skipped (**392** collected)
  - `npm audit` (web) : **6** vulns (3 high sharp → BUG-017 / Next 16)
- **Finding BUG-019 :** WIP local (évolué vers `pole-dashboard`, plus seulement
  MockupShell) sorti de l’arbre de travail via `git stash` en Vague 0 — HEAD
  conserve `/finances` → `finances-v2`, `/marketing` → `marketing-v2`.
- **Ouverts après Vague 0 :** BUG-004, BUG-017
- **Next step ordonné :** Vague 1 (Next 16 / BUG-017) **ou** Vague 2 (MissionsTab /
  BUG-004) **ou** `git stash pop` si reprise volontaire du pole-dashboard.
