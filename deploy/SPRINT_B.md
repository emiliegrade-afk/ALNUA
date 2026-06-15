# Sprint B — Deploy (Vercel + VPS + n8n)

Exécuter **après** Sprint A (flags locaux + migration GDD Supabase).

> **Windows local** : ne pas lancer `docker compose up` (prod) — build GroundingDINO ~30 min + chemins VPS (`/home/alnua/...`). Utiliser `npm run dev:docker` ou `npm run dev:api`. Prod Docker = **VPS Ubuntu uniquement**.

> **DNS** : `api.alnua.com` / `app.alnua.com` n'existent pas tant que tu n'as pas configuré les enregistrements chez ton registrar. `deploy:verify` contre prod échouera avant ça — c'est normal.

## B.1 — Build web (local)

```powershell
npm run deploy:build-web
```

Vérifie que `next build` passe avec les env de prod (copier `deploy/vercel.env.example` → `web/.env.production.local` si besoin).

## B.2 — Vercel

1. Projet Vercel, **Root Directory** = `web`.
2. Variables (Production) depuis `deploy/vercel.env.example` :
   - `HUB_API_BACKEND_URL=https://api.alnua.com`
   - `HUB_API_KEY` = même clé que VPS
   - `NEXT_PUBLIC_SUPABASE_URL` / `NEXT_PUBLIC_SUPABASE_ANON_KEY`
3. DNS : `app.alnua.com` → Vercel.
4. Déployer :

```bash
cd web && npx vercel --prod
```

## B.3 — VPS

```bash
# Première fois
bash deploy/setup_vps.sh
git clone <repo> /home/alnua/hub && cd /home/alnua/hub
cp deploy/.env.prod.example .env.prod
# Remplir toutes les clés dans .env.prod

python3 scripts/activate_prod_flags.py   # flags Phase 1-3 + URLs prod
docker compose up -d --build
curl http://127.0.0.1:8000/health
```

SSL (nginx déjà configuré pour `api.alnua.com` dans `deploy/nginx.conf`) :

```bash
docker compose run --rm certbot certonly --webroot \
  -w /var/www/certbot -d api.alnua.com \
  --email you@alnua.com --agree-tos --no-eff-email
docker compose restart hub_nginx
```

Mises à jour suivantes : `./deploy/deploy.sh`

## B.4 — n8n Cloud

Settings → Variables (sans slash final sur l'URL) :

| Variable | Valeur |
|----------|--------|
| `HUB_API_URL` | `https://api.alnua.com` |
| `HUB_API_KEY` | même que `.env.prod` |

Ré-importer les workflows `n8n/workflows/01`–`05` (ils utilisent `={{ $vars.HUB_API_URL }}`).

## B.5 — Vérification

**Avant DNS / VPS** (API locale ou Docker dev sur `:8000`) :

```powershell
npm run deploy:verify -- --api http://127.0.0.1:8000
# ou si dev natif sur 8002 :
npm run deploy:verify -- --api http://127.0.0.1:8002
```

**Après DNS + VPS + Vercel** :

Checklist manuelle :

- [ ] `https://api.alnua.com/health`
- [ ] `https://app.alnua.com` lobby
- [ ] `/admin/costs`, `/briefing`, `/gaming` (flags actifs)
- [ ] Bot Telegram
- [ ] Workflow n8n morning (01)

## Rollback rapide

- VPS : flags `*_ENABLED=0` dans `.env.prod` → `docker compose restart hub_api`
- Vercel : Promote previous deployment
- n8n : repasser `HUB_API_URL` sur l'ancienne URL

Voir aussi `deploy/DEPLOY.md` (guide complet).
