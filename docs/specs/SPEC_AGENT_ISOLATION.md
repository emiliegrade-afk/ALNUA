# SPEC — Agent Isolation (Phase A / AAF)

> Contrat : les agents ALNUA travaillent **sans se marcher dessus**.
> Isolation = resource locks + slots de concurrence + règle intégrateur.
>
> **Statut :** implémenté 2026-08-10 · **DEC-022**.
> Suite : Mission Graph (Phase B) + Loop Engine (Phase C) — hors scope.

---

## 1. Objectif

Quand N agents tournent en parallèle (coding, plan COO, idle, parallel_runner) :

1. **Pas d’overwrite** sur la même ressource (fichier, ticket, dossier, campagne).
2. **Parallélisme borné** (global / repo / agent).
3. **Merge protégé** : seuls l’intégrateur (et exceptions système documentées) touchent
   `main` / `master` / `staging`.

---

## 2. Règles (non négociables)

| ID | Règle |
|----|--------|
| A1 | 1 Task active = 1 Agent = 1 Workspace (worktree coding ou ownership artifact) |
| A2 | Acquire lock **avant** side-effect ; release au terminal (OK / fail / timeout) |
| A3 | Fail-closed : lock indisponible après wait → pas d’exécution |
| A4 | 2 agents, mêmes fichiers/ticket → 2ᵉ en file (wait) puis deny si timeout |
| A5 | Même repo, fichiers disjoints → OK si slots repo disponibles |
| A6 | Merge `main`/`master`/`staging` → `dev_integrator` (ou rôles système allowlist) |

---

## 3. Resource locks

Service : `services/resource_locks.py`  
Store : `data/resource_locks.json` (runtime, gitignored)

### Clés

| Forme | Exemple |
|-------|---------|
| `ticket:{id}` | `ticket:42` |
| `dossier:{id}` | `dossier:uuid` |
| `campaign:{id}` | `campaign:abc` |
| `path:{rel}` | `path:web/src/app/page.tsx` |
| `data:{file}` | `data:idle_queue.json` |
| `task:{id}` | `task:ISSUE-12` |

TTL par défaut : `ISOLATION_LOCK_TTL_S` (expire → purge au prochain acquire).

---

## 4. Execution slots

Service : `services/execution_slots.py`

| Limite | Env | Défaut |
|--------|-----|--------|
| Global | `ISOLATION_MAX_GLOBAL` | 8 |
| Par repo | `ISOLATION_MAX_PER_REPO` | 2 (= `CODING_MAX_PARALLEL`) |
| Par agent | `ISOLATION_MAX_PER_AGENT` | 1 |

Acquire bloque jusqu’à `wait_s` (file), puis lève `SlotBusyError`.

---

## 5. Merge policy

Service : `services/merge_policy.py`

Branches protégées : `main`, `master`, `staging`.

| Acteur | Autorisé |
|--------|----------|
| `dev_integrator` | Oui (staging/main) |
| `fix_pipeline` | Oui si `ISOLATION_FIX_PIPELINE_MERGE=1` (hotfix watchdog) |
| `coding_pipeline` / `gh_issues` | Academy seulement (auto-merge existant) |
| Autres agents | **Non** — PR only |

---

## 6. Points d’intégration

| Surface | Comportement |
|---------|--------------|
| `skills/coding_agent_*` | Lease locks (task + paths) + slot repo avant worktree |
| `services/parallel_runner_*` | Lease par tâche (clés inférées / `lock_keys`) |
| `services/plan_executor_*` | Idem sur chaque step |
| `agents/fix_pipeline_git` | `assert_can_merge` avant merge |
| `services/coding_pipeline.merge_pr_if_allowed` | Policy + agent_id |

API : `GET /isolation/locks`, `GET /isolation/slots`, `POST /isolation/locks/release`.

---

## 7. Critères d’acceptation

1. Deux coding tasks, mêmes `files_to_modify` → la 2ᵉ attend ou échoue `LockBusyError` (pas d’overwrite).
2. Deux tasks, fichiers disjoints, même repo → 2 worktrees si `MAX_PER_REPO` ≥ 2.
3. `max_per_agent=1` → un agent ne lance pas 2 EXECUTING simultanés.
4. Agent `dev_app` tentant merge `main` → deny.
5. `pytest tests/test_agent_isolation.py` vert.

---

## 8. Hors scope (phases suivantes)

Loop Engine (retry + feedback), Mission Graph unifié, Capability Packs / PermissionGuard,
mémoire L1–L4 — voir plan AAF d’intégration Hub.
