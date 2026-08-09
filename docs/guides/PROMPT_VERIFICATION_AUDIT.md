# ALNUA — Prompt Verification Audit

Checklist de vérification pour les pipelines agents autonomes.

## Phase 0 — Audit automatisé

```bash
python scripts/audit_autonomy_phase0.py
```

## Phase 1 — Coding pipeline renforcé

- [ ] `services/coding_pipeline.py` — config, `detect_stack`, `merge_pr_if_allowed`
- [ ] `config/settings.py` — `CODING_TIMEOUT_S` (3600), `CODING_MAX_TURNS` (60), `CODING_MAX_PARALLEL` (2)
- [ ] `CODING_AUTO_MERGE` / `CODING_MERGE_BASE_BRANCH` dans `.env` (staging par défaut)
- [ ] `skills/skill_coding_agent.py` lit la config dynamique + prompts par stack
- [ ] `skills/skill_gh_issues.py` — parallélisme semaphore + auto-merge post-QA
- [ ] `GITHUB_REPO_ACADEMY` + `REPO_PATH_ACADEMY` pour l'académie (Phase 2)
- [ ] `tests/test_coding_pipeline.py` passe

## Phase 2 — Académie ALNUA

```bash
python scripts/seed_academy_issues.py --level 1 --mark-ready
python scripts/academy_benchmark.py
```

- [ ] `services/academy_curriculum.py` — 52 exercices N1→N4
- [ ] `services/academy_progress.py` — manifest `data/academy_progress.json`
- [ ] `services/academy_seed.py` — seed GitHub + sprint agent-ready
- [ ] `GET /academy/status` + `POST /academy/seed` + `POST /academy/sprint`
- [ ] `POST /orchestration/academy-sprint` + n8n `08-academy-sprint.json`
- [ ] Cockpit `/hub` — `AcademyCockpit`
- [ ] `tests/test_academy.py` passe
- [ ] Pipeline UI utilise `process_issue` (coding_agent) pas OpenHands

## Phase 4 — Ops production (Sentry → issues)

```bash
python -m pytest tests/test_sentry_ops.py -q
curl -X POST http://localhost:8000/ops/production/simulate -H "X-Hub-Key: $HUB_API_KEY" -H "Content-Type: application/json" -d "{\"title\":\"Test crash\"}"
```

- [ ] `services/sentry_ops.py` — parse webhook, dedup, hotfix issue
- [ ] `services/production_ops.py` — orchestration + status
- [ ] `POST /webhook/sentry` (sans X-Hub-Key, signature HMAC)
- [ ] `GET /ops/production/status` + cockpit `/hub`
- [ ] `POST /orchestration/sentry-ingest` + n8n `09-sentry-to-hotfix.json`
- [ ] `SENTRY_WEBHOOK_SECRET` + `SENTRY_AUTO_ISSUE` dans `.env`
- [ ] `tests/test_sentry_ops.py` passe
- [ ] bug_watchdog consomme les entrées `agent_error_journal` créées par Sentry

## Phase 5 — Cockpit CEO + Gate NUAWAY

```bash
python -m pytest tests/test_nuaway_gate.py tests/test_ceo_cockpit.py -q
curl -H "X-Hub-Key: $HUB_API_KEY" http://localhost:8000/autonomy/ceo-cockpit
curl -X POST -H "X-Hub-Key: $HUB_API_KEY" http://localhost:8000/autonomy/nuaway-gate/evaluate
```

- [ ] `services/nuaway_gate.py` — 8 critères, `evaluate_nuaway_gate()`, persistance `data/academy_progress.json`
- [ ] `services/ceo_cockpit.py` — agrégateur gate + académie + ops + file CEO
- [ ] `GET /autonomy/ceo-cockpit` + `GET|POST /autonomy/nuaway-gate`
- [ ] Cockpit `/hub` — `CeoCockpitPanel` + `autonomy-api.ts`
- [ ] `AcademyCockpit` — critère `error_journal_top5` + badge `gate_open`
- [ ] `daily_briefing` injecte `nuaway_gate` dans collecte + `raw_data`
- [ ] `POST /orchestration/nuaway-gate` + n8n `10-nuaway-gate-check.json`
- [ ] `tests/test_nuaway_gate.py` + `tests/test_ceo_cockpit.py` passent

