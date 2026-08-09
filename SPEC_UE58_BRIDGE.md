# SPEC — Pont Hub ↔ serveur UE5.8 (DEC-017)

> Vague A / Phase 21. Contrat minimal pour le serveur côté studio.
> Le Hub (`skills/skill_ue58.py`) est le client ; ce document décrit ce que
> le serveur UE5.8 doit exposer. Pas de fake data si le serveur est down.

## Objectif

Remplacer Nwiro comme pont Gaming. Le serveur UE5.8 expose : santé, capacités
outils, chat agents, sync GDD contrôlée.

## Config Hub

| Variable | Rôle |
|----------|------|
| `UE5_SERVER_URL` | Base URL (ex. `http://127.0.0.1:8765`) — prioritaire |
| `UE58_HOST` / `UE58_PORT` | Fallback si URL absente (défaut port `8765`) |
| `UE58_API_KEY` | Bearer optionnel vers le serveur |

Si aucune URL/host n’est configuré → `configured: false` (honnête).

## Endpoints serveur (contrat)

### `GET /health`

```json
{
  "status": "ok",
  "engine": "UE5.8",
  "project": "Wyrdheim",
  "protocol_version": "1"
}
```

### `GET /v1/capabilities`

```json
{
  "capabilities": [
    { "id": "bt_create_tree", "category": "behavior", "description": "…" },
    { "id": "render_stat", "category": "render", "description": "…" },
    { "id": "niagara_spawn", "category": "niagara", "description": "…" }
  ]
}
```

Catégories attendues (filtre agents Hub) :

| Agent | Catégories / mots-clés |
|-------|------------------------|
| `ai_programmer` | behavior, bt, blackboard, ai |
| `technical_artist` | render, shader, nanite, lod, perf |
| `vfx_artist` | niagara, vfx, particle |

### `POST /v1/chat`

```json
{ "agent_id": "ai_programmer", "message": "…", "session_id": "optional" }
```

Réponse : `{ "reply": "…", "session_id": "…" }`.

### `GET /v1/gdd/{project_id}` / `PUT /v1/gdd/{project_id}`

Pull / push de sections GDD (JSON). Auth : `Authorization: Bearer <UE58_API_KEY>`
si la clé est configurée côté serveur.

### `POST /v1/tools/call`

```json
{ "name": "bt_create_tree", "arguments": { "...": "..." } }
```

Réponse : `{ "ok": true, "result": ... }`. Actions éditeur (Blueprint, Niagara, PIE…)
côté serveur — complément de l’agency **Claude Code sur le projet disque** (DEC-020).

## Agency PC (DEC-020) — hors ce serveur

Les agents Gaming agissent aussi sur le **PC hôte** via Claude Code / coding
pipeline Hub dans un worktree de `UE_PROJECT_PATH` (`skills/skill_gaming_agency.py`).
Ce n’est pas du computer-use GUI Windows.

## Endpoints Hub (client)

| Méthode | Path | Rôle |
|---------|------|------|
| GET | `/gaming/ue58/status` | Santé + configured/connected |
| POST | `/agents/{ai-programmer\|technical-artist\|vfx-artist}/ue58-probe` | Capacités filtrées |
| POST | `/gaming/ue58/chat` | Relais chat (input sanitizé) |
| POST | `/gaming/ue58/gdd/sync` | `direction=pull\|push` + `project_id` |
| POST | `/gaming/ue58/tools/call` | Outil éditeur serveur |
| GET | `/gaming/studio/agency/status` | Projet UE + Claude Code + UE58 |
| POST | `/gaming/studio/agency/run` | Claude Code sur le projet UE (worktree) |

## Règles

- Jamais inventer un moteur connecté — `ok: false` + message clair.
- Nwiro (`skill_nwiro`, `nwiro-probe`) = legacy jusqu’à bascule complète.
- Godot reste un chemin parallèle (DEC-017).
- Phases suivantes : plugin UE5 réel, UI chat riche, autonomie outils `tools/call`.
