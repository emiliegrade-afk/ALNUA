# AGENTS.md — point d'entrée universel

Ce fichier est la première chose à lire, humain ou agent, avant de toucher au code de
ce repo. Il n'y a rien à "faire" ici — juste l'ordre de lecture pour le reste.

## Ordre de lecture

1. **`CLAUDE.md`** — architecture, patterns, 27 agents, règles invariantes. Le plus
   souvent suffisant à lui seul pour une tâche courante.
2. **Gouvernance, si la tâche en dépend** — `ROADMAP.md` (où en est le projet),
   `DECISIONS.md` (pourquoi un choix a été fait, avant de le remettre en question),
   `BUGS.md` (ce qui est déjà connu, ouvert ou corrigé).
3. **`.cursor/rules/*.mdc`, à la demande** — chargées automatiquement par Cursor selon
   `globs`/`alwaysApply`, pas à lire en entier par réflexe. Trois règles générales
   toujours actives : `agent-orchestration.mdc` (comment paralléliser du travail sur ce
   repo), `ai-agent-survival.mdc` (ce qu'un agent ne doit jamais faire), `async-jobs.mdc`
   (workflows différés — n8n, dispatch R&D, watchdog). Les autres (`brandkit.mdc`,
   `rnd_dossier.mdc`, `alnua_company.mdc`) sont scopées par `globs` à une feature précise.
4. **`SPEC_*.md`**, seulement si la tâche touche la feature qu'elles décrivent
   (`SPEC_RND_DOSSIER_HUB.md`, `SPEC_WORKFLOW_ENGINE.md`, etc.).

## Principe : graph-first-recall

Ne jamais lire tout le repo par réflexe. Avant d'ouvrir un fichier de code en entier :
consulter `DECISIONS.md`/`ROADMAP.md` pour le contexte, n'ouvrir que ce qui est
directement utile à la tâche, s'arrêter dès qu'on a l'information nécessaire. Ce repo a
40 fichiers agents et ~112 fichiers services (`ARCHITECTURE.md` en donne la carte) —
personne ne les lit tous pour une tâche donnée.

## Projet existant, pas un scaffold

Ce repo n'est pas neuf — ne pas générer de code qui ignore les conventions déjà en
place. Avant toute feature : identifier le pattern déjà utilisé par un agent/router/
service voisin (`CLAUDE.md` en documente la majorité), s'y aligner plutôt que d'en
introduire un troisième.

## Skills disponibles

Voir la table `## Skills Cursor disponibles` dans `CLAUDE.md` — `/alnua-hub` en début
de session pour l'architecture complète, `/alnua-new-agent` pour créer un agent,
`/alnua-parallel` pour l'exécution multi-agents.
