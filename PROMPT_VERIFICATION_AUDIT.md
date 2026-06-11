# ALNUA — Prompt Verification Audit

Checklist de vérification pour les pipelines agents autonomes.

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
