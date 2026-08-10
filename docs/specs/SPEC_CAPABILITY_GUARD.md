# SPEC — Capability Packs + PermissionGuard (Phase E / AAF)

> Contrat : **Capability ≠ Skill**. Le LLM peut proposer un tool ; le Guard
> décide. Fail-closed (inconnu = deny). Journal append-only → Trust Graph.
>
> **Statut :** implémenté 2026-08-10 · **DEC-026**.
> Dépend : Isolation (A), Review Chain merge policy (D).
> Trust Score (`agent_trust`, DEC-011) reste distinct du Trust Graph.

---

## 1. Objectif

Empêcher un side-effect sensible sans capability explicite dans le pack du rôle
(agent), indépendamment de ce que le prompt « veut ».

---

## 2. Catalogue (MVP)

| Capability | Sens |
|------------|------|
| `git:commit` | Commit local |
| `git:push:feature` | Push branche feature |
| `git:merge:staging` | Merge vers staging |
| `git:merge:main` | Merge vers main/master |
| `github:pr:create` | Ouvrir PR |
| `github:pr:merge` | Merger PR via gh |
| `coding:worktree` | Créer/utiliser worktree |
| `data:write:path` | Écrire fichiers data/ runtime |
| `ads:spend` | Dépenser budget ads |
| `mail:send` | Envoyer email |
| `workflow:abort` | Aborter un workflow/run |
| `system:hotfix` | Bypass hotfix (fix_pipeline) |

---

## 3. Packs

`config/capability_packs.py` — `agent_id` → set de capabilities.  
Ex. `dev_frontend` : worktree + PR, **pas** `git:merge:main`.  
`dev_integrator` : `git:merge:staging` (+ PR merge).  
`fix_pipeline` : `system:hotfix` + `git:merge:main`.

---

## 4. PermissionGuard

`services/permission_guard.py` :

```
require_capability(agent_id, capability, *, resource=None, meta=None)
→ None | raise PermissionDeniedError
```

- `PERMISSION_GUARD_ENABLED=1` → fail-closed
- Toute décision (allow/deny) → `data/trust_graph.jsonl`

---

## 5. Trust Graph vs Trust Score

| | Trust Score | Trust Graph |
|---|-------------|-------------|
| Store | `agent_trust.json` | `trust_graph.jsonl` |
| Sens | Fiabilité 0–1 (DEC-011) | Audit allow/deny |
| UI | jauges `/trust` | décisions récentes |

---

## 6. Critères d’acceptation

1. `dev_app` + `git:merge:main` → deny + log ; pas de side-effect.
2. `dev_integrator` + `git:merge:staging` → allow (+ log).
3. Capability inconnue → deny.
4. Guard off (`PERMISSION_GUARD_ENABLED=0`) → allow (compat).
5. `pytest tests/test_permission_guard.py` vert.

---

## 7. Hors scope

Neo4j Trust Graph (jsonl suffit pour MVP).
Mémoire L1–L4 : `docs/specs/SPEC_CONTEXT_ENGINE.md` (Phase F).

## 8. Call-sites MVP (post-livraison)

| Capability | Choke-point |
|------------|-------------|
| `mail:send` | `secretary_composio_gmail.send_email` + COO Gmail tool |
| `github:pr:create` | `_finalize_pr`, `open_integration_pr`, `create_pr` |
| `github:pr:merge` | `merge_pr_if_allowed` |
| `git:commit` / `git:push:feature` | `coding_isolation`, `commit_and_push`, `_finalize_pr` |
| `workflow:abort` | `abort_mission`, `abort_workflow_run` (+ API) |
| `ads:spend` / merge / worktree | déjà Phase E initiale |

## 9. MCP PermissionGuard (progressif)

Quand le client s’identifie (`X-MCP-Agent` ou `X-MCP-Client: 1`) :

1. Middleware `api/middleware_mcp.py` intercepte les routes mappées
   (`config/mcp_capability_routes.py`).
2. `require` via `check_capability` → 403 + Trust Graph si deny.
3. Pack `cursor` / `mcp_client` = fail-closed (data:write seul).
4. Setting `PERMISSION_GUARD_MCP_ENABLED` (dépend aussi de
   `PERMISSION_GUARD_ENABLED`).
5. Routes non mappées : call-sites existants uniquement (extension progressive).

Critères :
- `cursor` + POST `/agents/ads/create-campaign` → 403
- `ads` + même route → allow (middleware)
- Sans header MCP → pas d’interception middleware
- `pytest tests/test_mcp_permission_guard.py` vert
