# Testing — ALNUA Hub

> Reconstitué le 2026-07-25 depuis `.github/workflows/ci.yml`, `pytest.ini` et
> l'inventaire de `tests/`. Chiffres resynchronisés le **2026-08-09** (Phase A /
> Audit 002).

## Pipeline CI (3 jobs, tous bloquants sur `main`/PR)

| Job | Étapes | Outil |
|-----|--------|-------|
| `backend` | ruff lint → smoke import (composio + `api.app`) → pytest + coverage | Python 3.12, pytest, ruff |
| `frontend` | typecheck (`tsc --noEmit`) → lint (`eslint .`) → tests unitaires | Next.js 16, Vitest |
| `e2e` | build + Playwright (Chromium) | Playwright, avec feature flags admin activés (`ADMIN_COSTS_PAGE_ENABLED`, etc.) |

Ordre respecté : lint avant build/tests (le moins cher d'abord), conforme au principe
"build passe avant les tests" — ici lint avant tout, import smoke-test avant la suite
complète.

## Suite Python (`tests/`)

- **~74 fichiers** `test_*.py` (**392** tests collectés au 2026-08-09 soir, Audit 004),
  organisés par module/feature, pas par couche architecturale stricte (pas de
  séparation explicite unit/integration/e2e par dossier).
- **Markers pytest** (`pytest.ini`) :
  - `integration` — tape un vrai service externe (Supabase, OpenRouter, Composio...),
    nécessite des credentials live, **pas exécuté par défaut en CI**.
  - `slow` — setup de fixtures lourd ou pipelines multi-rounds.
- **Couverture** : `--cov-fail-under=28` sur `services`, `agents`, `models` — seuil bas,
  gate anti-régression plutôt qu'objectif de couverture. Ne pas remonter ce seuil sans
  plan concret (le remonter mécaniquement casserait la CI sans ajouter de valeur).
- **Env de test** : credentials factices (`SUPABASE_URL=https://example.supabase.co`,
  clés `test-*`), `ENVIRONMENT=development`, `RATE_LIMIT_ENABLED=0`.
- **Auth Hub-Key** : `HUB_API_KEY` est obligatoire dans tous les environnements
  (DEC-010 / SEC-002). La suite couvre le comportement via notamment
  `tests/test_devex_phase6.py` (réécrit lors du correctif SEC-002) — l'ancienne note
  « aucun test dédié » de l'Audit 001 est **obsolète**.

## Suite frontend (`web/`)

- **Unitaire** : Vitest (`npm run test`) — **33** tests / 6 fichiers verts au
  close-out Sprint REM-002 (2026-08-09) ; encore mince face à la surface UI.
- **E2E** : Playwright (`web/e2e/`), Chromium seul en CI, flags admin forcés à `1` pour
  couvrir les pages derrière feature flag.
- **Typecheck** : `tsc --noEmit` bloquant, séparé du lint (Next **15.5.23**).
- **Build prod :** préférer `npm run build:safe` si `next dev` tourne (cache
  `.next` corrompu sinon — documenté BUG-017 / CHANGELOG).

## Ce qui manque (constat, pas un audit exhaustif)

- Pas de convention `[USER]`/`[ADMIN]`-style pour préfixer les tests d'autorisation —
  non prioritaire vu l'absence de système de rôles multi-utilisateurs dans le Hub
  aujourd'hui (accès protégé par `X-Hub-Key`, pas par rôle).
- Pas de séparation dossier par couche (`unit/`, `service/`, `repository/`) — les tests
  sont nommés par feature. Cohérent avec un projet solo à itération rapide ; à
  reconsidérer seulement si la confusion devient un problème réel.
- Couverture UI Finance profondeur (budgets / fiscalité) et suites MVP Phases
  31/32 (trust UI, Review Board LLM) encore mince — routes primaires live au HEAD
  (BUG-013 fermé) ; **ne pas committer** le WIP mockup VAE sans traiter BUG-019.
