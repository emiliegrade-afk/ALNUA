# AGENTS.md — point d'entrée universel

Ce fichier est la première chose à lire, humain ou agent, avant de toucher au code de
ce repo. Il n'y a rien à "faire" ici — juste l'ordre de lecture pour le reste.

## Ordre de lecture

1. **`CLAUDE.md`** — architecture, patterns, **52** agents personas, règles invariantes.
   Le plus souvent suffisant à lui seul pour une tâche courante.
2. **`ALNUA_OVERVIEW.md`** — vue produit / organisation (quoi / pourquoi), si le contexte
   métier manque ; pas un substitut à `CLAUDE.md` pour coder.
3. **Gouvernance vivante (racine)** — `ROADMAP.md`, `DECISIONS.md`, `BUGS.md`,
   `CHANGELOG.md`.
4. **Bible / classeur** — [`docs/README.md`](docs/README.md) : specs, architecture
   détaillée, testing, audits, guides, archives. Racine volontairement courte
   (8 fichiers doc + ce point d'entrée).
5. **`.cursor/rules/*.mdc`, à la demande** — chargées automatiquement par Cursor selon
   `globs`/`alwaysApply`. Toujours actives : `agent-orchestration.mdc`,
   `ai-agent-survival.mdc`, `async-jobs.mdc`. Scopées : `brandkit.mdc`,
   `rnd_dossier.mdc`, `alnua_company.mdc`.
6. **`docs/specs/SPEC_*.md`**, seulement si la tâche touche la feature
   (`SPEC_RND_DOSSIER_HUB.md`, `SPEC_WORKFLOW_ENGINE.md`, etc.).

## Principe : graph-first-recall

Ne jamais lire tout le repo par réflexe. Avant d'ouvrir un fichier de code en entier :
consulter `DECISIONS.md`/`ROADMAP.md` pour le contexte, n'ouvrir que ce qui est
directement utile à la tâche, s'arrêter dès qu'on a l'information nécessaire. Carte
système : [`docs/classeur/architecture.md`](docs/classeur/architecture.md).

## Projet existant, pas un scaffold

Ce repo n'est pas neuf — ne pas générer de code qui ignore les conventions déjà en
place. Avant toute feature : identifier le pattern déjà utilisé par un agent/router/
service voisin (`CLAUDE.md` en documente la majorité), s'y aligner plutôt que d'en
introduire un troisième.

## Checklist fin de lot (Vague 0 — obligatoire)

Avant de déclarer une tâche **terminée** (et avant tout commit demandé) :

1. **Anti-drift** — si le diff du lot / merge dépasse **~500 lignes** : au minimum
   une bullet dans `CHANGELOG.md` **le jour même** (type + pourquoi). Si le lot
   change un compte ou une version visible : resync le même jour
   (`README` / `docs/classeur/architecture` / `testing` / `implementation-status` /
   `CLAUDE` / `ROADMAP` selon ce qui a bougé — agents, routers, tests, Next.js).
2. **CI mentale Python** (si `agents/` `services/` `api/` `config/` `bots/` `skills/`
   touchés) : `ruff check agents/ services/ api/ config/ database/ bots/ skills/`
   puis `pytest tests/ -q` — pas un sous-ensemble « probablement concerné ».
3. **CI mentale frontend** (si `web/` touché) : `npx tsc --noEmit` puis
   `npm test` (ou Vitest ciblé). Build : `npm run build:safe` si `next dev` tourne.
4. **Pas de stub silencieux** — voir `.cursor/rules/ai-agent-survival.mdc`.
5. **Pas de secret** — rien en dur ; `.env` / clés hors du commit.
6. **Fichiers ≤ ~300 lignes** — scinder avant d'ajouter à la dette (façades OK).

## Habitudes durabilité

| Habitude | Fréquence | Comment |
|----------|-----------|---------|
| Audit santé 10 dimensions | ≤ toutes les **3 semaines** | Canvas + entrée `docs/classeur/doc-audit.md` (Audit 005 fait 2026-09-07 ; prochain ≤ ~2026-09-28) |
| Purge orphans / docs | Chaque fin de vague | Specs → `docs/specs/` ; plans terminés → `docs/archive/` |
| Ratio tests ↔ surface | Obligatoire Finance / trust / workflows | Nouveau endpoint → pytest le même lot |
| Vault library | Continu | Corps des notes **jamais** re-commités — seul `_index/` tracké |
| Worktrees pour splits | Quand fan-out | `agent-orchestration.mdc` — un intégrateur séquentiel pour le merge |

## Skills disponibles

Voir `CLAUDE.md` — `/alnua-hub`, `/alnua-new-agent`, `/alnua-parallel`.
