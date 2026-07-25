# Testing — ALNUA Hub

> Reconstitué le 2026-07-25 depuis `.github/workflows/ci.yml`, `pytest.ini` et
> l'inventaire de `tests/` lors du bootstrap de gouvernance.

## Pipeline CI (3 jobs, tous bloquants sur `main`/PR)

| Job | Étapes | Outil |
|-----|--------|-------|
| `backend` | ruff lint → smoke import (composio + `api.app`) → pytest + coverage | Python 3.12, pytest, ruff |
| `frontend` | typecheck (`tsc --noEmit`) → lint → tests unitaires | Next.js 14, Vitest |
| `e2e` | build + Playwright (Chromium) | Playwright, avec feature flags admin activés (`ADMIN_COSTS_PAGE_ENABLED`, etc.) |

Ordre respecté : lint avant build/tests (le moins cher d'abord), conforme au principe
"build passe avant les tests" — ici lint avant tout, import smoke-test avant la suite
complète.

## Suite Python (`tests/`)

- **63 fichiers** de test, organisés par module/feature (`test_<module>.py`), pas par
  couche architecturale stricte (pas de séparation explicite unit/integration/e2e par
  dossier).
- **Markers pytest** (`pytest.ini`) :
  - `integration` — tape un vrai service externe (Supabase, OpenRouter, Composio...),
    nécessite des credentials live, **pas exécuté par défaut en CI**.
  - `slow` — setup de fixtures lourd ou pipelines multi-rounds.
- **Couverture** : `--cov-fail-under=28` sur `services`, `agents`, `models` — seuil bas,
  gate anti-régression plutôt qu'objectif de couverture. Ne pas remonter ce seuil sans
  plan concret (le remonter mécaniquement casserait la CI sans ajouter de valeur).
- **Env de test** : credentials factices (`SUPABASE_URL=https://example.supabase.co`,
  clés `test-*`), `ENVIRONMENT=development`, `RATE_LIMIT_ENABLED=0`.

## Suite frontend (`web/`)

- **Unitaire** : Vitest (`npm run test`).
- **E2E** : Playwright (`web/e2e/`), Chromium seul en CI, flags admin forcés à `1` pour
  couvrir les pages derrière feature flag.
- **Typecheck** : `tsc --noEmit` bloquant, séparé du lint.

## Ce qui manque (constat, pas un audit exhaustif)

- Pas de convention `[USER]`/`[ADMIN]`-style pour préfixer les tests d'autorisation —
  non prioritaire vu l'absence de système de rôles multi-utilisateurs dans le Hub
  aujourd'hui (accès protégé par `X-Hub-Key`, pas par rôle).
- Pas de séparation dossier par couche (`unit/`, `service/`, `repository/`) — les tests
  sont nommés par feature. Cohérent avec un projet solo à itération rapide ; à
  reconsidérer seulement si la confusion devient un problème réel.
- Aucun test dédié trouvé pour la vérification `X-Hub-Key` en environnement
  non-`development` mal configuré (voir `BUGS.md`) au moment du bootstrap — à confirmer
  lors du prochain audit de sécurité plutôt qu'assumé ici.
