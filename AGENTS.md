# AGENTS.md — point d'entrée universel

Ce fichier est la première chose à lire, humain ou agent, avant de toucher au code de
ce repo. Il n'y a rien à "faire" ici — juste l'ordre de lecture pour le reste.

## Ordre de lecture

1. **`CLAUDE.md`** — architecture, patterns, **49** agents personas, règles invariantes.
   Le plus souvent suffisant à lui seul pour une tâche courante.
2. **`ALNUA_OVERVIEW.md`** — vue produit / organisation (quoi / pourquoi), si le contexte
   métier manque ; pas un substitut à `CLAUDE.md` pour coder.
3. **Gouvernance, si la tâche en dépend** — `ROADMAP.md` (où en est le projet),
   `DECISIONS.md` (pourquoi un choix a été fait, avant de le remettre en question),
   `BUGS.md` (ce qui est déjà connu, ouvert ou corrigé), `CHANGELOG.md` (ce qui a
   shippé récemment).
4. **`.cursor/rules/*.mdc`, à la demande** — chargées automatiquement par Cursor selon
   `globs`/`alwaysApply`, pas à lire en entier par réflexe. Trois règles générales
   toujours actives : `agent-orchestration.mdc` (comment paralléliser du travail sur ce
   repo), `ai-agent-survival.mdc` (ce qu'un agent ne doit jamais faire), `async-jobs.mdc`
   (workflows différés — n8n, dispatch R&D, watchdog). Les autres (`brandkit.mdc`,
   `rnd_dossier.mdc`, `alnua_company.mdc`) sont scopées par `globs` à une feature précise.
5. **`SPEC_*.md`**, seulement si la tâche touche la feature qu'elles décrivent
   (`SPEC_RND_DOSSIER_HUB.md`, `SPEC_WORKFLOW_ENGINE.md`, etc.).

## Principe : graph-first-recall

Ne jamais lire tout le repo par réflexe. Avant d'ouvrir un fichier de code en entier :
consulter `DECISIONS.md`/`ROADMAP.md` pour le contexte, n'ouvrir que ce qui est
directement utile à la tâche, s'arrêter dès qu'on a l'information nécessaire. Ce repo a
~50 fichiers agents et ~128 fichiers services (`ARCHITECTURE.md` en donne la carte) —
personne ne les lit tous pour une tâche donnée.

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
   (`README` / `ARCHITECTURE` / `TESTING` / `IMPLEMENTATION_STATUS` / `CLAUDE` /
   `ROADMAP` selon ce qui a bougé — agents, routers, tests collectés, Next.js).
2. **CI mentale Python** (si `agents/` `services/` `api/` `config/` `bots/` `skills/`
   touchés) : `ruff check agents/ services/ api/ config/ database/ bots/ skills/`
   puis `pytest tests/ -q` — pas un sous-ensemble « probablement concerné ».
3. **CI mentale frontend** (si `web/` touché) : `npx tsc --noEmit` puis
   `npm test` (ou Vitest ciblé sur les fichiers touchés). Build :
   `npm run build:safe` si `next dev` tourne déjà (évite de corrompre `.next`).
4. **Pas de stub silencieux** — voir `.cursor/rules/ai-agent-survival.mdc`.
5. **Pas de secret** — rien en dur ; `.env` / clés hors du commit.

Rappel historique : BUG-011 (CHANGELOG figé) puis BUG-018 (Next 14 encore affiché
après Next 15 le même jour) — la règle existe pour ça. Détail CHANGELOG aussi en
en-tête de `CHANGELOG.md`.

## Skills disponibles

Voir la table `## Skills Cursor disponibles` dans `CLAUDE.md` — `/alnua-hub` en début
de session pour l'architecture complète, `/alnua-new-agent` pour créer un agent,
`/alnua-parallel` pour l'exécution multi-agents.
