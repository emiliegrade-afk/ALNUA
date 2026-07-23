# Use case — Pipeline coding autonome

## Objectif
Issue GitHub → worktree → agent code → QA (tsc/pytest) → Spec review → PR → auto-merge.

## Flow
1. **BugWatchdog** ou poll issues détecte une erreur
2. **fix_pipeline** boucle itérative (max 3 tentatives)
3. **Coding QA** : `tsc --noEmit` / `pytest`
4. Merge sur staging (academy) ou main (config)

## Configuration `.env`
```env
CODING_BACKEND=hub
CODING_QA_REQUIRED=1
CODING_AUTO_MERGE=0
CODING_ACADEMY_AUTO_MERGE=1
TEST_COMMAND=pytest tests/ -v --tb=short
```

## Monitoring
- `data/coding_errors.json` — journal erreurs
- Sentry webhook → hotfix automatique

## Test local
```bash
python scripts/test_fix_pipeline.py
pytest tests/test_fix_pipeline.py -v
```
