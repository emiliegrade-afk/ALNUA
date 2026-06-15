# Assainissement ALNUA Hub — dossier de synthèse

Rapport consolidé des problèmes identifiés lors de l’audit (juin 2026) et des corrections livrées en **phases 0 à 6**.

## Documents

| Fichier | Contenu |
|---------|---------|
| [PROBLEMES_CORRECTIONS.md](./PROBLEMES_CORRECTIONS.md) | Tableau détaillé problème → correction par phase |
| [RESTE_A_FAIRE.md](./RESTE_A_FAIRE.md) | Dette reportée et follow-ups optionnels |
| [CONFIGURATION_CLES.md](./CONFIGURATION_CLES.md) | Où placer `HUB_API_KEY` (local, Next, Cursor MCP) |
| [../API_ROUTES.md](../API_ROUTES.md) | Carte des routes API (canon vs legacy, phase 4) |

## Verdict (état actuel)

| Check | Résultat |
|-------|----------|
| `pytest tests/` | 202 passed, 2 skipped |
| `web`: `npx tsc --noEmit` | OK |
| `web`: `npm run lint` | OK |

## Principes du plan

1. Sécurité avant refactor
2. Une phase = mergeable (CI verte)
3. Tests de non-régression par fix P0/P1
4. Personas : une source de vérité (`config/agent_personas.py`)

## Tests de garde ajoutés

| Fichier | Phase |
|---------|-------|
| `tests/test_facades_phase0.py` | 0 |
| `tests/test_security_phase1.py` | 1 |
| `tests/test_admin_phase1.py` | 1 |
| `tests/test_runtime_phase2.py` | 2 |
| `tests/test_briefing_phase2.py` | 2 |
| `tests/test_gdd_phase3.py` | 3 |
| `tests/test_api_routes_phase4.py` | 4 |
| `tests/test_personas_phase5.py` | 5 |
| `tests/test_devex_phase6.py` | 6 |

## Vérification rapide

```bash
# Backend
.venv\Scripts\python.exe -m pytest tests/ -q

# Frontend
cd web && npx tsc --noEmit && npm run lint
```

## Variables d’environnement introduites / documentées

```
SENTRY_WEBHOOK_SECRET, SENTRY_WEBHOOK_ALLOW_UNSIGNED
TELEGRAM_WEBHOOK_SECRET
SCHEDULER_LEADER, SCHEDULER_TIMEZONE
COSTS_UNIFIED_READ, COSTS_SHADOW_COMPARE
GDD_MANAGER_ENABLED
HUB_API_KEY (optionnel en development côté backend)
```
