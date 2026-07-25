# Roadmap — ALNUA Hub

> Reconstitué rétroactivement le 2026-07-25 lors du bootstrap de gouvernance (voir
> `DOC_AUDIT.md`) — ce projet n'avait pas de roadmap suivie jusqu'ici. Les phases et
> dates ci-dessous sont déduites de l'historique Git et des fichiers `SPEC_*.md`
> existants, pas d'un plan pré-établi. À partir de maintenant, tenir ce fichier à jour
> à chaque sprint plutôt que de le reconstituer après coup.

## Phases overview

| Phase | Objectif | Status |
|-------|----------|--------|
| 0 | Fondation Hub — agents CrewAI, API FastAPI, dashboard v3 | ✅ Complete |
| 1 | Pipeline codage autonome (OpenHands, Aider) + agents spécialisés | ✅ Complete |
| 2 | Intégrations mémoire/observabilité (Mem0, Langfuse) + Composio | ✅ Complete |
| 3 | Dashboard Next.js — siège social virtuel (lobby + bureaux) | ✅ Complete |
| 4 | Durcissement sécurité (X-Hub-Key, RLS restreinte, sanitizing) | ✅ Complete |
| 5 | Migration agents vers "9-layer operating specs" | ✅ Complete |
| 6 | Centre R&D — pipeline dossier (phases 0-8 internes) | ✅ Complete |
| 7 | R&D Dispatch Workspace (livrables persistants multi-pôles) | ✅ Complete |
| 8 | Audits P0-P2 (mounting routers, sanitizing, lint, e2e) | ✅ Complete |
| 9 | Suivi coûts (ElevenLabs, hosting) + jalons Google Calendar | ✅ Complete |
| 10 | Gouvernance repo (ce bootstrap) | ✅ Complete |

Statut légende : ⏸️ Not started | 🔄 In progress | ✅ Complete | 🔴 Blocked

## Current phase

Aucun sprint actif identifié dans le code au moment du bootstrap — le dernier commit
(`8b366a5`, 2026-07-24) clôt un correctif ponctuel (`fix(library)`), pas une phase. La
prochaine phase reste **à définir avec Emilie** ; ne pas la deviner ici.

## Points tranchés le 2026-07-25 (anciennement ouverts)

- **Nwiro/UE5 vs Godot** — tranché : les deux coexistent intentionnellement. `CLAUDE.md`
  corrigé, voir `DECISIONS.md` DEC-009.
- **Mode dev ouvert par défaut** — tranché : `HUB_API_KEY` obligatoire dans tous les
  environnements, plus de bypass. Voir `DECISIONS.md` DEC-010, `BUGS.md` SEC-002.

## Détail des phases

### Phase 6 — Centre R&D (dossier hub)
**Objectif :** transformer le Centre R&D (idées auto-scorées) en département complet —
dossier structuré, comité multi-agents, deck illustré, dispatch CEO.
**Référence :** `SPEC_RND_DOSSIER_HUB.md`
**Statut :** phases 0-8 internes marquées complètes par le commit `16c84c2`
(2026-07-23, "Centre R&D dossier hub completion + platform extensions").

### Phase 7 — R&D Dispatch Workspace
**Objectif :** chaque agent du dispatch CEO écrit un livrable concret sur disque, tracé
par un manifest JSON, validé avant d'être marqué `success`.
**Référence :** `SPEC_RND_DISPATCH_WORKSPACE.md`
**Statut :** implémenté (`services/rnd_dispatch_executor.py`, `services/rnd_dispatch_playbooks.py`, skill `.claude/skills/alnua-dispatch/`).

### Phase 8 — Audits de durcissement
**Objectif :** fermer les écarts trouvés lors d'audits internes successifs.
**Commits clés :** `4b8f984` (P0 — R&D agents, router mounting), `e1a4f38` (P1 — auth
bots, input sanitizing, résilience LLM, lint), `84e5664` (P2 — error boundaries web,
routes, e2e), `5497218` (écarts restants — migrations, imports routers).
**Statut :** ✅ Complete au moment du bootstrap ; l'audit sécurité/qualité mené en
parallèle de ce bootstrap (2026-07-25) peut rouvrir des points, voir `BUGS.md`.
