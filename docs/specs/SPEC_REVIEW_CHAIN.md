# SPEC — Review Chain + Merge (Phase D / AAF)

> Contrat : **gates auto → board → policy → integrate → done**.
> Auto toujours avant humain (ADR-012 AAF). Pas de 2ᵉ workflow engine (DEC-012).
>
> **Statut :** implémenté 2026-08-10 · **DEC-025**.
> Dépend : Isolation (A), Mission Graph (B), Loop Engine (C).
> Hors scope : PermissionGuard / Capability Packs (Phase E).

---

## 1. Objectif

Unifier les chemins « on merge ? » (coding, fix_pipeline, ship, Mission) sous
une **Review Chain** ordonnée + règles d’autonomie merge (staging vs main).

---

## 2. Chaîne ordonnée

```
AUTO → BOARD → POLICY → INTEGRATE? → DONE
  ↓ fail     ↓ reject   ↓ deny
 REJECT / A_VERIFIER / BLOCKED_POLICY
```

| Étape | Contenu |
|-------|---------|
| `AUTO` | lint / tsc / pytest / quality_gates — fail-fast |
| `BOARD` | `review_board` (+ QA/Spec déjà faits injectables) |
| `POLICY` | `merge_policy` + autonomie cible (DEC-025) |
| `INTEGRATE` | obligatoire si **N>1** feature branches → `dev_integrator` |
| `DONE` | `event_bus` `review_chain.completed` |

---

## 3. Autonomie merge (cibles)

| Cible | Règle |
|-------|--------|
| Academy / lab | auto si gates vertes (existant) |
| `staging` | auto si trust producer ≥ `REVIEW_CHAIN_STAGING_TRUST_MIN` (0.70) |
| `main` / `master` | jamais auto idle — humain / CEO / hotfix allowlist |
| ads / finances / publish | toujours humain |

Acteur merge protégé : toujours Phase A (`dev_integrator` / allowlist).

---

## 4. API

```
POST /review-chain/run
GET  /review-chain/defaults
```

---

## 5. Critères d’acceptation

1. AUTO fail → chaîne stoppe avant BOARD.
2. N>1 branches → INTEGRATE requis ; conflits → reject + feedback.
3. `main` sans `human_approved` → `human_required` (pas d’auto-merge).
4. `staging` + trust ≥ seuil → auto autorisé (si actor allowlist OK).
5. `pytest tests/test_review_chain.py` vert (inclut E2E dry-run
   2 PR → integrate → staging + `mission_ship`).

---

## 6. Hors scope

Capability Packs, PermissionGuard MCP (Phase E), mémoire L1–L4 (Phase F).
Git réel / `gh` network (dry-run + `integrate_fn` mockent le merge).
