# SPEC — Context Engine L1–L4 + Collective (Phase F / AAF)

> Contrat : tout prompt agent compile **L1→L4** dans cet ordre.
> L4 (working) est **wipé** en fin de Task. Promotion collective L3→L2
> si ≥N agents du même bureau apprennent la même leçon.
>
> **Statut :** implémenté 2026-08-10 · **DEC-027**.
> Dépend : Loop Engine (C) pour feedback L4 ; Mem0 + bibliothèque bureau
> déjà en place (pas un 2ᵉ store vectoriel).

---

## 1. Couches

| Layer | Contenu | Source | Durée |
|-------|---------|--------|--------|
| **L1** | Policies Enterprise (courtes, immuables) | `config/enterprise_policies.py` | Toujours |
| **L2** | Standards bureau + catalogue library | room + `get_library_context` | Bureau |
| **L3** | Leçons agent (Mem0) | `get_learning_context` | Agent |
| **L4** | Working : tentative + feedback loop | `services/working_memory.py` | Task only |

---

## 2. API compile

```python
compile_context(agent_id, task, *, task_id=None, loop_feedback=None) -> ContextBundle
compile_context_block(...) -> str  # injecté dans le prompt
```

`inject_learning_context` délègue à ce moteur (rétrocompat).

---

## 3. Promotion collective

Si **≥ `COLLECTIVE_PROMOTE_MIN_AGENTS` (3)** agents distincts du **même room**
enregistrent une leçon au même fingerprint → écrire L2 :
- Mem0 `bureau:{room}`
- `data/collective_lessons.json`

---

## 4. Wipe L4

`wipe_working_memory(task_id)` à la fin de chaque step plan / loop task
(succès ou échec) — pas de contamination entre missions.

---

## 5. Critères d’acceptation

1. Compile contient marqueurs L1…L4 (L4 vide OK si pas de task_id).
2. Feedback loop apparaît en L4.
3. Wipe L4 → plus de contenu pour ce `task_id`.
4. 3 agents même room, même leçon → entrée collective L2.
5. `pytest tests/test_context_engine.py` vert.

---

## 6. Hors scope

Neo4j / Knowledge Graph AAF complet ; wipe Mem0 L3 (jamais).
