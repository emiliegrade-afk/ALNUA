# MCP Cursor Setup — ALNUA Hub
> Guide complet pour activer tous les MCP servers dans Cursor.
> Après setup : Cursor peut appeler directement n8n, GitHub, browser logs, et la doc à jour.

---

## Architecture MCP ALNUA

```
Cursor (IDE)
├── context7          → Doc à jour FastAPI/Supabase/CrewAI (zero hallucination)
├── n8n-mcp           → Build/deploy workflows n8n directement depuis Cursor
├── github            → Crée issues, PRs, branches sur tes repos ALNUA
├── browser-tools     → Monitor logs browser (debug frontend Next.js)
└── alnua-hub         → Tous les agents ALNUA comme outils MCP natifs
```

---

## Étape 1 — Fichier mcp.json projet (déjà créé)

Le fichier `.cursor/mcp.json` est déjà dans le repo à `C:\Dev\ALUNA_HUB\.cursor\mcp.json`.
Il contient les 5 servers. **Tu dois juste remplacer les placeholders ci-dessous.**

---

## Étape 2 — Remplacer les placeholders

### 2a. GitHub Personal Access Token
1. Aller sur : https://github.com/settings/tokens/new
2. Nom : `ALNUA-Cursor-MCP`
3. Scopes nécessaires : `repo`, `read:org`, `read:user`
4. Copier le token généré
5. Dans `.cursor/mcp.json`, remplacer `YOUR_GITHUB_PAT_HERE` par le token

### 2b. n8n API Key
1. Ouvrir n8n : http://localhost:5678
2. Settings → API Keys → Create API Key
3. Nom : `cursor-mcp`
4. Dans `.cursor/mcp.json`, remplacer `YOUR_N8N_API_KEY_HERE` par la clé

> **Si n8n tourne sur un autre port ou en cloud**, changer aussi `N8N_BASE_URL`.

### 2c. ALNUA Hub
Le server `alnua-hub` pointe sur `http://localhost:8000/mcp`.
Il s'active automatiquement quand le Hub FastAPI tourne (`uvicorn api.main:app`).

---

## Étape 3 — Installer les dépendances npm (une seule fois)

```bash
# Dans un terminal PowerShell
npm install -g n8n-mcp
npm install -g @modelcontextprotocol/server-github
```

`context7` et `browser-tools` utilisent `npx` — pas d'installation nécessaire.

---

## Étape 4 — browser-tools-mcp (setup spécifique)

browser-tools nécessite **deux composants** :

### 4a. Extension Chrome
Installer depuis Chrome Web Store : https://chromewebstore.google.com/detail/agentdesk-browser-tools/...
(Chercher "AgentDesk Browser Tools" dans le Chrome Web Store)

### 4b. Serveur local
```bash
# À lancer avant d'utiliser browser-tools dans Cursor
npx @agentdeskai/browser-tools-server
# Laisse ce terminal ouvert en background
```

---

## Étape 5 — Config globale Cursor (optionnel)

Pour avoir les MCPs **dans tous tes projets** (pas seulement ALNUA), copier le même contenu dans :
```
C:\Users\emili\.cursor\mcp.json
```

---

## Étape 6 — Redémarrer Cursor

Après modification de `.cursor/mcp.json` :
1. Fermer Cursor complètement
2. Rouvrir Cursor
3. Ouvrir le projet ALNUA_HUB
4. Vérifier dans Settings → MCP que les 5 servers apparaissent en vert

---

## Utilisation dans Cursor

### context7 — Doc à jour
```
# Dans un prompt Cursor :
"Montre-moi comment utiliser FastAPI avec dépendances Depends, use context7"
→ Cursor charge automatiquement la doc FastAPI à jour
```

### n8n-mcp — Builder des workflows
```
"Crée un workflow n8n qui appelle POST /agents/content/create-post tous les lundis à 9h"
→ n8n-mcp génère le JSON du workflow et peut le déployer directement
```

### github — Issues & PRs
```
"Crée une issue GitHub sur mon repo ALNUA_HUB pour tracker le bug du leaderboard"
→ github-mcp crée l'issue avec titre, body et labels automatiquement
```

### browser-tools — Debug frontend
```
"Quelles erreurs console sur la page /analytics ?"
→ browser-tools retourne les logs de la console Chrome en temps réel
```

### alnua-hub — Appel direct agents
```
"Appelle l'agent analyst-data pour générer une requête SQL pour les scores du mois"
→ alnua-hub appelle POST /agents/analyst-data/sql directement comme outil MCP
```

---

## Vérification que tout fonctionne

```bash
# Terminal 1 — Lancer le Hub
cd C:\Dev\ALUNA_HUB
uvicorn api.main:app --reload --port 8000

# Terminal 2 — Lancer n8n (si local)
n8n start

# Terminal 3 — Lancer browser-tools-server (si frontend debug)
npx @agentdeskai/browser-tools-server
```

Puis dans Cursor → Cmd+Shift+P → "MCP: List Servers" → tous doivent être connected.

---

## godot-mcp — Setup (Nova / Gaming Studio)

Pour utiliser le MCP Godot (Nova Fischer, dev_gaming) :

### Installation
```bash
npm install -g godot-mcp
```

### Variable d'environnement
Dans ton `.env` à la racine du repo :
```
GODOT_PROJECT_PATH=/chemin/absolu/vers/ton/projet.godot
```
Exemple macOS : `/Users/emilie/Dev/NomadGame/project.godot`

### Prérequis
- Godot 4.x installé et accessible dans le PATH (`godot --version`)
- Le projet Godot doit être **ouvert dans l'éditeur** pour que le MCP puisse s'y connecter

### Test rapide
Dans Cursor après restart, le MCP `godot` doit apparaître dans "MCP: List Servers".
Test : demande à Cursor/ALNUA "liste les nœuds de la scène principale" → godot-mcp répond.

---

## Troubleshooting

| Problème | Solution |
|----------|----------|
| `alnua-hub` not connected | Vérifier que `uvicorn api.main:app` tourne sur port 8000 |
| `n8n-mcp` auth error | Vérifier N8N_API_KEY et que n8n tourne sur le bon port |
| `context7` slow | Normal à la première requête (cache froid) — attend 10s |
| `browser-tools` no data | Vérifier que l'extension Chrome est installée et active |
| `github` permission denied | Vérifier que le PAT a les scopes `repo` + `read:org` |
| `godot` not connected | Ouvrir le projet dans l'éditeur Godot + vérifier GODOT_PROJECT_PATH |
| `godot` Godot not found | Ajouter Godot au PATH ou définir `GODOT_PATH` dans l'env |
