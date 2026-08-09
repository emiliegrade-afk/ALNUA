# Problèmes et corrections — assainissement phases 0→6

> Audit initial : bugs CI, sécurité, frictions runtime/UX, dette API, incohérences personas, DevEx.
> Dernière mise à jour : juin 2026.

---

## Phase 0 — Stabilisation CI & onboarding

**Objectif :** CI locale et distante verte, dev onboarding sans piège.

| # | Problème | Correction | Fichiers |
|---|----------|------------|----------|
| 0.1 | `tsc` échoue — itération sur `Set` dans `hq-prefetch.ts` | `Array.from(new Set(...))` | `web/src/lib/hq-prefetch.ts` |
| 0.2 | Proxy Next peut boucler sur lui-même si `HUB_API_BACKEND_URL` absent et fallback sur `NEXT_PUBLIC_API_URL` | `hubBackendBaseUrl()` ne tombe **jamais** sur `/api/hub` ; défaut `http://localhost:8000` | `web/src/lib/hub-api-config.ts` |
| 0.3 | Doc env Next incomplète | `web/.env.example`, `web/README.md` | idem |
| 0.4 | `composio` manquant en venv local | Install via `requirements.txt` (déjà listé) | — |
| 0.5 | Tests CreatorFlow : mocks sur mauvais chemin (`services.*` au lieu du router) | Patch `api.routers.creatorflow.*` | `tests/test_creatorflow_sprint4.py` |
| 0.6 | `test_phase0_feature_flags_default_safe` pollué par `.env` racine (flags à `1`) | `monkeypatch.setenv(key, "0")` explicite au lieu de `delenv` | `tests/test_facades_phase0.py` |
| 0.7 | Warnings ESLint hooks (`exhaustive-deps`) | Corrections ciblées | `finances-transaction-list.tsx`, `rnd-pitch-modal.tsx` |

**Critère done :** pytest + tsc + lint verts.

---

## Phase 1 — Sécurité

**Objectif :** aucune fuite PII admin beta, webhooks non spoofables en prod.

| # | Problème | Correction | Fichiers |
|---|----------|------------|----------|
| 1.1 | Routes beta admin accessibles sans `X-Hub-Key` | Seules routes **publiques** exemptées : `/beta/info/*`, `POST /beta/register`, `POST /beta/feedback` (JWT), `GET /beta/my-feedback` (JWT). Admin (`/beta/testers`, `/export`, `GET /beta/feedback`, `/stats`, `POST /invite`) **protégé** | `api/middleware.py` |
| 1.2 | Webhook Sentry acceptait payloads non signés | Refus sauf `SENTRY_WEBHOOK_ALLOW_UNSIGNED=1` (dev) ; vérif HMAC | `services/sentry_ops.py`, `services/production_ops.py`, `config/settings.py` |
| 1.3 | Webhook Telegram sans secret | Header `X-Telegram-Bot-Api-Secret-Token` requis en prod | `api/routers/releases.py`, `config/settings.py` |
| 1.4 | Ingest Sentry orchestration non marquée trusted | `trusted_relay=True` | `services/orchestration.py` |
| 1.5 | Comparaison clé Hub non timing-safe | `secrets.compare_digest` | `api/middleware.py` |
| 1.6 | Env non documentés | `SENTRY_WEBHOOK_SECRET`, `TELEGRAM_WEBHOOK_SECRET`, etc. | `.env.example`, `deploy/.env.prod.example` |

**Tests :** `tests/test_security_phase1.py`, `tests/test_admin_phase1.py`

---

## Phase 2 — Fiabilité runtime

**Objectif :** erreurs API visibles côté UI, pas de silence sur pannes.