## Phase 6 — Gate readiness beta NUAWAY

```bash
python scripts/nuaway_readiness_audit.py
python -m pytest tests/test_nuaway_readiness.py -q
curl -H "X-Hub-Key: $HUB_API_KEY" http://localhost:8000/autonomy/nuaway-readiness
curl -X POST -H "X-Hub-Key: $HUB_API_KEY" http://localhost:8000/autonomy/nuaway-readiness/report
```

- [ ] `services/nuaway_readiness.py` — checklist beta 8 critères + `beta_ready`
- [ ] `data/nuaway_readiness.json` — go CEO persisté
- [ ] `GET /autonomy/nuaway-readiness` + `POST .../report` + `POST .../ceo-go`
- [ ] Cockpit `/hub` — checklist beta + bouton **Go beta CEO**
- [ ] `POST /orchestration/nuaway-readiness-report` + n8n `11-nuaway-readiness-report.json`
- [ ] `scripts/nuaway_readiness_audit.py` — audit CLI
- [ ] `tests/test_nuaway_readiness.py` passe

## Phase 7 — Bootstrap ops NUAWAY

```bash
.\scripts\setup_nomad.ps1
.\scripts\bootstrap_nuaway_ops.ps1 -Port 8003
curl -H "X-Hub-Key: $HUB_API_KEY" http://localhost:8003/autonomy/nuaway-bootstrap
```

- [ ] `scripts/setup_nomad.ps1` — clone NUAWAY + `REPO_PATH_NOMAD` dans `.env`
- [ ] `scripts/bootstrap_nuaway_ops.ps1` — audit Phase 0 + readiness + diagnostic
- [ ] `scripts/restart_hub_api.ps1` — kill par port (zombies uvicorn)
- [ ] `services/nuaway_bootstrap.py` — diagnostic + `next_steps`
- [ ] `GET /autonomy/nuaway-bootstrap` + `POST /orchestration/nuaway-bootstrap`
- [ ] Briefing COO inclut `beta_ready` + `missing_critical`
- [ ] `tests/test_nuaway_bootstrap.py` passe

## Error journal & retry loop

- [ ] `skills/skill_error_journal.py` existe et expose `log_error`, `search_similar_errors`, `mark_resolved`, `get_open_errors_summary`
- [ ] `skills/skill_retry_loop.py` existe et expose `retry_with_learning`, `classify_error`
- [ ] Table Supabase `agent_error_journal` créée (migration `20260611140000_agent_error_journal.sql`)
- [ ] Fonction RPC `increment_error_attempts` déployée sur Supabase
- [ ] `execute_coding_task` dans `skills/skill_coding_agent.py` utilise `retry_with_learning` (max 3 tentatives)
- [ ] `_execute_coding_task_core` contient la logique worktree/Claude/PR sans retry
- [ ] `agents/dev_gaming_agent.py` : `nwiro_execute_tool` et `nwiro_prompt_tool` utilisent le retry
- [ ] `agents/embedded_dev_agent.py` : `pi_ssh_tool` utilise `execute_pi_ssh_with_retry`
- [ ] `agents/coo_agent.py` : `get_daily_briefing()` inclut `get_open_errors_summary()`
- [ ] Notifications Telegram sur retry / escalade COO (si `telegram_notify_fn` configuré)

## Agents concernés

| Agent | Fichier | Mécanisme retry |
|-------|---------|-----------------|
| DevApp | `skills/skill_coding_agent.py` | `retry_with_learning` |
| DevGaming | `agents/dev_gaming_agent.py` | Nwiro + coding agent |
| EmbeddedDev | `agents/embedded_dev_agent.py` | SSH + coding agent |
| R&D | *(à créer)* | Doit réutiliser `retry_with_learning` |

## Test manuel

1. Créer une issue GitHub avec description volontairement floue (label `agent-ready`)
2. Lancer le pipeline DevApp
3. Vérifier entrée dans `agent_error_journal` (status `open`)
4. Vérifier notification Telegram retry
5. Après succès : status `resolved` + solution renseignée
6. Après 3 échecs : status `escalated` + notification COO
7. Briefing matinal COO : section erreurs ouvertes visible
