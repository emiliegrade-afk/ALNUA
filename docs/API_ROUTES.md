# ALNUA Hub — API route map

Canonical vs legacy endpoints. **Legacy routes stay until clients migrate** (minimum one release).

Last updated: Phase 4 assainissement.

---

## Briefing

| Action | Canonical | Legacy (deprecated) |
|--------|-----------|---------------------|
| Today's operational briefing | `GET /briefing/today` | `GET /brief/today` (COO-shaped dashboard JSON) |
| History | `GET /briefing/history` | — |
| Generate operational (+ optional orchestration if flag) | `POST /briefing/generate` | — |
| Morning pipeline (COO + Telegram) | `POST /orchestration/morning` | `POST /briefing/morning-run` |
| COO executive brief (LLM) | `POST /services/briefing/daily` | `POST /services/briefing/quick` |
| COO tab UI gate | flag `BRIEFING_COO_SECTION_ENABLED` | — |
| Unified generate | flag `BRIEFING_UNIFIED_GENERATE` → `POST /briefing/generate` also runs orchestration | — |

**Facade:** `services/facades/briefing_facade.py` — operational reads + COO brief + flag helpers.

---

## Finances

| Action | Canonical | Legacy (deprecated) |
|--------|-----------|---------------------|
| List/create/update/delete transactions | `/finances/transactions` | `POST /transactions` |
| Monthly summary | `GET /finances/summary/{month}` | was implemented in `rnd.py` (removed Phase 4) |
| Force regenerate summary | `POST /finances/summary/generate` | was in `rnd.py` |
| Dashboard aggregates | `GET /finances/dashboard` | was in `rnd.py` |
| SaaS spend (live + catalogue) | `GET /finances/saas-spend` | Phase 34 |
| Invoice ledger | `GET/POST /finances/invoices`, `PATCH /finances/invoices/{id}` | no agent payment |
| Revolut read-only | `GET /finances/revolut/status` | needs `REVOLUT_ACCESS_TOKEN` |

**Router:** `api/routers/finances.py` (transactions + summaries + SaaS/invoices).  
**Agents:** `POST /agents/accounting/advice`, `GET /agents/accounting/invoices` ; Rémi via `/agents/controller/*`.  
**Note:** URLs unchanged for clients; only the owning router changed.

---

## Costs (LLM spend)

| Action | Canonical | Notes |
|--------|-----------|-------|
| Daily / week / month | `/costs/day`, `/costs/week`, `/costs/month` | Via `costs_facade` when shadow/unified flags set |
| Admin services | `/services/costs/*` | Tier-3 admin UI |
| Migration flags | `COSTS_UNIFIED_READ`, `COSTS_SHADOW_COMPARE` | Surfaced on `/admin/costs` |

**Facade:** `services/facades/costs_facade.py`

---

## Orchestration vs Autonomy

| Domain | Prefix | Use for |
|--------|--------|---------|
| n8n / cron workflows | `/orchestration/*` | morning, sentry-ingest, content sprint, PRD decompose |
| CEO / NUAWAY ops cockpit | `/autonomy/*` | nuaway-gate, readiness, bootstrap |

Some capabilities overlap historically — prefer **orchestration** for scheduled jobs, **autonomy** for CEO-facing ops reads.

---

## R&D

| Action | Router |
|--------|--------|
| Dossiers, comité, CEO package, product pages | `api/routers/rnd.py` |
| Arbres / hypothèses R&D | `api/routers/rnd_trees.py` (split Phase D) |
| Finance summaries | `api/routers/finances.py` uniquement (retiré de `rnd.py`, phase 4) |

---

## Trust / Quality / Cross-dept (Phase E MVP)

| Action | Canonical |
|--------|-----------|
| Trust scores | `GET /agents/trust`, `GET /agents/trust/{agent_id}` |
| Quality gate thresholds | `GET /quality-gates` |
| Review board (structural) | `POST /review-board/evaluate` |
| Cross-dept work queue | `GET /cross-dept/queue` |
| Validation recipes | `POST /workflows/run` with `content_validation` / `campaign_validation` |

**Router:** `api/routers/trust.py`. Trust ≠ competition (`DEC-011`).

---

## GDD (gaming)

| Action | When |
|--------|------|
| `/gdd/*` | Router mounted **only if** `GDD_MANAGER_ENABLED=1` at process start |

---

## Beta portal

| Public (no hub key) | Admin (hub key) |
|---------------------|-----------------|
| `GET /beta/info/{slug}`, `POST /beta/register`, `POST /beta/feedback` (JWT), `GET /beta/my-feedback` (JWT) | `/beta/testers`, `/export`, `GET /beta/feedback`, `/stats`, `POST /invite` |

---

## Webhooks

| Path | Auth |
|------|------|
| `POST /webhook/sentry` | `Sentry-Hook-Signature` or `SENTRY_WEBHOOK_ALLOW_UNSIGNED=1` (dev) |
| `POST /webhook/telegram` | `X-Telegram-Bot-Api-Secret-Token` when `TELEGRAM_WEBHOOK_SECRET` set |
| `POST /orchestration/sentry-ingest` | `X-Hub-Key` (trusted relay) |

---

## Adding routes

1. Pick the **canonical** router (avoid god routers).
2. If replacing an endpoint, keep the old path one release with `deprecated=True`.
3. Update this file in the same PR.
