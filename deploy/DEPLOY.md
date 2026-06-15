# ALNUA Hub — Déploiement (Phase 5)

Architecture cible : **Next.js sur Vercel** + **FastAPI sur VPS** (Docker + nginx + Telegram bot).

```
Browser ──► Vercel (app.alnua.com)
              └── /api/hub/* ──proxy──► VPS API (api.alnua.com:443)
                                         ├── hub_api (uvicorn)
                                         ├── hub_bot (telegram)
                                         └── hub_nginx (SSL)
```

Le navigateur ne contacte jamais l'API directement : le proxy Next.js (`web/src/app/api/hub/[...path]/route.ts`) injecte `X-Hub-Key`.

---

## 1. Dev local (3 modes)

### Mode A — Natif (recommandé au quotidien)

```powershell
# Si dev:api / dev:web échouent (port occupé) — souvent après npm run test:e2e
npm run dev:status   # voir qui écoute sur 3000 / 8000
npm run dev:stop     # arrête uvicorn + next dev + playwright

# Terminal 1 — API
npm run dev:api

# Terminal 2 — Web
npm run dev:web
```

Ports alternatifs si besoin :

```powershell
$env:DEV_API_PORT=8002; npm run dev:api
$env:DEV_WEB_PORT=3001; npm run dev:web
# Mettre à jour web/.env.local : HUB_API_BACKEND_URL=http://127.0.0.1:8002
```

Copier `.env.example` → `.env` et `web/.env.example` → `web/.env.local`.  
`HUB_API_KEY` doit être identique dans les deux fichiers.

### Mode B — API en Docker (image légère, ~2 min)

Utilise `Dockerfile.dev` + `requirements-dev.txt` (sans torch / GroundingDINO).

```powershell
npm run dev:docker
npm run dev:web
```

### Mode C — Tests E2E (Playwright démarre API + Web)

```powershell
npm run test:e2e
# depuis web/: npm run test:e2e
```

---

## 2. Vercel (frontend)

1. Créer un projet Vercel lié au repo GitHub.
2. **Root Directory** : `web` (obligatoire).
3. Variables d'environnement : copier depuis `deploy/vercel.env.example`.
4. `HUB_API_BACKEND_URL` = URL publique de l'API VPS (`https://api.alnua.com`).
5. Déployer : push sur `main` ou `vercel --prod` depuis `web/`.

```bash
cd web
npx vercel link
npx vercel env pull .env.local
npx vercel --prod
```

Preview deployments héritent des env **Preview** ; production des env **Production**.

---

## 3. VPS (API + bot + nginx)

### Première installation

```bash
# En root sur Ubuntu 22.04+
bash deploy/setup_vps.sh

# En tant que alnua
git clone <repo> /home/alnua/hub
cd /home/alnua/hub
cp deploy/.env.prod.example .env.prod
# Éditer .env.prod — remplir toutes les clés

docker compose up -d --build
curl http://127.0.0.1:8000/health
```

### SSL (Let's Encrypt)

1. Obtenir le certificat pour `api.alnua.com` (`deploy/nginx.conf` est déjà configuré) :

```bash
docker compose run --rm certbot certonly --webroot \
  -w /var/www/certbot \
  -d api.alnua.com \
  --email you@alnua.com --agree-tos --no-eff-email
docker compose restart hub_nginx
```

### Mise à jour (zéro-downtime API)

```bash
./deploy/deploy.sh
```

---

## 4. Matrice des variables

| Variable | `.env` local | `.env.prod` VPS | Vercel (`web`) |
|----------|--------------|-----------------|----------------|
| `HUB_API_KEY` | ✅ | ✅ | ✅ (server) |
| `HUB_API_BACKEND_URL` | — | — | ✅ → URL VPS |
| `OPENROUTER_API_KEY` | ✅ | ✅ | — |
| `SUPABASE_URL/KEY` | ✅ | ✅ | anon key only (`NEXT_PUBLIC_*`) |
| `ADMIN_*_ENABLED` | ✅ | ✅ | — (lu par l'API) |
| `GDD_MANAGER_ENABLED` | ✅ | ✅ | — |
| `HUB_API_URL` | `http://localhost:8000` | `https://api.alnua.com` | — (n8n) |
| `BETA_PORTAL_BASE_URL` | `http://localhost:3000` | `https://app.alnua.com` | — |

---

## 5. n8n

Dans n8n Cloud → Settings → Variables :

```
HUB_API_URL=https://api.alnua.com
HUB_API_KEY=<même que VPS>
```

Workflows `n8n/workflows/01`–`05` appellent l'API via ces variables.

---

## 6. Feature flags en production

Activer progressivement dans `.env.prod` :

```env
ADMIN_COSTS_PAGE_ENABLED=1
ADMIN_EVENTS_PAGE_ENABLED=1
ADMIN_AB_TEST_PAGE_ENABLED=1
BRIEFING_COO_SECTION_ENABLED=1
GDD_MANAGER_ENABLED=1
```

Rollback = repasser à `0` + `docker compose restart hub_api`.

Migration GDD : `supabase db push` (migration `20260613210000_gdd_chunks.sql`) avant `GDD_MANAGER_ENABLED=1`.

---

## 7. Checklist post-deploy

Automatisé (local ou prod) :

```powershell
$env:HUB_API_URL="https://api.alnua.com"
$env:BETA_PORTAL_BASE_URL="https://app.alnua.com"   # optionnel
npm run deploy:verify
```

Manuel :

- [ ] `curl https://api.alnua.com/health` → `{"status":"ok"}`
- [ ] Vercel app charge le lobby (`https://app.alnua.com`)
- [ ] `/admin/flags` via proxy (`/api/hub/admin/flags` + `X-Hub-Key`)
- [ ] Bot Telegram répond
- [ ] n8n morning workflow OK
- [ ] `pytest tests/ -v` + `npm run test:e2e` verts en CI

---

## 8. Rollback

```bash
cd /home/alnua/hub
git checkout <previous-tag>
docker compose build hub_api hub_bot
docker compose up -d --no-deps hub_api hub_bot
```

Vercel : Dashboard → Deployments → Promote previous deployment.

---

## 9. Fichiers clés

| Fichier | Rôle |
|---------|------|
| `docker-compose.dev.yml` | API local hot-reload |
| `docker-compose.yml` | Prod VPS (API + bot + nginx + certbot) |
| `deploy/nginx.conf` | Reverse proxy HTTPS → `hub_api:8000` |
| `deploy/deploy.sh` | Pull + rebuild + healthcheck |
| `web/vercel.json` | Config build Vercel |
| `deploy/SPRINT_B.md` | Runbook Sprint B (Vercel + VPS + n8n) |
| `scripts/verify_deploy.py` | Smoke post-deploy API + web |
