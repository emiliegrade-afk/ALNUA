# Configuration des clés Hub — local

> Fichiers **gitignored** — ne jamais committer de secrets.

## Ta clé Hub API

Elle est **déjà définie** dans ton environnement local :

| Fichier | Variable | Statut |
|---------|----------|--------|
| `.env` (racine) | `HUB_API_KEY` | ✅ présente |
| `web/.env.local` | `HUB_API_KEY` | ✅ même valeur |
| `.cursor/mcp.json` | `${env:HUB_API_KEY}` | ⚠️ lit la variable **système** Cursor |

Valeur (masquée) : `alnua_dev_…a4c8`

## Où la clé doit aller

### Backend FastAPI (uvicorn)

```env
# .env à la racine du repo — déjà configuré chez toi
HUB_API_KEY=<ta clé — voir .env local>
ENVIRONMENT=development
```

### Frontend Next.js (proxy `/api/hub`)

```env
# web/.env.local — déjà configuré chez toi
HUB_API_BACKEND_URL=http://127.0.0.1:8000
HUB_API_KEY=<même valeur que .env racine>
```

### Cursor MCP `alnua-hub`

Le fichier `.cursor/mcp.json` référence `${env:HUB_API_KEY}`.

Pour que le MCP Hub fonctionne dans Cursor :

1. **Option A** — Ajouter `HUB_API_KEY` aux variables d’environnement Windows (session utilisateur), puis redémarrer Cursor.
2. **Option B** — Lancer Cursor depuis un terminal où `.env` est chargé (moins fiable).

La clé est la **même** que dans `.env` racine.

### n8n / production

Copier la même clé dans n8n (Variables) et `deploy/.env.prod` — **pas** dans les fichiers `.example` versionnés.

## Mode dev sans clé (optionnel)

Si `HUB_API_KEY` est **vide** et `ENVIRONMENT=development` :

- Backend : routes ouvertes sans `X-Hub-Key`
- Proxy Next : transmet sans header (depuis correction phase 6 finale)

Avec ta config actuelle, la clé est **définie** → auth active (comportement recommandé).

## Régénérer une clé

Si tu veux une nouvelle clé :

```powershell
# Exemple — 32 hex chars
-join ((48..57) + (97..102) | Get-Random -Count 32 | ForEach-Object { [char]$_ })
```

Puis mets la **même** valeur dans `.env`, `web/.env.local`, et les env Cursor/n8n.