| # | Problème | Correction | Fichiers |
|---|----------|------------|----------|
| 2.1 | OpenRoom : échec API silencieux (données vides) | `fetchAgentsStatus()` → `{ ok, data, error }` ; bannière amber | `web/src/lib/openroom-api.ts`, `openroom/page.tsx`, `lobby-view.tsx`, `bureau-agents-section.tsx` |
| 2.2 | Lobby : pas de feedback si refresh stats échoue | `refreshError` sur stats + bannière | `web/src/lib/lobby-api.ts`, `lobby-view.tsx` |
| 2.3 | `fetchCeoQueue` : fallback silencieux sur erreur non-404 | `throw` sur erreurs réseau/API (404 seul → liste vide) | `web/src/lib/rnd-dossier.ts` |
| 2.4 | Supabase service role utilisé sans avertissement ; `insert_many` fragile | Log warning one-shot ; garde sur batch vide | `database/supabase_client.py` |
| 2.5 | Scheduler : TZ non configurée, multi-worker double-run | `SCHEDULER_TIMEZONE`, `SCHEDULER_LEADER` | `config/settings.py`, `api/lifespan.py` |
| 2.6 | BugWatchdog : arrêt brutal au shutdown | `stop_watchdog()` graceful | `agents/bug_watchdog.py`, `api/lifespan.py` |
| 2.7 | `GET /releases/generate` capturé par `/{release_id}` | Route `GET /releases/generate` → **405** avant `{id}` | `api/routers/releases.py` |

**Tests :** `tests/test_runtime_phase2.py`, `tests/test_briefing_phase2.py`

---

## Phase 3 — UX navigation

**Objectif :** retour lobby cohérent, admin sans doublons, routes legacy redirigées.

| # | Problème | Correction | Fichiers |
|---|----------|------------|----------|
| 3.1 | `/briefing` sans retour lobby | `BackToLobby` | `web/src/components/briefing/briefing-view.tsx` |
| 3.2 | Admin : double `BackToLobby` (page + shell) | Retiré de `admin/page.tsx` / `admin-shell` ; shell unique | `web/src/app/admin/page.tsx`, `admin-shell.tsx` |
| 3.3 | Preview admin flags sans `?preview=1` sur liens lobby | `withAdminPreview()` | `admin-flags-api.ts`, `lobby-view.tsx`, `admin/page.tsx` |
| 3.4 | `/brainstorm` orphelin | Redirect → `/rd?tab=brainstorm` ; lecture `?tab=` | `brainstorm/page.tsx`, `rd-page-content.tsx` |
| 3.5 | Helpers routes absents | `isAdminRoute`, `BRAINSTORM_LEGACY_PATH` | `web/src/lib/routes.ts` |

**Tests :** `tests/test_gdd_phase3.py` (contexte admin/GDD)

---

## Phase 4 — Dette API & documentation

**Objectif :** carte des routes, ownership clair, facades, flags exposés.

| # | Problème | Correction | Fichiers |
|---|----------|------------|----------|
| 4.1 | Pas de doc canon vs legacy | `docs/API_ROUTES.md` | nouveau |
| 4.2 | Finances summary/dashboard dans `rnd.py` | Déplacés vers `finances.py` (URLs inchangées) | `api/routers/finances.py`, `rnd.py` |
| 4.3 | Briefing router accès direct DB | Facade `briefing_facade.fetch_operational_briefing_for_date` | `services/facades/briefing_facade.py`, `api/routers/briefing.py` |
| 4.4 | Routes legacy sans signal OpenAPI | `deprecated=True` sur `/brief/today`, `POST /transactions`, `POST /briefing/morning-run` | `dashboard.py`, `core.py`, `briefing.py` |
| 4.5 | Router GDD monté même si flag off | `gdd_router` inclus seulement si `GDD_MANAGER_ENABLED=1` au startup | `api/routers/__init__.py` |
| 4.6 | Flags coûts invisibles en admin | Banner `COSTS_UNIFIED_READ` / `COSTS_SHADOW_COMPARE` | `costs_facade.py`, `admin-costs-view.tsx` |

**Tests :** `tests/test_api_routes_phase4.py`

**Reporté (volontaire) :** split `releases.py`, allègement `route_common.py`, deprecation briefing dans `advanced_services`.

---

## Phase 5 — Cohérence personas

**Objectif :** une source de vérité — `config/agent_personas.py`.

