# SPEC — Loop Engine (Phase C / AAF)

> Contrat : **exécute → évalue → feedback brut → ré-exécute** jusqu’à
> `max_iterations`, sinon escalade. Un seul FSM pour fix_pipeline, Mission
> Graph et étapes workflow retryables.
>
> **Statut :** implémenté 2026-08-10 · **DEC-024**.
> Dépend : Phase A isolation (DEC-022), Phase B Mission Graph (DEC-023).

---

## 1. Objectif

Généraliser le loop de `fix_pipeline` (tests/QA/Spec → retry) en service
commun `services/loop_engine.py` — pas un second workflow engine (DEC-012).

---

## 2. FSM

```
PENDING → EXECUTING → EVALUATING → COMPLETED
                   ↘ REJECT → EXECUTING (iteration++)
                   ↘ FATAL / max → ESCALATED | FAILED
```

| État | Signification |
|------|----------------|
| `PENDING` | Créé, iteration 0 |
| `EXECUTING` | Producteur en cours |
| `EVALUATING` | Gates / review |
| `COMPLETED` | Approuvé |
| `FAILED` | Fatal non retryable |
| `ESCALATED` | Cap itérations atteint |

Transitions illégales rejetées (`IllegalTransitionError`).  
Rejet **sans** feedback → erreur (AAF : Mandatory Feedback).

---

## 3. Feedback

- Append-only `feedback_log[]` (jamais écrasé).
- Contenu : stdout tests, message QA/Spec, stack — pas « try again ».
- Injecté dans le contexte d’exécution suivant (`LoopContext.last_feedback` + historique).

---

## 4. Caps

| Setting | Défaut | Usage |
|---------|--------|--------|
| `LOOP_MAX_ITERATIONS` | 3 | défaut (aligné watchdog) |
| `LOOP_STRICT_MAX_ITERATIONS` | 2 | merge / deploy / `ship_*` / `dev_integrator` / `fix_pipeline` |
| `LOOP_RETRY_SLEEP_S` | 0 | pause entre itérations (fix_pipeline peut surcharger) |

Helpers : `is_strict_loop(...)` + `resolve_max_iterations(strict=...)`.
Surfaces strictes → plafond `min(override, LOOP_STRICT_MAX_ITERATIONS)`.

---

## 5. Intégrations

| Surface | Comportement |
|---------|--------------|
| `fix_pipeline` | `run_loop_async` — execute=fix ; evaluate=tests+QA+Spec ; **cap strict** |
| `plan_executor` / Mission Graph | `run_loop` ; merge/integrator → **cap strict** |
| `workflow_engine` | `RETRYABLE` ; recettes `ship_*` → **cap strict** ; `ECART` = humain |

---

## 6. Critères d’acceptation

1. FSM : `PENDING→COMPLETED` sans skip `EVALUATING`.
2. Rejet sans feedback → exception.
3. Cap 3 → `ESCALATED`, pas de 4ᵉ execute.
4. Parcours tests KO → feedback dans contexte → OK → `COMPLETED`.
5. Merge/integrator/ship → plafond `LOOP_STRICT_MAX_ITERATIONS`.
6. `pytest tests/test_loop_engine.py` vert.

---

## 7. Hors scope

Capability Packs, PermissionGuard MCP (Phase E — voir
`docs/specs/SPEC_CAPABILITY_GUARD.md`), mémoire L1–L4 (Phase F).
