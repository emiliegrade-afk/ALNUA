# Changelog — ALNUA Hub

> Reconstitué rétroactivement le 2026-07-25 depuis `git log` (68 commits, historique
> depuis 2026-06-11) lors du bootstrap de gouvernance. Regroupé par date/thème plutôt
> qu'un commit par ligne — le détail exact reste dans `git log`. À partir de
> maintenant, ajouter une entrée par sprint/lot de changement au fur et à mesure,
> pas en dump différé.

## 2026-07-24 — Coûts & jalons (feat + fix)

- **Type :** feat + fix
- **Commits :** `013a04e`, `a3d33e2`, `8113af3`, `2ec99d2`, `3401e34`, `aa7b39d`, `8b366a5`
- **Details :** suivi combiné des coûts API (ElevenLabs auto + hosting manuel) sur la
  page Comptabilité ; "Jalons à venir" branché sur Google Calendar via Nadia ; fixes
  UI R&D (scroll, flexbox) ; vérification `library` corrigée pour checker la leçon
  apprise réelle plutôt que la seule source.

## 2026-07-23 — Centre R&D dossier hub + polish design (feat + fix + style)

- **Type :** feat + fix + style + chore
- **Commits :** `16c84c2`, `cbb9169`, `fd769c2`, `7f8061c`, `1a9d96f`, `c42e81f`,
  `7ae0798`, `617ab07`, `ddb979e`, `4dec459`, `ab36242`, `2ff02dc`, `7fcd614`,
  `d9880cd`, `b2e7a19`, `de90d83`, `8b05cd7`
- **Details :** complétion du pipeline Centre R&D dossier hub + extensions
  plateforme ; correctifs findings design (FINDING-001 à 006 : topbar, sparklines,
  hydratation SSR, contraste) ; retrait CreatorFlow/NUAWAY ops/media pipeline studio ;
  lint F401 enforced en CI ; noms d'agents réels dans le graphe de comm.

## 2026-07-23 — Audits P0/P1/P2 (fix)

- **Type :** fix
- **Commits :** `4b8f984` (P0 — agents R&D, montage routers), `e1a4f38` (P1 — auth
  bots, sanitizing input, résilience LLM, lint), `84e5664` (P2 — error boundaries web,
  routes comme source de vérité, couverture e2e), `5497218` (écarts restants —
  migrations, imports routers, openroom, pi-command)
- **Details :** série d'audits internes successifs fermant des écarts de sécurité et
  de robustesse identifiés en amont.

## 2026-06-24 — Migration 9-layer operating specs (feat)

- **Type :** feat
- **Commit :** `1a46408`
- **Details :** tous les personas migrés d'un `SYSTEM_PROMPT` 5-sections inline vers
  génération via `config/agent_operating_spec.py::get_system_prompt()`.

## 2026-06-13 → 2026-06-15 — Extension API + Centre R&D + assainissement (feat)

- **Type :** feat + chore
- **Commits :** `5c0447a` (Centre R&D dossier pipeline phases 0-8), `02fdba3`
  (extension architecture API Hub, services avancés au runtime), `10989d3`
  (assainissement Hub phases 0-6, perf lobby-bureau, extensions plateforme)

## 2026-06-12 — Durcissement sécurité + fallbacks robustesse (feat + fix)

- **Type :** feat + fix
- **Commits :** `7c86370` (X-Hub-Key obligatoire sur routes Hub API), `2df9669` (RLS
  anon restreinte à SELECT sur tables sensibles), `d094203` (restriction `/brand/assets`
  au dossier `brand_kits`), `cf9e9f9`/`f9054d0`/`831c2bf`/`c890f778`/`4656289`
  (fallbacks gracieux : Composio, Discord, Nwiro/UE5, SSH embedded, hardware BOM),
  `0cd7c53` (fix tests Windows + COO API), `41790b3`, `716767a`, `7c41e94`,
  `824a0ab`, `137a752`

## 2026-06-11 — Fondation du Hub (feat)

- **Type :** feat (burst initial)
- **Commits :** `e995186` (first commit) → `137a752`
- **Details :** mise en place initiale — API FastAPI, agents CrewAI, dashboard v3
  (siège social virtuel : lobby + bureaux par département), OpenRoom (war room
  visuelle), intégrations Mem0 (mémoire persistante), Langfuse (tracing LLM),
  Composio (OAuth gateway), Chroma (base de connaissances), OpenHands + Aider
  (pipeline codage autonome), skill Nwiro (UE5, port 5353 — voir `DECISIONS.md`
  DEC-009 pour le statut actuel, non tranché).

## 2026-07-25 — Bootstrap gouvernance (docs)

- **Type :** docs
- **Details :** création de `ARCHITECTURE.md`, `ROADMAP.md`, `DECISIONS.md`,
  `BUGS.md`, `CHANGELOG.md` (ce fichier), `IMPLEMENTATION_STATUS.md`, `TESTING.md`,
  `DOC_AUDIT.md` — ALNUA Hub était le seul des 4 projets du workspace `C:\Dev` sans
  cette couche de gouvernance. Voir `DOC_AUDIT.md` pour le détail de l'audit mené en
  parallèle.