| # | Problème | Correction | Fichiers |
|---|----------|------------|----------|
| 5.1 | COO : Aria Stern (docs/prompts) vs Aria Voss (UI/assets) | Canon **Aria Voss** partout runtime | `agent_personas.py`, agents, services, skills, `CLAUDE.md` |
| 5.2 | PM : Léa Moreau vs Sam Rivera | Canon **Sam Rivera** | idem |
| 5.3 | Spec : Marcus Webb vs Léon Marchand | Canon **Léon Marchand** | idem |
| 5.4 | QA : Sven Lindqvist vs Alex Okafor | Canon **Alex Okafor** | idem |
| 5.5 | Noms hardcodés dans prompts LLM | Helpers `persona_prompt_intro()`, `persona_first_name()` | `config/agent_personas.py` |
| 5.6 | Events bus avec anciens prénoms | Prénoms dynamiques depuis personas | `services/event_bus.py` |

**Tests :** `tests/test_personas_phase5.py` (scan anti-legacy dans `agents/`, `services/`, `api/`)

**Non modifié :** assets `aria-voss-*` (déjà cohérents).

---

## Phase 6 — DevEx & hygiène repo

**Objectif :** onboarding dev simplifié, CI smoke, MCP moderne, BYOK renforcé.

| # | Problème | Correction | Fichiers |
|---|----------|------------|----------|
| 6.1 | `HUB_API_KEY` obligatoire au démarrage même en dev | Warning au lieu de `ValueError` si `ENVIRONMENT=development` | `config/settings.py` |
| 6.2 | Impossible de tester l’API locale sans clé | **Dev open mode** : middleware skip si clé absente en dev | `api/middleware.py` |
| 6.3 | `fastapi-mcp` sur transport SSE déprécié | `mount()` → `mount_http()` | `api/app.py` |
| 6.4 | BYOK CreatorFlow : XOR faible | Fernet v2 (`v2:` prefix) + decrypt legacy XOR | `services/creatorflow_secrets.py`, `requirements.txt` (`cryptography`) |
| 6.5 | CI sans vérif import post-install | Step smoke `composio` + `api.app` | `.github/workflows/ci.yml` |
| 6.6 | `.venv` / `.pytest_cache` parfois visibles dans git status | Commentaires explicites dans `.gitignore` | `.gitignore` |
| 6.7 | Doc dev incomplète sur clé optionnelle | `README.md`, `.env.example`, `CLAUDE.md` | idem |

**Tests :** `tests/test_devex_phase6.py`

| # | Problème | Correction | Fichiers |
|---|----------|------------|----------|
| 6.8 | Proxy Next exigeait `HUB_API_KEY` même en dev open | Transmet sans `X-Hub-Key` si clé absente (aligné backend) | `web/src/app/api/hub/[...path]/route.ts` |
| 6.9 | Doc `API_ROUTES.md` obsolète (aliases rnd) | Ligne finances corrigée | `docs/API_ROUTES.md` |

---

## Synthèse chiffrée

| Métrique | Avant audit | Après phase 6 |
|----------|-------------|---------------|
| Tests pytest | 3 failed, ~149 pass | **202 pass**, 2 skip |
| `tsc` | 1 erreur | **OK** |
| ESLint | 2 warnings hooks | **OK** |
| Routes beta admin ouvertes | Oui | **Non** (hub key) |
| Personas legacy en runtime | Oui | **Non** (scan test) |

---

## Fichiers clés modifiés (référence rapide)

```
api/middleware.py          # Sécurité + dev open mode
api/app.py               # mount_http
api/routers/finances.py  # Ownership finances
api/routers/briefing.py  # Facade briefing
api/routers/releases.py  # Ordre routes
api/lifespan.py          # Scheduler + watchdog
config/settings.py       # Flags + HUB_API_KEY dev
config/agent_personas.py # Source vérité personas
services/facades/        # briefing, costs
services/creatorflow_secrets.py  # Fernet BYOK
web/src/lib/hub-api-config.ts    # Anti-boucle proxy
web/src/lib/openroom-api.ts      # Erreurs visibles
web/src/lib/lobby-api.ts         # refreshError
docs/API_ROUTES.md
docs/assainissement/     # Ce dossier
```
