# SPEC — Mission Graph (Phase B / AAF)

> Contrat : un **graphe unique** Mission → Tasks (`depends_on`) pour le travail
> séquentiel et parallèle multi-agents. Façade sur `plan_executor` + isolation
> Phase A (DEC-022) — **pas** un second moteur (DEC-012 / DEC-023).
>
> **Statut :** implémenté 2026-08-10 · **DEC-023**.
> Suite : Loop Engine (Phase C) — hors scope.

---

## 1. Objectif

Unifier `plan_executor` / tickets / `workflow_runs` dispersés sous un agrégat
**Mission** consultable (API + OpenRoom) :

```
Mission
  └─ Projects? (optionnel, milestones)
       └─ Tasks[]  — assignee, depends_on[], status, lock_keys, workspace hint
```

---

## 2. États

### Task

| Statut | Signification |
|--------|----------------|
| `PENDING` | Créée, deps non satisfaites |
| `READY` | Deps OK, en file |
| `EXECUTING` | Agent en cours (+ isolation lease) |
| `COMPLETED` | Succès |
| `FAILED` | Échec après retries plan |
| `BLOCKED` | Deps en échec / cycle |
| `A_VERIFIER` | Succès mais revue humaine (réservé Phase C/D) |
| `SKIPPED` | Annulée |

### Mission (dérivé)

| Statut | Règle |
|--------|--------|
| `DRAFTED` | Pas encore démarrée |
| `IN_PROGRESS` | ≥1 task EXECUTING/READY/COMPLETED, pas terminal |
| `BLOCKED` | Reste des tasks BLOCKED et rien d’exécutable |
| `COMPLETED` | 100 % tasks `COMPLETED` (ou SKIPPED) |
| `FAILED` | ≥1 `FAILED` et plus rien d’exécutable |
| `A_VERIFIER` | ≥1 `A_VERIFIER` et le reste terminal OK |

---

## 3. Dispatch

1. COO / API : `create` depuis objectif (`parse_coo_plan`) ou plan explicite.
2. `run` : batches parallèles des tasks `READY` (`depends_on` satisfaits),
   isolation Phase A, même `_execute_step` que `plan_executor`.
3. Persistance : `data/missions/{mission_id}.json` (gitignored).
4. Events : `mission.started` / `mission.task_finished` / `mission.completed`.

---

## 4. API

```
GET    /missions
GET    /missions/{id}
POST   /missions                 — { objective, context? } | { title, tasks[] }
POST   /missions/{id}/run        — exécute (sync MVP)
POST   /missions/from-plan       — { title, objective?, steps[] }
```

---

## 5. OpenRoom

Overlay : tasks `EXECUTING` → agent `working` + `missionId` / `taskId` / progress.

---

## 6. Critères d’acceptation

1. Mission 2 tasks indépendantes → exécution parallèle (même run).
2. Task B `depends_on` A → B n’exécute qu’après A `COMPLETED`.
3. Échec A → B passe `BLOCKED` ; Mission `FAILED` ou `BLOCKED`.
4. `GET /missions/{id}` reflète le graphe + statuts.
5. `pytest tests/test_mission_graph.py` vert.

---

## 7. Hors scope

Loop Engine (retry + feedback L4), Review Chain merge, Capability Packs.
