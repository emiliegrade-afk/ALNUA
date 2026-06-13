# Guide d'activation — variables d'environnement ALNUA Hub

> Référence pour activer progressivement les pôles (Robo, Gaming, Reviews, etc.).
> Dernière mise à jour : juin 2026.

## Deux fichiers à connaître

| Fichier | Sert à |
|---------|--------|
| **`.env`** (racine du repo) | Backend FastAPI, agents, bots, pipeline GitHub |
| **`web/.env.local`** | Frontend Next.js (Nwiro, Supabase anon, clé Hub SSR) |

Après toute modification : **redémarrer l'API** (`python -m api.main`) **et** Next.js (`cd web && npm run dev`).

Templates vides : `.env.example` et `web/.env.example`.

---

## Déjà opérationnel (rien à faire)

Ces blocs sont en place tant que les clés sont remplies dans ton `.env` :

- Supabase (lecture/écriture backend via `SUPABASE_SERVICE_ROLE_KEY`)
- OpenRouter (LLM agents)
- GitHub pipeline (issues → fix automatique)
- Telegram bot COO
- Composio (OAuth apps tierces)
- Mem0 + Langfuse + Chroma
- Hub API auth (`HUB_API_KEY` ↔ `web/.env.local`)

---

## À activer plus tard — checklist

Coche au fur et à mesure. Laisser **vide** = feature gracieusement désactivée (pas d'erreur bloquante).

### Pôle Robo — Eve + Pi

| Variable | Fichier | Exemple | Effet |
|----------|---------|---------|-------|
| `PI_HOST` | `.env` | `192.168.1.42` ou `eve.local` | Statut Pi online, SSH, commandes Embedded |
| `PI_USER` | `.env` | `pi` | Utilisateur SSH (déjà `pi` par défaut) |
| `PI_SSH_KEY` | `.env` | `~/.ssh/id_ed25519_eve` | Clé privée SSH |
| `LOOKING_GLASS_HOST` | `.env` | `http://192.168.1.42:8080` | Statut HoloPlay direct |
| *(alternative LG)* | — | laisser `LOOKING_GLASS_HOST` vide | Détection via `PI_HOST` + `pgrep holoplay` |

**UI** : `/robo` → BOM, Eve Pi, Looking Glass, agents Viktor / Rin.

---

### Pôle Gaming — Nwiro / UE5

| Variable | Fichier | Exemple | Effet |
|----------|---------|---------|-------|
| `NWIRO_HOST` | `.env` | `localhost` | Backend (déjà `localhost`) |
| `NWIRO_PORT` | `.env` | `5353` | Port MCP Nwiro |
| `NEXT_PUBLIC_NWIRO_HOST` | `web/.env.local` | `http://localhost:5353` | Badge « Nwiro connecté » sur `/gaming` |

Décommenter la ligne dans `web/.env.local` quand UE5 + Nwiro tournent.

---

### Reviews App Store / Google Play

| Variable | Fichier | Où trouver la valeur |
|----------|---------|---------------------|
| `APP_STORE_ID_NAIA` | `.env` | ID numérique dans l'URL App Store / App Store Connect |
| `GOOGLE_PLAY_PACKAGE_NAIA` | `.env` | Package Android, ex. `com.alnua.naia` |

Prérequis Google Play : `pip install google-play-scraper` (déjà dans `requirements.txt`).

**Déclenchement** : `/marketing` → bouton « Sync reviews stores », ou cron daily 08:00 du `reviews_bot`.

---

### Discord Wyrdheim + Publisher

| Variable | Fichier | Effet |
|----------|---------|-------|
| `DISCORD_BOT_TOKEN` | `.env` | Bot communauté + publication posts queue |
| `DISCORD_GUILD_ID` | `.env` | Serveur Wyrdheim |
| `DISCORD_CHANNEL_ANNONCES` | `.env` | Channel annonces (ou `_ANNOUNCEMENTS`) |
| `DISCORD_CHANNEL_LORE` | `.env` | Channel lore |
| `DISCORD_CHANNEL_GENERAL` | `.env` | Channel général |
| `DISCORD_CHANNEL_DEVLOG` | `.env` | Dev logs |

**Composio** (Twitter/X, LinkedIn) : déjà `COMPOSIO_API_KEY` — connecter les apps via `/connections`.

---

### Analytics web (Plausible)

| Variable | Fichier | Effet |
|----------|---------|-------|
| `PLAUSIBLE_API_KEY` | `.env` | Sync visiteurs → table `analytics` |

**Déclenchement** : `/marketing` → « Analytics sync », ou cron daily 06:00.

---

## Supabase — rôles des clés

| Clé | Usage |
|-----|--------|
| `SUPABASE_KEY` | Clé anon/publishable — frontend (`web/.env.local` → `NEXT_PUBLIC_SUPABASE_ANON_KEY`) |
| `SUPABASE_SERVICE_ROLE_KEY` | **Backend uniquement** — écritures BOM, agents, etc. **Ne jamais mettre dans le frontend.** |

---

## Ordre d'activation recommandé

1. **Robo** — `PI_HOST` quand le prototype Eve est sur le réseau
2. **Gaming** — `NEXT_PUBLIC_NWIRO_HOST` quand UE5 tourne
3. **Discord** — token + channel IDs pour la communauté Wyrdheim
4. **Reviews** — IDs stores quand Naïa est publiée
5. **Plausible** — clé API quand le site prod est branché

---

## Vérification rapide

```powershell
# Backend
python -m api.main
# → http://localhost:8000/docs

# Frontend
cd web; npm run dev
# → http://localhost:3000

# Tests
python -m pytest tests/ -v
```

Endpoints liés aux features « plus tard » :

- `GET /eve/status` — Pi Eve
- `GET /looking-glass/status` — Looking Glass
- `GET/POST/PATCH/DELETE /bom/eve` — BOM CRUD
- `POST /reviews/sync` — import reviews stores
- `POST /bots/publisher/run` — publication posts approuvés
- `POST /bots/analytics/run` — sync Plausible
