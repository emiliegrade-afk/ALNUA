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
| 11 | Refonte UI départements App / Gaming / Robotique (socle commun + onglets spécialisés) | ✅ Complete |
| 12 | Fondations données transverses (assigné, points, échéance sur les tickets) | ✅ Complete |
| 13 | Agents manquants Gaming (7) + Robotique (8) — 15 personas | ✅ Complete |
| 14 | Système Modules/sous-fonctionnalités réel (page détail projet) | ✅ Complete |
| 15 | Décisions en attente réelles (page détail projet) | ✅ Complete |
| 16 | Gaming — pipeline build/télémétrie UE5 | ✅ Complete (réceptacle) |
| 17 | Gaming — pipeline Assets réel (Perforce / UE5 asset registry) | ✅ Complete |
| 18 | Gaming — intégrations Steamworks (Wishlist) + Discord | ✅ Complete (réceptacle) |
| 19 | Robotique — BOM étendu (PCB/firmware/tests) + bancs connectés (Laboratoire) | ✅ Complete (réceptacle) |
| 20 | Robotique — télémétrie IoT (Analytics : conso/temp/batterie/cycles) | ✅ Complete (réceptacle) |
| 21 | Outils réels (skills) pour les 15 agents spécialisés Gaming/Robotique (Phase 13) | ✅ Hub Complete (config UE/Pi externe pour live studio) |
| 22 | Redesign R&D v2 — socle & coquille (`/rnd-v2`) | ✅ Complete |
| 23 | Redesign R&D v2 — Innovation Pipeline (cartes) | ✅ Complete |
| 24 | Redesign R&D v2 — Incubateur (Kanban) | ✅ Complete |
| 25 | Redesign R&D v2 — Moteur Conseil (stratégique + IA) | ✅ Complete (réceptacle) |
| 26 | Redesign R&D v2 — Arbres (canvas mindmap) | ✅ Complete |
| 27 | Redesign R&D v2 — Dossiers (vue table) | ✅ Complete |
| 28 | Redesign R&D v2 — Explorer (veille externe autonome) | ✅ Complete (Vague E) |
| 29 | Marketing/Finances — Command Center visuel (chrome immersif + cockpits) | ✅ Complete |
| 30 | Workflow engine généralisé — recettes de validation configurables + niveaux d'autonomie | ✅ Complete (DEC-032 Vague 2) |
| 31 | Agent Trust System — indice de confiance par agent, distinct de la compétition | ✅ Complete (DEC-032) |
| 32 | Review Board générique + Quality Gates par département | ✅ Complete (DEC-032) |
| 33 | Marketing Command Center — profondeur (campagnes, calendrier éditorial unifié) | ✅ Complete (Campagnes + Content Studio) |
| 34 | Finance Cockpit — profondeur (budgets, factures, fiscalité) | ✅ Complete sans `budget_transfer` (DEC-032) |
| 35 | Brand Design — design system transversal + reviewer cross-département | ✅ Depth+ Complete (débat Élise↔Anouk + split brand-view) |
| 36 | Orchestration inter-départements — event bus cross-département + briefing COO étendu | ✅ Depth+ Complete |
| 37 | Marketing Command Center : mesure de performance réelle (Reach/Engagement/ROI/Funnel) | ✅ Complete |
| 38 | Harmonisation visuelle globale du Hub sur les maquettes ChatGPT (rendu visuel, branchement à reconnecter) | ✅ Complete |
| 39 | Idle agent work — file hybride COO/CEO, ambition entreprise, trust + budget adaptatif | ✅ Complete (DEC-032 Vague 3) |
| 40 | Agent isolation (AAF Phase A) — locks + slots + merge integrator-only | ✅ Complete (DEC-022) |
| 41 | Mission Graph (AAF Phase B) — DAG Mission/Tasks + API + OpenRoom | ✅ Complete (DEC-023) |
| 42 | Loop Engine (AAF Phase C) — execute/evaluate/feedback/retry | ✅ Complete (DEC-024) |
| 43 | Review Chain + Merge (AAF Phase D) — AUTO→BOARD→POLICY→INTEGRATE | ✅ Complete (DEC-025) |
| 44 | Capabilities + PermissionGuard + Trust Graph (AAF Phase E) | ✅ Complete (DEC-026) |
| 45 | Context Engine L1–L4 + Collective (AAF Phase F) | ✅ Complete (DEC-027) |
| 46 | Agent Lounge — remplace OpenRoom ; gamification expérimentale isolée | ✅ Complete (DEC-031) |
| 47 | Overlay Jarvis — Nadia/Aria faits texte + réplique voix (DEC-033) | 🔄 Lots 0–4 |

Statut légende : ⏸️ Not started | 🔄 In progress | ✅ Complete | 🔴 Blocked

## Current phase

**Plan Hub 100 % logiciel (DEC-032) — Vague 0–5 + Audit 005 (7) done.**
Phases **30 / 31 / 32 / 34 / 39 = ✅**. Audit 005 fait le 2026-09-07 —
voir `docs/classeur/doc-audit.md` (`BUGS.md` : 0 finding ouvert). Reste :
Vague 6 « Apps NAÏA/NUAWAY coding » ; fin de plan = Vague 8 (Pi/UE5.8/
Revolut/ads, hors scope Hub).
**Fin reportée :** Pi, UE5.8, Revolut, ads.

**En cours :** Phase **47** Overlay Jarvis — Lots 0–4 ✅. Suivant = Lot 5 (ElevenLabs optionnel).
Sans crédits OpenRouter : `VOICE_OVERLAY_LLM=0` ; météo = tool HTTP (wttr.in).

## Points tranchés le 2026-08-12 (DEC-032)

- **31 / 32 / 34** — closes MVP / Depth+ sans rouvrir `budget_transfer`.
- **30** — Complete seulement après UI workflows (Vague 2) ; pas de transfert auto.
- **100 % Hub logiciel** ≠ Pi / UE5.8 / Revolut / réseaux sociaux (fin de plan).

## Points tranchés le 2026-07-25 (anciennement ouverts)

- **Nwiro/UE5 vs Godot** — historique DEC-009 ; **remplacé 2026-08-09 par DEC-017**
  (serveur UE5.8 + Godot optionnel ; Nwiro abandonné).
- **Mode dev ouvert par défaut** — tranché : `HUB_API_KEY` obligatoire dans tous les
  environnements, plus de bypass. Voir `DECISIONS.md` DEC-010, `BUGS.md` SEC-002.

## Points tranchés le 2026-08-09 (P0)

- **Pont Gaming** — serveur UE5.8 (chat + GDD + outils agents), pas Nwiro (DEC-017).
- **Eve Pi** — différé jusqu’à `PI_HOST` ; agents = Hub SSH ; WinSCP = humain (DEC-018).
- **UI Finances/Marketing** — `*-v2` live ; stash pole-dashboard jeté (DEC-019).
- **`budget_transfer`** — toujours reporté (note DEC-016).

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

### Phase 11 — Refonte UI départements App / Gaming / Robotique
**Objectif :** un socle d'interface identique sur tous les départements (Équipe /
Projets / Missions / Backlog / Documentation / Analytics / Paramètres), contenu
spécialisé par métier — philosophie "80% commun, 20% métier" (cf. plan Emilie du
2026-07-31). Gaming ajoute un onglet Assets, Robotique un onglet Laboratoire.
**Livré :**
- App : `/app` (déjà en place), page détail projet `/projects/[id]` (5 sous-vues :
  vue d'ensemble, modules, équipe/fiche agent/flow, conversation).
- Gaming : `/gaming` — roster visuel (3 agents réels + 7 postes vacants), DA
  cinématique (grille viewport discrète, Obsidian/Titane/Cuivre).
- Robotique : `/robo` — roster visuel (2 agents réels + 8 postes vacants), DA
  labo (grille titane).
- Fonctionnalités réelles de l'ancien `/gaming`/`/robo` préservées, repliées en bas
  de page (`GamingConsole`, `GddWorkspace`, `RoboConsole`, `AppConsole`).
- Un seul branchement réel fait au passage : le compteur "Composants BOM" de la
  carte projet Eve tire les vraies données de `/bom/eve` (au lieu d'un placeholder).
**Non couvert (voir phases 12+ ci-dessous) :** tout ce que la maquette montre mais
que le Hub ne suit pas encore réellement — listé et commenté directement dans le
code (`mock-data.ts` de chaque département, `services/gstack` non concerné).
**Statut :** ✅ Complete, validé par Emilie le 2026-07-31.

### Phase 12 — Fondations données transverses
**Objectif :** ajouter à `Ticket` les champs qui manquaient et que Missions/Backlog
simulaient par un hash stable — `assignee_agent_id`, `story_points`, `due_date`.
**Livré :**
- Colonnes ajoutées via `supabase/migrations/20260730120000_ticket_assignee_points_due.sql`
  (nullable, pas de backfill — les tickets existants restent sur fallback) +
  reflet dans `database/schema.sql`.
- `TicketCreate`/`TicketUpdate` (`api/schemas.py`) + `POST /tickets`/`PATCH /tickets/{id}`
  (`api/routers/core.py`) acceptent et persistent les 3 champs.
- `Ticket`/`CreateTicketPayload`/`UpdateTicketPayload` (`web/src/lib/types.ts`,
  `web/src/lib/tickets.ts`) mis à jour ; `CreateTicketModal` (composant partagé)
  gagne 3 champs — Assigné (select agents du bureau), Points, Échéance.
- Missions (App/Gaming/Robo) : la carte ticket utilise `assignee_agent_id`/
  `story_points` réels en priorité, avec fallback `pseudoAssignee`/`pseudoPoints`
  (hash stable) pour les tickets créés avant cette phase — jamais de trou visuel.
  Échéance réelle affichée (badge rouge si dépassée), auparavant absente de la
  maquette.
- Backlog Gaming/Robo : le "recommandé" utilise le vrai assigné quand présent
  (libellé passe à "Assigné"), l'échéance réelle remplace l'ETA en semaines
  quand elle existe. Backlog App inchangé ("auteur"/"sprint" ne correspondent
  pas au même concept qu'assigné/échéance — laissés en l'état).
- `web/src/components/shared/missions-kanban.test.tsx` mis à jour (fixture avec
  les 3 nouveaux champs).
**Non couvert :** pas de backfill des tickets existants (restent sur fallback
tant qu'ils ne sont pas réassignés manuellement) ; `STATUS_LOAD` (charge par
agent) reste dérivé du statut agent, pas du nombre réel de tickets assignés —
hors scope de cette phase, à traiter séparément si besoin.
**Statut :** ✅ Complete, 2026-07-30.

### Phase 13 — Agents manquants Gaming (7) + Robotique (8)
**Objectif :** créer les 15 personas décrits par le plan (Gaming : AI Programmer,
Environment/Technical Artist, Narrative Designer, VFX/Sound Designer, QA ;
Robotique : Vision IA, Électronique, Firmware, Mécanique, Industrial Design, QA
Robot, Safety, Simulation) pour remplacer les "postes vacants" visuels de la
Phase 11 par de vrais agents.
**Livré (les 15) :**
- `config/agent_personas.py` — 15 entrées `AGENT_PERSONAS` + ajout aux listes
  `agents` de `ROOMS["gaming_studio"]`/`ROOMS["hardware_workshop"]` et
  `TEAMS["gaming"]`/`TEAMS["robo"]` (les deux équipes passent en
  `intra_competition: True`, cohérent avec l'équipe `app` à effectif comparable).
- `config/agent_specs_registry.py` — 15 `AgentOperatingSpec` complets (mission,
  responsabilités, hors périmètre, processus, priorités, relations).
- `config/agent_models.py` — 15 entrées `AGENT_TIERS` (toutes `standard`) + 15
  alias `<id>_agent`. Retrait au passage de l'alias `"narrative_designer":
  "level_designer"`, devenu faux depuis que Narrative Designer est un agent à
  part entière distinct de Finn (Level & Narrative Designer).
- `agents/<id>_agent.py` × 15 — pattern `AgentBase` (comme `level_designer_agent.py`,
  pas le pattern CrewAI legacy de `hardware_agent.py`/`embedded_dev_agent.py`),
  une méthode métier réelle par agent (ex. `design_behavior`, `assess_risk`).
- `api/route_common.py` (imports), `api/schemas.py` (15 Request schemas),
  `api/routers/agents_pole.py` (15 endpoints `POST /agents/<slug>/...`).
- `web/src/lib/agent-bureau.ts` — 15 entrées `BUREAU_AGENTS` (les rosters
  Équipe de `/gaming` et `/robo` les affichent automatiquement comme cartes
  réelles, sans autre changement de composant).
- `VACANT_ROLES` vidé dans `gaming-v2/page.tsx` et `robo-v2/page.tsx` — les 10
  rôles de chaque département ont maintenant un agent réel.
- `CLAUDE.md` — tableau des 34 agents mis à jour (49 au total).
**Non couvert :** pas de frontend `AGENT_LABELS` à maintenir — `model-settings-view.tsx`
lit déjà `display_name`/`role_label` depuis le backend (`get_all_agent_models()` →
`AGENT_PERSONAS`), donc l'étape 6 de la checklist `CLAUDE.md` est obsolète pour ce
projet (source de vérité unique = `AGENT_PERSONAS`). Vérifié : app FastAPI démarre,
15 endpoints présents, `tsc`/`ruff` propres.
**Statut :** ✅ Complete, 2026-07-30.

### Phase 14 — Système Modules réel (page détail projet)
**Objectif :** remplacer `modulesForProject` (mock-data.ts) par une vraie table
`project_modules` (nom, statut, progression, fonctionnalités, tests, bugs) +
endpoints CRUD. Bénéficie à App/Gaming/Robotique uniformément (page détail
projet partagée).
**Livré :**
- `supabase/migrations/20260730130000_project_modules.sql` — table
  `project_modules` (RLS + policy `authenticated_full_access`, même posture
  que `tickets`/`roadmap`) + reflet dans `database/schema.sql`.
- `api/schemas.py` (`ModuleCreate`/`ModuleUpdate`) + `api/routers/core.py`
  (`GET/POST /modules`, `PATCH/DELETE /modules/{id}`).
- `web/src/lib/types.ts` (`ProjectModule`, `ModuleStatus`) + `web/src/lib/modules.ts`
  (client API) + `web/src/components/shared/create-module-modal.tsx`.
- `modules-view.tsx` réécrit : cartes + détail sur vraies données, changement
  de statut en direct (`<select>` → `PATCH /modules/{id}`), création via modal.
- `page.tsx` : fetch des modules levé au niveau page (même pattern que les
  tickets), passé en props à `ModulesView` — `totalFeatures` de la vue
  d'ensemble utilise désormais les vrais comptes.
- `mock-data.ts` : `modulesForProject`/`MockModule` retirés (code mort).
  `featuresForModule`/`dependenciesForModule` (détail ligne par ligne à
  l'intérieur d'un module) restent provisoires — pas de table pour ce niveau
  de granularité, à traiter dans une phase ultérieure si besoin.
**Vérifié :** `tsc`/`ruff` propres, endpoints `/modules` montés au boot FastAPI,
migration `20260730130000` poussée et confirmée sur Supabase (2026-07-30).
**Statut :** ✅ Complete, 2026-07-30.

### Phase 15 — Décisions en attente réelles
**Objectif :** la page détail projet affichait 3 décisions factices
(`decisionsEnAttente`) — investiguer si un système existant peut être réutilisé
plutôt que d'en dupliquer un nouveau.
**Investigation :** le nav "▤ Décisions" (badge `useConsoleData()`) route vers
`/ceo` (dossiers R&D en attente, brief du jour, PRs GitHub) — un concept CEO
transverse, pas scopé par projet, pas réutilisable tel quel. En revanche la
table **`roadmap`** (déjà réelle, CRUD complet depuis longtemps : `GET/POST
/roadmap`, `PATCH/DELETE /roadmap/{id}`, `web/src/lib/roadmap.ts`) a
exactement la forme voulue — un item de statut `idea`/`planned` **est**
littéralement une décision/arbitrage pas encore tranché sur ce projet.
**Livré :**
- "Décisions en attente" = `fetchRoadmapItems({ project_id })` filtré sur
  `status IN (idea, planned)`, triés par priorité (déjà fait côté API).
  Affiche titre/description/priorité réels (`PRIORITY_STYLES`).
- Bouton "＋ Ajouter" ouvre `CreateRoadmapModal` (composant déjà existant,
  réutilisé tel quel — `defaultStatus="idea"`).
- `decisionsEnAttente`/`MockDecision` retirés de `mock-data.ts` (code mort).
- **Onglet "Roadmap"** de la page détail projet volontairement laissé en
  placeholder — hors scope de cette phase (un vrai onglet Roadmap réutiliserait
  `RoadmapView`, qui est conçu comme une page globale multi-projets, pas un
  composant scopé à injecter tel quel ; à traiter séparément si voulu).
**BUG-007 découvert et corrigé en implémentant cette phase :** la table
`roadmap` en production avait dérivé de `database/schema.sql` — `priority` y
était `INTEGER` (pas `TEXT`+`CHECK`) et le `CHECK` de `status` n'incluait
jamais `idea`. Résultat : `POST /roadmap` échouait à 100% dès qu'un statut ou
une priorité était fourni, invisible jusqu'ici faute d'avoir déjà créé un item
en prod (0 lignes constatées). Deux colonnes documentées (`updated_at`,
`linked_ticket_id`) manquaient aussi réellement — `POST /roadmap/from-ticket/{id}`
était donc également 100% cassé. Migrations
`supabase/migrations/20260730140000_roadmap_status_priority_fix.sql` et
`20260730150000_roadmap_missing_columns.sql` appliquées (aucune ligne réelle
affectée) — voir `BUGS.md` BUG-007 pour le détail complet.
**Vérifié en live :** création d'une décision (`idea`, priorité `high`) via
l'UI réelle → apparaît dans "Décisions en attente" avec les bons champs →
supprimée après vérification. `tsc`/`ruff` propres.
**Statut :** ✅ Complete, 2026-07-30.

### Phase 16 — Gaming : pipeline build/télémétrie UE5
**Objectif :** brancher un vrai flux de build (branche Git, build #, FPS, crashs,
draw calls).
**Investigation :** `skills/skill_nwiro.py` (209 outils : Blueprints, Materials,
World/Actors, PIE Runtime, Sequencer, Niagara VFX...) est un pont de **scripting
d'éditeur UE5 en direct**, pas un système de build/CI — aucune catégorie
build/profiling parmi ses outils. Vérifié : aucun projet Wyrdheim UE5 n'existe
sur cette machine (`C:\Dev` ne contient qu'ALUNA_HUB/NAÏA/NUAWAY/RESONANCE),
UE5 n'y est pas installé, `nwiro_is_available()` renvoie `False`. Il n'existe
donc aujourd'hui **aucun pipeline de build UE5 réel**, nulle part.
**Scope retenu (décision Emilie 2026-07-30) :** construire le réceptacle
Hub-side — base, API, UI — prêt à recevoir de vraies données le jour où un
pipeline de build existe, plutôt que d'attendre ou d'inventer des chiffres.
**Livré :**
- Table réelle `gaming_builds` (branche, build#, version jeu/moteur, statut,
  FPS moyen, crashs, draw calls, commit) — migration
  `supabase/migrations/20260730160000_gaming_builds.sql` (RLS incluse) +
  reflet `database/schema.sql`.
- `api/schemas.py::GamingBuildCreate` + `GET/POST /gaming/builds`
  (`api/routers/core.py`).
- `web/src/lib/gaming-builds.ts` (client) + `GamingBuild` (types.ts).
- Carte projet (`gaming-v2/projects-tab.tsx`) : version/build/FPS/crashs
  affichent le dernier build réel rapporté, `—` si aucun.
- Carte agent (`gaming-v2/page.tsx`, onglet Équipe) : remplace
  `agentBuildInfo` (branche/build/commit fictifs **par agent**, sans aucun
  système réel de suivi Git par personne) par le dernier build réel **partagé**
  par toute l'équipe — honnête, puisqu'aucun outil ne permet de savoir qui
  travaille sur quelle branche aujourd'hui. Affiche "Aucun build rapporté" à
  vide.
- `scripts/report_ue5_build.py` — script autonome (aucune dépendance Hub, tourne
  depuis une machine de build séparée) qui POST un build vers `/gaming/builds`.
  À brancher en fin de pipeline UAT/CI le jour où celui-ci existera.
- `mock-data.ts` : `agentBuildInfo`/`BUILD_BRANCHES` retirés ;
  `projectStats` réduit à `bugs`/`features` (encore provisoires, hors scope).
**Non couvert :** `bugs`/`features` (carte projet) et draw calls/Lumen/Nanite
(mentionnés dans l'objectif d'origine, pas encore dans l'UI — la table les
supporte déjà côté `draw_calls`) — pas de compteur Lumen/Nanite séparé prévu
pour l'instant, `draw_calls` suffit comme premier signal de perf rendu.
**Bug trouvé en testant** : le script utilisait des emoji (✅/❌) dans ses
messages de sortie, provoquant un `UnicodeEncodeError` sur un terminal Windows
en cp1252 (le POST réussissait quand même, seul l'affichage plantait) —
corrigé (`[OK]`/`[ERREUR]` ASCII).
**Vérifié en live :** script exécuté contre le vrai projet "Wyrdheim Online" →
build créé → carte agent et carte projet affichent les vraies valeurs
(capture d'écran) → nettoyé après vérification.
**Statut :** ✅ Complete pour le réceptacle Hub-side, 2026-07-30 — la partie
"faire tourner un vrai build UE5" reste à faire côté studio (Nova/Emilie),
hors périmètre d'un assistant de code.

### Phase 17 — Gaming : pipeline Assets réel
**Objectif :** connecter l'onglet Assets à un vrai inventaire au lieu des
exemples déterministes actuels.
**Contexte :** contrairement à la Phase 16, le projet Wyrdheim existe bel et
bien — il est sur un disque séparé, non accessible depuis cet environnement
(confirmé par Emilie). Contrairement à un pipeline de build, un inventaire
d'assets n'a besoin de rien d'autre qu'un accès au dossier réel : scope plus
directement réalisable qu'un connecteur Perforce/UE5 asset registry
(nécessiteraient des identifiants/API que le Hub n'a pas).
**Livré :**
- Table réelle `gaming_assets` (catégorie = dossier parent réel, type = extension
  réelle, nom, chemin, taille en octets, date de modification réelle) —
  migration `supabase/migrations/20260730170000_gaming_assets.sql` (RLS) +
  reflet `database/schema.sql`.
- `GET /gaming/assets` (liste) + `POST /gaming/assets/sync` (resynchronisation
  complète : purge puis réinsertion — reflète l'état du dossier à l'instant du
  scan).
- `scripts/sync_ue5_assets.py` — scanne récursivement un dossier réel (aucune
  dépendance Hub, tourne depuis n'importe quelle machine ayant accès au disque
  où se trouve Wyrdheim) et pousse l'inventaire. Mapping extension → type :
  `.uasset`→Blueprint, `.umap`→Niveau, textures/sons/mesh usuels.
- `assets-tab.tsx` réécrit : catégories dérivées dynamiquement des vraies
  données (plus de liste fictive à 10 catégories), taille/date réelles
  formatées, état vide honnête avec la commande à lancer.
**Vérifié en live :** dossier de test réel créé (4 fichiers dans
Characters/Textures/Audio) → scanné → 4 assets apparaissent dans l'UI avec
les bonnes catégories/tailles/dates (capture d'écran) → resynchronisé avec un
dossier vide pour confirmer que la purge fonctionne → nettoyé.
**Statut :** ✅ Complete, 2026-07-30 — prêt dès qu'Emilie/Nova lance le script
contre le vrai dossier Content de Wyrdheim.

### Phase 18 — Gaming : intégrations Steamworks + Discord
**Objectif :** Steam Wishlist réel (Steamworks API) et membres Discord réels (bot)
pour l'onglet Analytics.
**Décision Emilie (2026-07-30) :** construire le réceptacle + un endroit pour les
clés (pas encore possédées) — même logique que les Phases 16/17.
**Investigation :** `skills/skill_discord_wyrdheim.py` existait déjà (post/lecture
de messages Discord via bot) — étendu plutôt que dupliqué. Aucune intégration
Steam n'existait. Le nombre de **wishlists Steam n'est pas exposé par une API
publique Valve** — uniquement visible dans le dashboard Steamworks Partner
(accès partenaire, pas une simple clé Web API) : affiché honnêtement comme non
disponible plutôt que deviné ou omis silencieusement. Le nombre de **joueurs
simultanés** (`GetNumberOfCurrentPlayers`) est en revanche public et sans clé —
branché comme métrique Steam réelle de substitution.
**Livré :**
- `config/settings.py` + `.env.example` — 4 emplacements de config :
  `STEAM_API_KEY`, `STEAM_APP_ID`, `DISCORD_BOT_TOKEN` (existant), `DISCORD_GUILD_ID`
  (déjà documenté dans `.env.example`, jamais lu par le code avant aujourd'hui).
- `skills/skill_steam.py` (nouveau) — `get_concurrent_players()` réel,
  `get_wishlist_count()` documenté `None` de façon permanente et explicite.
- `skills/skill_discord_wyrdheim.py` — `get_member_count()` ajouté (réutilise
  `get_headers()`/`discord_is_configured()` existants).
- `GET /gaming/community-stats` (`api/routers/core.py`).
- `web/src/lib/gaming-community.ts` + `GamingCommunityStats` (types.ts).
- `analytics-tab.tsx` — section COMMUNAUTÉ & DISTRIBUTION : "Joueurs en ligne
  (Steam)"/"Membres Discord" réels, "Non configuré" tant que les clés sont
  vides ; note explicite sur l'absence de Wishlist.
**Vérifié en live :** `get_concurrent_players()` testé avec un vrai App ID Steam
public (CS2, 730) → nombre de joueurs réel renvoyé (876 720) — preuve que le
code fonctionne, il ne manque que le vrai `STEAM_APP_ID` de Wyrdheim. Capture
d'écran de l'onglet Analytics confirmant l'état "Non configuré" honnête tant
qu'aucune clé n'est renseignée.
**Statut :** ✅ Complete pour le réceptacle + les emplacements de clés,
2026-07-30 — à activer en renseignant `STEAM_APP_ID` (une fois Wyrdheim publié
sur Steamworks) et `DISCORD_BOT_TOKEN`/`DISCORD_GUILD_ID` dans `.env`.

### Phase 19 — Robotique : BOM étendu + Laboratoire connecté
**Objectif :** étendre le vrai système BOM existant (`/bom/eve`, phase 11) au suivi
PCB/firmware/tests par projet, et connecter l'onglet Laboratoire à de vrais bancs
de test/capteurs plutôt qu'un journal d'exemples.
**Décision Emilie (2026-07-30) :** construire tout ce qui est possible sans le
robot physique — même logique que les Phases 16-18.
**Livré :**
- Tables réelles `robo_builds` (branche, stage, version, PCB, firmware, tests
  passés, anomalies) et `robo_lab_tests` (catégorie, nom, statut pass/fail/en
  cours, valeur mesurée) — migration
  `supabase/migrations/20260730180000_robo_builds_lab_telemetry.sql` (RLS).
- `GET/POST /robo/builds`, `GET/POST /robo/lab-tests` (`api/routers/core.py`).
- `scripts/report_robo_build.py` + `scripts/report_lab_test.py` — scripts
  autonomes à lancer après une vraie itération hardware/firmware ou un vrai
  essai sur banc.
- `projects-tab.tsx` : version/PCB/firmware/tests passés/anomalies viennent du
  dernier build réel ; composants BOM reste branché sur `/bom/eve` (Phase 11,
  inchangé).
- `page.tsx` (Équipe) : carte agent affiche le dernier build hardware réel
  partagé (comme Gaming), "Aucun build rapporté" à vide.
- `laboratoire-tab.tsx` réécrit : vrais essais, catégories dynamiques, état
  vide honnête avec la commande à lancer.
- `mock-data.ts` : `agentBuildInfo`/`projectStats` entièrement retirés (plus
  aucun champ placeholder restant, contrairement à Gaming).
**Vérifié en live :** build hardware + 2 essais labo (1 réussi, 1 échec)
rapportés pour Eve → apparaissent correctement dans Équipe/Projets/Laboratoire
(captures d'écran) → nettoyés après vérification.
**Statut :** ✅ Complete pour le réceptacle, 2026-07-30 — le comptage BOM était
déjà réel depuis la Phase 11 ; PCB/firmware/tests/labo attendent qu'Eve (le
robot physique) ou un banc de test rapportent une vraie itération.

### Phase 20 — Robotique : télémétrie IoT (Analytics)
**Objectif :** consommation, température, batterie, cycles, autonomie réels depuis
le hardware Eve plutôt que des valeurs de démonstration.
**Livré :**
- Table réelle `robo_telemetry` (puissance, température, CPU, batterie, cycles
  de charge, autonomie) — même migration que la Phase 19.
- `GET/POST /robo/telemetry`.
- `scripts/report_robo_telemetry.py` — prévu pour tourner directement sur le
  Raspberry Pi d'Eve (lecture de capteurs réels) une fois disponible ;
  utilisable manuellement en attendant.
- `analytics-tab.tsx` : section ÉNERGIE & THERMIQUE sur la dernière télémétrie
  réelle, "—" à vide. "Tests passés" (FIABILITÉ & TESTS) calculé sur les vrais
  essais Laboratoire (Phase 19) quand il en existe — petit bonus gratuit du
  fait que les deux phases partagent la même base. Fiabilité/Unités
  produites/Défauts restent provisoires (pas de suivi manufacturing).
**Vérifié en live :** télémétrie rapportée pour Eve → tuiles ÉNERGIE &
THERMIQUE affichent les vraies valeurs ; "Tests passés" à 50% cohérent avec
1 essai réussi / 1 échoué rapportés en Phase 19 → nettoyé après vérification.
**Statut :** ✅ Complete pour le réceptacle, 2026-07-30 — dépend de capteurs
IoT réels sur Eve pour recevoir des données en continu.

### Phase 21 — Outils réels pour les 15 agents spécialisés Gaming/Robotique
**Objectif :** les 15 agents créés en Phase 13 n'ont aujourd'hui qu'une méthode LLM
texte → JSON chacun (aucun outil `tool()`, aucune connexion réelle) — contrairement
à leurs voisins `dev_gaming` (ex-Nwiro / futur UE5.8), `embedded_dev` (SSH Pi/GPIO)
ou `hardware` (BOM Supabase). Leur brancher de vrais outils : **serveur UE5.8**
(DEC-017) pour `ai_programmer` / `technical_artist` / `vfx_artist` ; accès SSH Pi /
GPIO pour `vision_ai` / `firmware` / `electronics` ; lecture/écriture BOM pour
`mechanical` / `electronics` / `industrial_design` ; bancs pour `qa_robot` / `safety`.
**Dépendances :** phases 16 (build/télémétrie UE5) et 19 (BOM + Laboratoire) ;
pont Nwiro **abandonné** (DEC-017) — ne plus étendre `skill_nwiro`.
**Vague 3 (2026-08-09) — premier sprint « 3 skills utiles » :**
- `ai_programmer` → `POST /agents/ai-programmer/nwiro-probe` (**legacy** jusqu’au
  skill UE5.8)
- `firmware` → `POST /agents/firmware/pi-probe` (`skill_pi_ssh` + denylist ; Pi
  optionnel — DEC-018)
- `electronics` → `POST /agents/electronics/bom-context` (`skills/skill_bom.py`)
**2026-08-09 soir — Eve sourcing / montage :**
- `POST /agents/electronics/alternatives` — options pro/budget (estimations)
- `POST /agents/mechanical/assembly-plan` — plan de montage depuis BOM
- `POST /agents/hardware/infra-blueprint` — robot physique vs app compagnon
  (`dev_app`, comme Naïa) ; `GET /robo/pi-bridge` (SSH Hub, Pi différable)
- UI `/robo` console : panneau BOM + boutons IA
**P0 (2026-08-09) :** DEC-017/018 — Pi reste différé.
**Vague A (2026-08-09) — pont UE5.8 (DEC-017) :**
- Spec : `SPEC_UE58_BRIDGE.md` (health / capabilities / chat / GDD / tools/call)
- Skill : `skills/skill_ue58.py` + router `api/routers/ue58_bridge.py`
- Probes : `POST /agents/{ai-programmer|technical-artist|vfx-artist}/ue58-probe`
- Status / chat / GDD : `GET /gaming/ue58/status`, `POST /gaming/ue58/chat`,
  `POST /gaming/ue58/gdd/sync` ; UI console Gaming affiche le statut UE5.8
- Nwiro probes = legacy (conservés, non étendus)
**DEC-020 (2026-08-10) — agency PC type Claude Code :**
- `skill_gaming_agency` + `POST /gaming/studio/agency/run` sur `UE_PROJECT_PATH`
- UI : lancer Nova/Kenji/Otto/Diego sur le projet UE local (worktree)
**Vague B (2026-08-10) — robotique probes restants :**
- `skill_robo_lab` + router `robo_phase21` (pas de croissance `agents_pole`)
- BOM : mechanical / industrial_design ; lab : qa_robot / safety / simulation ;
  Pi probe : vision_ai (DEC-018)
- UI `/robo` : panneau probes Vague B
**Vague A suite (2026-08-10) — gaming probes restants :**
- environment_artist / narrative_designer / sound_designer / qa_gaming :
  `probe_ue58` + endpoints ; narrative `search_canon` ; qa `list_recent_builds` ;
  agency `run_studio_task` (env + sound) ; filtres `AGENT_CAP_FILTERS`
**Statut :** ✅ Hub-side Complete (Vague D 2026-08-11) — UI 100 % honnête
(builds/télémétrie/lab/community ou « — ») ; studio live dépend encore de
`UE_PROJECT_PATH` + serveur UE5.8 + Pi optionnel (DEC-017/018/020).

### Phase 22 — Redesign R&D v2 : socle & coquille (`/rnd-v2`)
**Objectif :** premier étage d'une refonte en 7 phases (22-28) du département
R&D — passer d'un "chat + liste d'idées" à une expérience "laboratoire"
(Skunk Works/OpenAI/xAI), en réutilisant le pattern déjà validé pour
App/Gaming/Robo (`app-v2`/`gaming-v2`/`robo-v2`) plutôt que l'ancien système
`DepartmentWorkspace` encore utilisé par `/rd`. Plan complet approuvé par
Emilie : `PLAN` en pièce jointe de la session (Phases 22-28 détaillées —
socle, Innovation Pipeline, Incubateur Kanban, Moteur Conseil IA, Arbres
mindmap, Dossiers table, Explorer veille externe).
**Investigation :** le backend R&D (~55 endpoints `api/routers/rnd.py`,
pipeline dossier 7 étapes, comité multi-agents, arbre d'hypothèses réel,
dispatch post-CEO déjà fonctionnel) est très mature — la refonte est donc
très majoritairement frontend, contrairement à Gaming/Robo Phases 15-20 qui
avaient dû reconstruire de vraies données depuis zéro.
**Décision (validée avec Emilie) :** nouvelle route `/rnd-v2`, `/rd` reste
la page réelle et fonctionnelle jusqu'à bascule finale (même précédent que
`/app` → `/app-v2`) ; réutilise `C`/`Ring`/`Bar` de `app-v2/shared.tsx` et
`MissionBox`/`ChatPanel`/`RecentTasksPanel`/`ApercuPanel` de `app-v2/team.tsx`
sans dupliquer.
**Livré :**
- `web/src/app/rnd-v2/page.tsx` — coquille complète (en-tête, sidebar
  Départements, barre d'onglets, barre de commandes) calquée sur
  `gaming-v2/page.tsx`, avec un seul onglet Équipe pour cette phase (les
  6 autres arrivent Phases 23-28 — pas d'onglet fantôme désactivé).
  Onglet Équipe sur les 2 vrais agents du bureau R&D (Idris Okonkwo —
  Brainstorm, Alex Mercer — R&D Recherche autonome), roster + panneau
  détail (Mission/Discussion/Tâches récentes/Aperçu) réutilisés à
  l'identique du pattern App.
- `web/src/lib/routes.ts` — `ROUTES.rndV2 = "/rnd-v2"` (nouvelle constante,
  `ROUTES.rd` inchangé).
- `web/src/components/layout/hub-shell.tsx` — `/rnd-v2` ajouté à la liste
  des routes "immersives" (chrome autonome, pas de double-wrap
  `ConsoleShell`), même mécanisme que App/Gaming/Robo v2.
- **Hygiène schema.sql (repérée en Phase 22, indépendante de la feature) :**
  les 4 migrations R&D (`20260613120000_rnd_dossiers.sql`,
  `20260613150000_rnd_ceo_phase6.sql`, `20260613150100_roadmap_rnd_dispatch.sql`,
  `20260617120000_rnd_hub_branch.sql`) n'avaient jamais été mirrorées dans
  `database/schema.sql` — comblé (nouvelle section "4f", + colonnes
  `rnd_dossier_id`/`session_type`/`image_asset_path` ajoutées aux
  définitions `roadmap`/`posts_queue`/`brainstorm_summaries` existantes).
  Gap restant, hors périmètre : `lore_entries`/`bom_eve` (qui reçoivent
  aussi une colonne `rnd_dossier_id`) ne sont pas du tout mirrorées dans
  `schema.sql`, avant même cette phase — signalé en commentaire dans le
  fichier plutôt que corrigé silencieusement.
**Vérifié en live :** `tsc --noEmit` et `eslint` propres sur tout le projet ;
`/rnd-v2` ouvert dans le navigateur — rendu identique au pattern
App/Gaming/Robo (en-tête, sidebar avec "03 R&D" actif, ALNUA CORE), les 2
agents réels s'affichent et se sélectionnent correctement (Idris Okonkwo ↔
Alex Mercer), toutes les zones sans donnée réelle affichent un état vide
honnête ("Aucune mission en cours.", "Aucun projet rattaché à ce bureau.")
plutôt qu'une donnée fabriquée. Aucune erreur console/réseau après
stabilisation (une salve de 404/500 observée sur un premier essai s'est
avérée être un artefact de rechargement à chaud Next.js pendant que
`schema.sql`/`ROADMAP.md` étaient en cours d'édition — non reproductible).
**Non couvert (prévu pour les phases suivantes) :** onglets Pipeline
(Phase 23), Incubateur (24), Conseil (25), Arbres (26), Dossiers (27),
Explorer (28) ; `/rd` reste la page de référence jusqu'à la bascule finale.
**Statut :** ✅ Complete, 2026-07-31.

### Phase 23 — Redesign R&D v2 : Innovation Pipeline (cartes)
**Objectif :** renommer Centre R&D → "Innovation Pipeline" — remplacer les
vues liste par des cartes score/verdict animées, + une vue détail dossier
"façon Apple" en cliquant une carte.
**Réutilisé (aucun changement backend, confirmé) :** `RndIdeaOut`
(`score`/`market_score`/`feasibility_score`/`vision_score`/`verdict`) déjà
calculé par `rnd_center.py` ; `web/src/lib/rnd.ts::fetchRndIdeas` et
`web/src/lib/rnd-dossier.ts::fetchRndDossier`/`fetchDossierPipeline`, déjà
existants ; logique de mise en forme portée (pas le composant) depuis
`web/src/components/rnd/rnd-pitch-modal.tsx::buildPitchBlocks`.
**Livré :**
- `web/src/app/rnd-v2/pipeline-tab.tsx` — grille de cartes (score en anneau,
  badge GO/MAYBE/NO, sous-scores Marché/Tech/Business, pulse discret CSS
  `animate-rnd-card-breathe` défini dans `globals.css`), filtres GO/MAYBE/NO,
  triées par score. Onglet "Pipeline" ajouté à `rnd-v2/page.tsx`.
- `web/src/app/rnd-v2/dossier-detail-view.tsx` — overlay plein écran :
  en-tête (score, verdict, sous-scores, frise pipeline 7 étapes via
  `fetchDossierPipeline`), puis onglets Résumé/Pitch/Marché & concurrence/
  Business/Technique/Risques/Budget/Débat IA/Décision CEO (`MarkdownContent`
  sur le contenu réel des sections). Idée sans dossier → état honnête
  ("juste l'évaluation initiale de l'agent") + bouton "Créer le dossier
  détaillé" (réutilise `promoteRndIdea`, déjà existant).
**Vérifié en live :** `tsc`/`eslint` propres ; 38 idées réelles chargées et
affichées avec leurs vrais scores/verdicts (`/rnd/ideas` en prod) ; overlay
détail testé sur une idée réelle sans dossier (SentinelAI) — état vide
honnête + bouton promotion corrects ; 10 dossiers réels confirmés existants
en base (ex. SkillForge Marketplace, NomadComply) pour la suite. Aucune
erreur console.
**Correctif (2026-07-31, signalé par Emilie) :** l'overlay masquait
*tout* le contenu (Résumé/Pitch/Décision CEO) dès qu'une idée n'avait pas
encore de dossier, alors que `buildApplePanels()` génère déjà un vrai
Résumé/Pitch à partir de `idea.description`/`reasoning` sans avoir besoin
d'un dossier — le rendu vérifié ci-dessus ("état vide honnête") était en
fait le bug : pour 37 des 38 idées réelles (toutes sauf celles avec un
dossier), aucun texte de présentation n'apparaissait du tout. Corrigé :
les panneaux s'affichent désormais toujours dès qu'au moins un a du
contenu ; le bandeau "pas encore de dossier détaillé" devient une bannière
au-dessus des onglets plutôt qu'un remplacement total. Revérifié en direct
sur SentinelAI — Résumé/Pitch/Décision CEO s'affichent avec le vrai texte.
**Correctif 2 (2026-07-31) :** `web/src/lib/rnd.ts::fetchRndIdeas(verdict,
inboxOnly)` — quand `inboxOnly=false`, le paramètre `inbox_only` n'était
tout simplement jamais envoyé (`if (inboxOnly) params.set(...)`) au lieu
d'envoyer explicitement `"false"` ; le backend retombant sur son propre
défaut (`inbox_only=True`), Pipeline affichait un sous-ensemble "inbox"
(idées jamais promues/archivées) au lieu du pipeline complet — bug latent
depuis toujours dans `rnd.ts`, jamais déclenché avant Phase 23 car aucun
appelant ne passait `false` auparavant. Corrigé (+ limite remontée à 100,
plafond backend) ; revérifié en direct : 57 idées réelles affichées (contre
36-38 avant), plusieurs cartes affichent maintenant "Dossier ouvert" à la
place de "Pas encore de dossier" pour les idées réellement promues.
**Actions carte ajoutées (2026-07-31, demande Emilie) :** l'overlay détail
n'avait qu'une action ("Créer le dossier détaillé"). Ajouté 3 choix
explicites en en-tête : **Garder pour réfléchir** (ferme sans action),
**🧪 Incuber** (réutilise `updateIncubatorStage` — Phase 24 — passe l'idée
à l'étape Prototype de l'Incubateur), **Supprimer** (réutilise
`archiveRndIdea`, déjà existant côté client mais jamais câblé sur aucune
des deux vues détail R&D jusqu'ici). Vérifié `tsc`/`eslint` propres.
**"+ Nouvelle idée" branché (2026-07-31, demande Emilie) :** le bouton
existait déjà visuellement dans la barre de commandes mais ne faisait rien.
Ouvre désormais `new-idea-modal.tsx`, 2 modes :
- **Proposer une idée** → `injectRndIdea` (déjà existant, utilisé par
  l'ancienne page `/rd`, jamais branché sur rnd-v2) — ajout brut au
  Pipeline, `score: null` tant que le prochain cycle R&D ne l'a pas évaluée
  (honnête, pas de note fabriquée).
- **Lancer une recherche** → `services/deep_research.py::run_deep_research`
  (pipeline réel multi-rounds explore/approfondit/vérifie, jamais exposé
  sur aucune UI R&D avant, ni ancienne ni nouvelle) — affiche le rapport
  tel quel (synthèse/constats/actions recommandées/zones d'ombre), ne crée
  pas d'idée automatiquement.
- **Bug trouvé en testant :** le client appelait `/deep-research/run` — 404,
  le routeur `advanced_services.py` a `prefix="/services"` (visible dans le
  docstring de `run_deep_research` lui-même, manqué à la première lecture).
  Corrigé (`/services/deep-research/run`), revérifié : 200 réel.
**Vérifié en live :** "Proposer une idée" testé bout en bout via l'UI
(remplissage → clic → toast de confirmation → idée réelle créée en base) ;
"Lancer une recherche" testé via l'API — crédits OpenRouter de nouveau
épuisés au moment du test, mais `deep_research.py` dégrade déjà proprement
de lui-même (`executive_summary: "Synthèse indisponible."`, l'échec listé
dans `knowledge_gaps` plutôt qu'un plantage ou un faux rapport positif) —
aucun correctif nécessaire côté honnêteté, déjà bien fait en amont. Données
de test nettoyées (Supabase + `data/rnd_ideas.json`, gitignored).
**Bouton introuvable (2026-07-31, signalé par Emilie juste après) :** sous
~1280px de large (`xl` breakpoint Tailwind — un simple laptop non maximisé),
les 4 icônes de la barre de commandes perdent leur libellé (`hidden
xl:inline`) et deviennent 4 ronds identiques sans indice de ce qu'ils font
— "Nouvelle idée" (la seule vraiment câblée) illisible au milieu de 3
icônes décoratives inertes. Corrigé : `title` (info-bulle native) ajouté
aux 4 ; "Nouvelle idée" garde désormais son libellé visible à toute largeur
et un fond cuivre distinct, pour ne plus se confondre avec les 3 icônes
inertes. Revérifié à 1200px de large — bouton net et lisible.
**Chemin "dossier existant" vérifié (2026-07-31, pendant les correctifs
ci-dessus) :** ouvert sur SkillForge Marketplace (dossier réel) — les
8 onglets s'affichent (Résumé/Pitch/Marché & concurrence/Business/
Technique/Risques/Budget/Décision CEO) avec le vrai contenu du dossier,
sans le bandeau "pas encore de dossier" (masqué correctement). Dernier
angle non couvert de cette phase désormais fermé.
**Statut :** ✅ Complete, 2026-07-31.

### Phase 24 — Redesign R&D v2 : Incubateur (Kanban)
**Objectif :** nouvel onglet, Kanban Idée → Prototype → Validation → MVP →
Projet → Département. Glisser une carte vers Département doit créer un vrai
projet dans le département cible.
**Découverte en cours de route (a changé la conception) :** `record_ceo_decision`
exige qu'un package CEO existe déjà (`ceo_package_json`), et `generate_package`
n'est éligible que si le dossier a un statut avancé OU un rapport de comité
d'au moins 40 caractères (`PACKAGE_ELIGIBLE_STATUSES` /
`_ceo_package_eligible`, `agents/rnd_ceo_agent.py`). Glisser une idée fraîche
directement vers Département ne peut donc pas être automatisé de bout en
bout sans un vrai passage en comité — au lieu de simuler cette étape, le
nouvel endpoint **refuse honnêtement** (403, message explicite) quand ce
n'est pas encore le cas, plutôt que de fabriquer une approbation.
**Réutilisé :** `agents/rnd_ceo_agent.py::generate_package/record_ceo_decision/
dispatch_to_coo` (logique existante, aucune réécriture) ; `@hello-pangea/dnd`
(déjà une dépendance, déjà utilisé dans `web/src/components/roadmap/roadmap-kanban.tsx`).
**Livré :**
- Migration `supabase/migrations/20260731100000_rnd_incubator_stage.sql` —
  `rnd_ideas.incubator_stage` (6 valeurs, défaut `idee`) +
  `incubator_stage_updated_at`. Poussée en prod (`supabase db push --linked`).
  Mirrorée dans `database/schema.sql`.
- `services/rnd_schemas.py::RndIdeaOut.incubator_stage` +
  `services/rnd_repository.py::row_to_api_idea` (mapping) — et
  **`agents/rnd_center.py::get_top_ideas`** (bug détecté en vérifiant : ce
  chemin construit son propre dict à la main et omettait le nouveau champ,
  corrigé).
- `agents/rnd_ceo_agent.py::RndCeoAgent.promote_idea_to_department()` — crée
  le dossier si absent, génère le package si éligible, approuve, dispatch ;
  laisse remonter `CeoPackageNotReadyError` telle quelle si non éligible.
- Endpoints : `PATCH /rnd/ideas/{id}/incubator-stage` (étiquette simple,
  refuse `departement` avec un message dirigeant vers le bon endpoint) et
  `POST /rnd/ideas/{id}/incubator/promote-to-department`.
- `web/src/lib/rnd.ts` — `updateIncubatorStage`, `promoteIdeaToDepartment`,
  type `IncubatorStage`.
- `web/src/app/rnd-v2/incubateur-tab.tsx` — Kanban 6 colonnes
  `@hello-pangea/dnd`, mise à jour optimiste (+ rollback si erreur) pour les
  5 colonnes simples, état "Promotion en cours…" (pas d'optimisme) pour
  Département vu que l'appel peut être refusé.
**Vérifié en live :** migration poussée ; `PATCH .../incubator-stage`
testé bout en bout sur une idée réelle (idee→prototype→idee, confirmé puis
nettoyé) ; `PATCH ... {stage:"departement"}` refusé (400, message correct) ;
`POST .../promote-to-department` testé sur un dossier réel non éligible
(OptiR&D Lab, statut `draft`) → **403 avec le message honnête attendu**,
dossier et `incubator_stage` inchangés (aucun effet de bord) ; Kanban ouvert
dans le navigateur — 38 idées réelles toutes en colonne Idée (cohérent après
nettoyage), aucune erreur console.
**Non couvert :** le chemin de succès complet (dossier déjà éligible → vrai
dispatch) n'a pas été déclenché en direct — aucun des 10 dossiers réels
actuels n'a encore de rapport de comité, donc aucun n'est éligible
aujourd'hui ; se vérifiera naturellement une fois la Phase 25 (Conseil)
livrée et un premier comité réellement tenu.
**Statut :** ✅ Complete, 2026-07-31.

### Phase 25 — Redesign R&D v2 : Moteur Conseil (stratégique + IA)
**Objectif :** livrer ensemble la refonte Brainstorm ("Conseil stratégique
IA" — débat live 3 colonnes avec jauges) et "💎 Conseil IA" (input structuré
→ débat → vote individuel par agent → Décision Collective), les deux
partageant la même infrastructure.
**Investigation :** `RndCommitteeAgent` (comité dossier existant) exige
toujours un `dossier_id` réel — inutilisable pour une idéation libre ou une
évaluation sans dossier. Nouvelle orchestration (`RndCouncilAgent`), sans
sous-classer ni modifier `RndCommitteeAgent`.
**Décision roster (tranchée avec Emilie) :** 5 personas dédiés au Conseil,
noms distincts de tout agent existant (voir échange précédent — Mira/Nova
du texte de vision correspondaient en réalité à Mira Chen/Nova Fischer,
Gaming). Personas **inline** dans `agents/rnd_council_agent.py`
(`COUNCIL_MEMBERS`), **pas** d'entrée dans `config/agent_personas.py` : ils
n'ont pas de méthode solo (seulement une participation aux délibérations),
et `AgentAvatar` (frontend) rend un avatar à partir du seul (agent_id, name)
sans registre — `agent_models.py::AGENT_TIERS.get` retombe proprement sur
le tier "standard" pour un agent_id inconnu. Roster : Selene Marchetti
(Présidente), Kai Osei (Innovation), Freya Lindqvist (Faisabilité), Darius
Whitmore (Business), Amara Solis (Données).
**Schéma :** migration `supabase/migrations/20260731110000_rnd_council_votes.sql`
— `rnd_committee_sessions.dossier_id` devient nullable + `session_kind`
('dossier'/'strategic'/'evaluation', défaut 'dossier' = rétrocompatible) +
`idea_id`/`structured_input`/`topic` ; `rnd_committee_messages.dossier_id`
nullable ; nouvelle table `rnd_committee_votes` (verdict/confidence/
axis_scores/stance_text par agent, `round_index`+`is_final` pour servir à
la fois les jauges live et la Décision Collective finale). Poussée en prod,
mirrorée dans `database/schema.sql`.
**Livré :**
- `agents/rnd_council_agent.py::RndCouncilAgent` — `start_session`,
  `post_message` (async, 5 appels LLM en parallèle via `asyncio.gather` +
  `LLMClient.complete_async`, chaque membre répond en JSON structuré
  content/stance_text/verdict/confidence_pct/axis_scores),
  `compute_gauges` (Consensus = ratio d'accord entre verdicts, les 4 autres
  = moyenne des axis_scores), `close_session` (fige les votes `is_final`,
  agrège), `evaluate` (start+débat+clôture en un seul appel pour le
  formulaire structuré).
- **Garde-fou honnêteté (ajouté après un test réel en credits épuisés) :**
  `close_session` renvoie `deliberated: bool` — si tous les membres ont
  échoué (0 vote), pas de fausse "Décision Collective : MAYBE, 0%" ;
  `evaluate` lève une erreur claire (503) plutôt que de fabriquer un
  verdict. Le frontend respecte ce flag avant d'afficher la bannière.
- Nouveau routeur `api/routers/rnd_council.py` (5 endpoints), enregistré
  dans `api/routers/__init__.py::ALL_ROUTERS` (compte à l'origine **40** routers +
  `gdd` conditionnel — Phase E `trust` ; historique Phase 25 = 38 ; resync
  Audit 005 2026-09-07 : **86** routers réels, voir `BUGS.md` BUG-023).
- `web/src/lib/rnd-council.ts` — client complet.
- `web/src/app/rnd-v2/conseil-tab.tsx` — 3 colonnes (participants/
  conversation/jauges), toggle Discussion libre ↔ 💎 Conseil IA (formulaire
  budget/équipe/délai/type produit inline, pas un onglet séparé).
**Vérifié en live :** `ruff`/`tsc`/`eslint` propres ; session réelle créée
(`POST /rnd/council/sessions`) ; `post_message` réel testé — **crédits
OpenRouter épuisés au moment du test** (les 5 membres échouent proprement,
logués, endpoint reste 200 avec le message utilisateur seul plutôt que de
planter) ; bug BUG-006 (connexion Supabase HTTP/2 périmée) reproduit une
fois sur `/gauges` puis confirmé transitoire au retry ; `close_session` sur
session à 0 vote → `deliberated: false`, pas de fausse décision ; `evaluate`
sur le même scénario → 503 avec message honnête, vérifié explicitement ;
onglet Conseil ouvert dans le navigateur — 5 participants réels affichés,
états vides honnêtes ("Les jauges apparaissent dès que..."), aucune erreur
console propre à cet onglet. Sessions de test nettoyées (cascade FK
vérifiée : 0 message/vote orphelin).
**Non couvert :** le chemin de succès complet (débat réel avec réponses LLM
effectives, jauges qui bougent, Décision Collective réelle) n'a pas pu être
vérifié en direct — bloqué par les crédits OpenRouter épuisés au moment du
test (même blocage que Théo/dev_app, déjà documenté). Se vérifiera dès que
les crédits seront reconstitués ; le code du chemin heureux partage la même
plomberie déjà validée (parsing JSON, écriture DB, agrégation) que le
chemin d'échec testé.
**Statut :** ✅ Complete (réceptacle), 2026-07-31.

### Phase 26 — Redesign R&D v2 : Arbres (canvas mindmap interactif)
**Objectif :** remplacer le rendu SVG statique de l'arbre d'hypothèses
(`rnd-hypothesis-tree-graph.tsx`, `onClick` uniquement, aucun `useRef`/
gestionnaire de glisser) par un vrai canvas mindmap glissable — déplacer,
créer, relier/fusionner des nœuds, glisser pour promouvoir en dossier.
**Investigation :** `services/rnd_hypothesis_tree.py` (873 lignes) déjà très
mature — `build_tree_graph()` (layout BFS recalculé à chaque appel, jamais
persisté), `expand_node(manual=...)` (création manuelle de branche, déjà
prête), `promote_node_to_dossier()` (positionne déjà `status="merged"` +
crée le dossier). L'arbre est en revanche **strictement parent/enfant**
(`parent_id`/`children`, `build_tree_graph()` dérive ses `edges` de cette
hiérarchie, aucun concept pair-à-pair stocké) : glisser un nœud sur un autre
("relier") n'avait donc aucun endpoint — seul vrai trou backend de cette
phase.
**Décision :** "créer" = `expand_node(manual=...)` (existant) ; "fusionner/
promouvoir" = `promote_node_to_dossier()` (existant, positionne déjà
`merged`) ; "relier" = nouveau `reparent_node(slug, node_id, new_parent_id)`
— détache du parent actuel, rattache à la cible, refuse racine déplacée/
auto-parenté/cycle (BFS sur les descendants) plutôt que de corrompre
l'arbre silencieusement. Positions jamais persistées côté serveur → déplacer
un nœud sans le lâcher sur un autre est un repositionnement purement visuel,
local à la session ; seul un dépôt sur un autre nœud déclenche une vraie
mutation (`PATCH .../reparent`). Pattern de glisser repris de
`web/src/components/brand/bbox-editor.tsx` (mouse events + `useEffect`
scoping `window.addEventListener("mousemove"/"mouseup")`), pas pointer
events — précédent déjà établi dans le projet, contrairement à l'hypothèse
initiale du plan.
**Livré :**
- `services/rnd_hypothesis_tree.py::reparent_node()` — détache/rattache +
  `_recompute_depths()` (recalcule `depth` sur tout le sous-arbre déplacé).
- `PATCH /rnd/trees/{slug}/nodes/{node_id}/reparent` (`api/routers/rnd.py`).
- `web/src/lib/rnd-tree-api.ts::reparentRndNode()`.
- `web/src/app/rnd-v2/arbres-tab.tsx` — canvas SVG (nœuds = `div` absolus
  positionnés sur les coordonnées `x`/`y` déjà calculées par
  `build_tree_graph()`, arêtes = bézier), sélecteur d'arbre, lancement
  d'une nouvelle investigation (`startRndInvestigation`, message honnête
  "~3-8 min" repris tel quel du backend), panneau détail (hypothèse/statut/
  score/insight/findings/actions recommandées/rapport markdown) avec
  actions ▶ Explorer / + Ajouter une branche / ✂ Élaguer / ✓ Fusionner en
  dossier.
**Bug trouvé et corrigé en vérification live :** `HypothesisNode.evidence.
key_findings` était typé `string[]` dans `rnd-tree-api.ts` (jamais exercé
avant cette phase, l'ancien renderer SVG ne l'affichait pas) — en réalité
un tableau d'objets `{finding, confidence, source}` (même pipeline
`quick_research`/`deep_research.py` que `DeepResearchFinding`, déjà
correctement typé ailleurs dans `rnd.ts`). Le rendu direct de l'objet
provoquait un crash React plein écran ("Objects are not valid as a React
child") au premier clic sur un nœud possédant des findings. Corrigé : type
aligné sur la forme réelle + rendu `f.finding`/`f.confidence` (repris du
pattern déjà correct de `new-idea-modal.tsx`) ; ajout au passage du rendu
de `recommended_actions` (existait côté données, jamais affiché).
**Vérifié en live :** `ruff`/`tsc`/`eslint` propres. Backend redémarré
(rechargement à chaud n'avait pas pris le nouvel endpoint — même symptôme
récurrent que les phases précédentes) puis `reparent_node` testé par
`curl` direct sur l'arbre réel `recherche-r-d-diffusiongemma` (3 nœuds
enfants réels) : déplacement valide confirmé (parent/depth mis à jour),
rejet cycle confirmé (400, nœud replacé sous son propre enfant refusé),
rejet auto-parenté confirmé (400), rejet déplacement de la racine confirmé
(400) — puis structure ré-alignée exactement sur l'état d'origine, vérifié
par re-fetch. Onglet Arbres ouvert dans le navigateur sur ce même arbre :
canvas rendu correctement (4 nœuds réels, couleurs par statut, arêtes
courbes), clic sur le nœud racine → panneau détail affiche l'hypothèse et
l'insight réels sans erreur (post-correction du bug ci-dessus). Aucune
donnée de test créée (toutes les mutations de vérification ont été
inversées sur le même arbre réel).
**Non couvert :** vérification live du glisser-déposer "relier" directement
dans le navigateur (outil `browse` devenu instable/redémarrages répétés en
fin de session) — la mutation qu'il déclenche (`reparentRndNode` →
`PATCH .../reparent`) est la même déjà validée par `curl`, et la logique de
détection de cible (distance au point de dépôt) est un calcul client simple
sans dépendance serveur ; à confirmer visuellement à l'occasion d'un
prochain passage sur `/rnd-v2`. Lancement d'une nouvelle investigation
(`🌱 Investiguer`) non déclenché en vérification (opération LLM ~3-8 min,
dépendante de crédits OpenRouter déjà épuisés plusieurs fois cette
session) — le endpoint `POST /rnd/investigate` lui-même est pré-existant
et hors périmètre de cette phase.
**Statut :** ✅ Complete, 2026-07-31.

### Phase 27 — Redesign R&D v2 : Dossiers (vue table façon Notion)

**Objectif :** vue bibliothèque/table par dossier — Résumé/État/Dernière
MAJ/Score/Agents/Votes/Documents/Concurrence/Études/Prototype/Décision.
**Investigation :** `RndDossierOut` (score/verdict exclus — ils vivent sur
l'idée liée, pas le dossier), `RndDossierListItem` (utilisé par
`GET /rnd/dossiers`) n'incluent ni score/verdict d'idée, ni vote Conseil, ni
nombre de documents — les construire à la volée depuis le frontend aurait
demandé un N+1 (12 dossiers réels × plusieurs appels chacun). "Concurrence"
et "Études" du plan initial n'ont en réalité qu'une seule source de données
(la section `market` du dossier) — fusionnées en une colonne "Marché"
plutôt que de fabriquer deux valeurs distinctes à partir d'un seul texte.
**Décision :** nouveau read model backend `services/rnd_dossier_table.py::
build_dossier_table_rows()` (même famille que `services/rnd_pipeline.py`,
déjà établi pour ce genre de vue agrégée), exposé via
`GET /rnd/dossiers/table-view` (placé avant `GET /rnd/dossiers/{dossier_id}`
dans `api/routers/rnd.py` — sinon la route dynamique l'aurait masqué, comme
`/rnd/dossiers/slug/{slug}` déjà présent pour la même raison). "Votes"
provient d'une session Conseil (`session_kind` 'evaluation'/'strategic',
Phase 25) rattachée au même `idea_id`, close, avec vote majoritaire calculé
— honnêtement vide (`—`) pour les 12 dossiers réels actuels, aucun n'ayant
encore de session Conseil close. Clic "Ouvrir ↗" renvoie vers `/rd` (via
`ceoDossierHref`, déjà existant) plutôt que de porter toute l'UI d'édition
dossier (sections/comité/finance/deck) en v2 — hors périmètre "vue table"
de cette phase.
**Livré :**
- `services/rnd_dossier_table.py` — idées/documents/sessions comité
  batch-fetchés en un seul appel chacun puis indexés en Python (au lieu
  d'un appel par dossier), `repo.get_dossier(id)` restant appelé par
  dossier (agrège sections/committee_team/statut CEO — dupliquer cette
  logique juste pour gagner quelques secondes de plus aurait été hors
  périmètre).
- `GET /rnd/dossiers/table-view` (`api/routers/rnd.py`).
- `web/src/lib/rnd-dossier.ts::fetchRndDossierTableView` + types
  `RndDossierTableRow`/`RndDossierCouncilVote`.
- `web/src/app/rnd-v2/dossiers-tab.tsx` — table 10 colonnes + lien "Ouvrir",
  recherche texte + filtres statut dynamiques (calculés depuis les
  statuts réellement présents plutôt qu'une liste figée des 9 statuts
  possibles, la plupart absents des données réelles actuelles).
**Bugs trouvés et corrigés avant toute vérification live (auto-relecture) :**
(1) premier appel à `repo.get_dossier(item.id, refresh_stale_finance=False)`
— ce paramètre n'existe que sur `RndDossierAgent.get_dossier()` (couche
agent), pas sur `RndRepository.get_dossier()` (couche repository) —
`TypeError` immédiat, corrigé en retirant le paramètre (pas de refresh
finance nécessaire ici, la repository ne le fait de toute façon jamais).
(2) lors du passage en batch-fetch, `idea_row.get("verdict")` sur la ligne
brute Supabase — la colonne réelle est `agent_verdict` (vu dans
`RndRepository.row_to_api_idea`), pas `verdict` ; aurait rendu la colonne
Score toujours sans verdict silencieusement. Les deux corrigés avant tout
test navigateur.
**Vérifié en live :** `ruff`/`tsc`/`eslint` propres. `GET
/rnd/dossiers/table-view` testé par `curl` direct (200, 12 lignes réelles,
score/verdict/agents_count/documents_count/market_excerpt cohérents avec
les dossiers sources) avant même d'écrire le frontend. Version initiale
(un appel complet par dossier) mesurée à ~14.5s pour 12 dossiers ; passage
au batch-fetch → ~7.5s (mesuré par `curl` avant/après, division par ~2).
Onglet Dossiers ouvert dans le navigateur (attente généreuse ~18s) : 12
dossiers réels affichés, colonnes Score (`24/100 GO` etc.), Agents (`6`
pour NomadComply, `—` sinon), Marché (extraits réels de la section
`market`), Décision (`Pivot demandé` en ambre pour NomadComply — cohérent
avec son `ceo_status: pivot_requested` réel, vérifié par `curl`), lien
"Ouvrir ↗" pointant vers `/rd?dossier=subventia&view=ceo` (vérifié via
l'attribut `href`, cohérent avec `ceoDossierHref`). Filtres statut et
recherche texte fonctionnels. Aucune donnée de test créée (endpoint
lecture seule).
**Non couvert / limite connue :** à attente courte (~10-12s), le navigateur
affiche parfois un état vide transitoire ("0 dossiers") avant de se
stabiliser sur les 12 réels à ~18-20s — confirmé non lié au nouveau code
(`curl` direct contre le backend est fidèle et rapide à chaque essai, zéro
trace d'erreur dans les logs uvicorn pour ces appels) ; cohérent avec les
artefacts de rechargement à chaud Next.js déjà notés en Phase 22
(double-fetch React StrictMode en dev + compilation à la volée de la route
proxy `/api/hub/[...path]`). `dossiers-tab.tsx` ne distingue pas
explicitement erreur vs "aucun dossier" (même limite pré-existante que
`pipeline-tab.tsx`/`incubateur-tab.tsx` — cohérence entre onglets jugée
préférable à un correctif isolé ici, hors périmètre de cette phase).
**Statut :** ✅ Complete, 2026-07-31.

**Correctif (2026-07-31) — "Ouvrir" renvoyait vers l'ancienne page /rd :**
Emilie a signalé successivement (1) un blocage rate-limit à l'ouverture
(BUG-009, `BUGS.md`), (2) une fois corrigé, un pop-up "tout grisé, je ne
sais rien faire" (BUG-010 — texte de chargement ajouté à
`rnd-pitch-modal.tsx`, X confirmé fonctionnel), puis (3) verdict final :
"la page n'est pas bonne... il faut refaire". Plutôt qu'un nouveau
correctif ponctuel sur l'ancienne page, décision de couper la dépendance à
`/rd` entièrement : le bouton "Ouvrir" du tableau Dossiers rouvre
désormais `DossierDetailView` (Phase 23) — l'overlay déjà construit et
déjà rapide utilisé par Pipeline — au lieu de naviguer vers
`/rd?dossier=...&view=ceo`. `DossierDetailView` attend un objet `RndIdea`
(pas un dossier) : plutôt que de refaire un aller-retour réseau,
reconstruit directement depuis la ligne du tableau déjà chargée
(`rowToIdea()`), donc ouverture instantanée (score/verdict/sous-scores/
actions visibles immédiatement) pendant que seul le contenu détaillé des
sections continue de charger en arrière-plan.
**Nouveau backend :** `services/rnd_dossier_table.py::build_dossier_table_rows`
expose désormais aussi `idea_legacy_id` (nécessaire pour que
"Incuber"/"Supprimer" opèrent sur la bonne idée — ces actions ciblent
l'idée, pas le dossier), `market_score`/`feasibility_score`/`vision_score`
(sous-scores affichés dans l'en-tête de `DossierDetailView`) et
`incubator_stage` — tous déjà présents dans `ideas_by_id` (batch déjà
fetché pour score/verdict), donc **aucune requête Supabase supplémentaire**.
**Vérifié en live :** `ruff`/`tsc`/`eslint` propres. Endpoint re-testé par
`curl` : `idea_legacy_id`/sous-scores/`incubator_stage` cohérents avec les
données réelles. Onglet Dossiers ouvert dans le navigateur, clic sur
"Ouvrir" (Subventia) → overlay `DossierDetailView` visible immédiatement
avec score réel (24/100 GO), sous-scores (Marché 8/10, Tech 7/10, Business
9/10), boutons Garder/Incuber/Supprimer, pendant que la barre de pipeline
et les onglets de contenu (Résumé/Pitch/Marché & concurrence/Business/
Technique/Risques/Budget/Décision CEO) finissent de charger — capturé une
seconde fois quelques secondes plus tard avec tout le contenu réel affiché
(barre de pipeline 7 étapes, onglet Résumé avec le vrai texte du dossier).
Reste sur `/rnd-v2` tout du long (plus de saut vers l'ancienne page /rd).
`ceoDossierHref`/le lien `/rd` retirés de `dossiers-tab.tsx`. Aucune
donnée modifiée (pas de clic sur Incuber/Supprimer pendant la
vérification, pour ne pas altérer les données réelles).
**Statut :** ✅ Correctif appliqué, 2026-07-31.

**Correctif (suite, 2026-07-31) — "Ouvrir" rouvrait un dossier condensé, pas
le vrai espace de travail :** après le correctif précédent (couper la
dépendance à `/rd`), Emilie a testé le résultat et tranché : *"c'est pas du
tout la bonne chose... le dossier doit être beaucoup plus complet, il y en
avait déjà des faits normalement"*. Question posée pour clarifier le
périmètre exact ("toutes les vraies sections en entier" vs "le vrai espace
de travail complet finance/comité/deck/social/CEO") — réponse explicite :
**le vrai espace de travail complet**.
**Investigation (3 agents Explore + 1 agent Plan, plan complet approuvé en
mode plan) :** l'ancien système (`/rd`) a déjà TOUTES ces fonctionnalités,
chacune dans un composant autonome piloté par props
(`web/src/components/rnd/rnd-finance-panel.tsx`, `rnd-committee-panel.tsx`,
`rnd-deck-panel.tsx`, `rnd-visual-panel.tsx`, `rnd-social-panel.tsx`,
`rnd-ceo-panel.tsx`, `rnd-product-panel.tsx`, `rnd-pipeline-panel.tsx`),
déjà branchées sur de vraies actions (aucune n'importe
`rnd-pitch-modal.tsx`/`rnd-dossier-workspace.tsx` — réutilisables telles
quelles). Seule la UI Sections (édition markdown + valider/réviser/
régénérer) vivait en fonctions **privées** (`SectionPreview`/
`SectionStatusIcon`, non exportées) dans `rnd-dossier-workspace.tsx` —
encore utilisé en direct par l'ancienne page `/rd`, donc extraction requise
plutôt que duplication.
**Décision :** remplacer les 9 onglets "pitch" condensés de
`dossier-detail-view.tsx` (Phase 23, `buildApplePanels`) par 8 onglets fixes
donnant accès aux vrais panneaux : Sections · Comité · Deck · Visuels ·
Social · Dossier CEO · Fiche produit · Pipeline. Aucune réécriture de
logique/API — uniquement les brancher avec les props déjà disponibles
depuis `dossier: RndDossierDetail`. Reskin visuel de ces panneaux (encore en
shadcn/Tailwind, pas le système `C` inline du reste de `/rnd-v2`)
**volontairement différé** — cette combinaison (nouveau cadre + ces mêmes
panneaux) existe déjà en prod via `/rd?view=ceo|committee|...`, la demande
d'Emilie portait sur le fonctionnel ("plus complet"), pas le visuel.
**Livré (checkpoint A — extraction, zéro changement de comportement) :**
`web/src/components/rnd/rnd-section-preview.tsx` (nouveau, exporte
`SectionStatusIcon`/`SectionPreview`) + `rnd-dossier-sections-panel.tsx`
(nouveau, exporte `RndDossierSectionsPanel` — liste sections + journal +
preview) ; `rnd-dossier-workspace.tsx` refactoré pour consommer les deux au
lieu de ses définitions privées, comportement identique.
**Livré (checkpoint B — nouvelle architecture d'onglets + Sections/Comité) :**
`dossier-detail-view.tsx` : `buildApplePanels`/rendu markdown unique
supprimés, remplacés par un tableau `TABS` statique (8 entrées) + rendu par
condition sur `activeId`, avec deux modes d'habillage (wrapper borné pour
Sections/Comité qui gèrent leur propre scroll interne, wrapper
`overflow-y-auto` générique pour les 6 autres onglets — inverser les deux
casse l'UI). État `events` ajouté ; poll 5s/120s (déjà utilisé par
`rnd-dossier-workspace.tsx` pour rafraîchir pendant l'enrichissement en
arrière-plan) répliqué ici. Overlay agrandi (`max-w-[860px] max-h-[880px]`
→ `max-w-[1180px] max-h-[92vh]` — les panneaux ont été conçus pour un cadre
plus large). `PipelineStrip` (puces de statut dans l'en-tête) rendue
cliquable (`onNavigate`) avec `PIPELINE_TAB_MAP = {pitch: "sections"}` pour
faire correspondre les 6 valeurs `tab` connues du backend
(`services/rnd_pipeline.py::STAGE_DEFS`) aux 8 nouveaux onglets. Les 6
onglets pas encore branchés (Deck/Visuels/Social/CEO/Produit/Pipeline)
affichent un placeholder "à venir" temporaire (diff lisible, prochains
checkpoints).
**Vérifié en live :** `ruff`/`tsc`/`eslint` propres après chaque étape.
Clic-test sur `/rd?tab=dossiers` (sélection d'un vrai dossier, `Subventia`)
confirmant zéro régression du panneau Sections extrait (liste des 10
sections, journal, preview/édition identiques à avant). Sur `/rnd-v2` →
Dossiers → "Ouvrir" : les 8 onglets s'affichent, onglet Sections montre le
panneau Finance réel (VIABLE, grille tarifaire, ROI) + les 10 vraies
sections + le journal + la preview éditable — texte identique à celui vérifié
sur `/rd`. Onglet Comité testé : panneau réel avec équipe (Alex/Spec/Maya/
Compta/Dev App/Content), a effectivement démarré une vraie session comité
avec un message LLM réel d'Alex (comportement hérité de
`RndCommitteePanel`, pas une régression — c'est le même comportement que
l'ancien système). **Nettoyage effectué :** les 2 sessions de test créées
(doublées par le mode strict de React en dev, comme observé ailleurs cette
session) + leurs messages supprimés directement en base, et le statut du
dossier `subventia` (passé à `committee_active` par la création de
session) restauré à `draft` — aucune trace de test laissée.
**Non couvert (checkpoint suivant) :** onglets Deck/Visuels/Social/CEO/
Produit/Pipeline (placeholders pour l'instant) ; reskin visuel des panneaux
réutilisés (différé, voir Décision ci-dessus).

**Livré (checkpoints C+D — Deck/Visuels/Social/CEO/Produit/Pipeline +
`onNavigateTab`) :** les 6 onglets restants branchés dans la même passe
(mécaniquement identique à B — composant existant + props déjà disponibles
depuis `dossier`) : `RndDeckPanel`, `RndVisualPanel`, `RndSocialPanel`,
`RndCeoPanel`, `RndProductPanel`, `RndPipelinePanel`. `PipelineStrip`
(en-tête) rendue cliquable via `onNavigate` ; `handleNavigateTab` mappe les
6 valeurs `tab` connues du backend vers les 8 onglets
(`PIPELINE_TAB_MAP = {pitch: "sections"}`, le reste 1:1).
**Vérifié en live (les 8 onglets, un vrai dossier `subventia`) :**
`ruff`/`tsc`/`eslint` propres. Deck → contenu réel + bouton "Générer le
deck pitch" + état honnête "Enrichissez le dossier... avant la première
génération" (aucun deck existant). Visuels → texte réel "hero, mockup,
moodboard et graphiques finance" + bouton génération. Social → état
verrouillé honnête ("Disponible après validation CEO du dossier — Statut
actuel : draft · CEO : pending", cohérent : aucun dossier réel n'est encore
`ceo_status=approved`). Dossier CEO → contenu réel ("Package exécutif pour
Subventia..."). Fiche produit → état verrouillé honnête ("Fiche produit
verrouillée — validation CEO requise"). Pipeline → suivi réel 7 phases
(1/7 · 14%, boutons "Ouvrir" par phase, phases 5/7 verrouillées) —
identique à ce qui était déjà vérifié sur l'ancienne page `/rd`. Navigation
`onNavigateTab` confirmée fonctionnelle : depuis l'onglet Deck, clic sur la
puce d'en-tête "Visuels & deck" → bascule effective vers l'onglet Visuels.
Aucune erreur console propre au nouveau code sur les 8 onglets (seuls des
avertissements Recharts bénins "width(-1)" lors des transitions d'onglet,
et des 500 transitoires isolés confirmés sans rapport — même requête
`product/status` retestée immédiatement après en isolant le réseau : 200
propre both times). Aucune donnée de test créée par ces 6 panneaux (aucun
n'a de `useEffect` mutant au montage, contrairement à `RndCommitteePanel` —
confirmé par lecture directe du code avant de tester).
**Non couvert :** clic direct sur un bouton "Ouvrir" *à l'intérieur* de
l'onglet Pipeline (par opposition aux puces de l'en-tête, elles,
confirmées) — non vérifié interactivement (ambiguïté DOM avec les boutons
"Ouvrir" du tableau Dossiers sous-jacent, non résolue avec l'outil de test
disponible) ; la logique est cependant strictement la même fonction
`handleNavigateTab` déjà validée via les puces d'en-tête, et
`RndPipelinePanel` lui-même n'a pas été modifié (contrat `onNavigateTab`
préexistant, inchangé). Reskin visuel des 8 panneaux toujours différé
(Décision ci-dessus) — périmètre assumé, pas une lacune.
**Statut :** ✅ Correctif complet (checkpoints A-E), 2026-07-31.

### Phase 28 — Redesign R&D v2 : Explorer (veille externe)
**Objectif :** onglet Explorer sur `/rnd-v2` — signaux externes réels
(HN / Reddit / GitHub) + brief labo (Idris), sans inventer de métriques
si les sources sont down. Pipeline dossier / comité / dispatch inchangés.
**Livré Vague E (2026-08-10) :**
- `services/rnd_explorer.py` — scan + brief R&D (pas angles marketing Camille)
- Router `rnd_explorer` : `GET /rnd/explorer/signals`, `POST /rnd/explorer/brief`
- UI `explorer-tab.tsx` — topics, scan, brief, seed → Pipeline
- Tests `test_rnd_explorer.py`
**Statut :** ✅ Complete (Vague E), 2026-08-10.

### Phase 29 — Marketing/Finances : Command Center visuel
**Objectif :** transformer `/marketing` et `/finances` en cockpits immersifs
("Marketing Command Center" / "ALNUA Finance Center" du brief Emilie) —
sortir ces deux départements du `ConsoleShell` standard pour rejoindre le
chrome plein écran déjà réservé à App/Gaming/Robo/R&D-v2 (`hub-shell.tsx`),
et refondre leurs pages sur le modèle de coquille déjà établi 4 fois
(`rnd-v2/page.tsx` / `gaming-v2/page.tsx` — header/sidebar/onglets/command-bar)
plutôt que le `DepartmentWorkspace` générique actuellement monté
(`marketing/page.tsx`, `finances/page.tsx`). **Correction (2026-07-31) :** la
première rédaction de cette phase référençait `rnd-dossier-workspace.tsx`
comme modèle — vérifié en conception détaillée que ce fichier est en
réalité la vue détail d'un seul dossier R&D (page `/rd`), pas un pattern de
coquille de département ; la bonne référence est le pattern `-v2` ci-dessus.
**Contrainte :** aucune nouvelle table nécessaire pour cette phase — les
données existent déjà (`transactions`, `financial_summaries`, `posts_queue`,
leaderboard `services/competition.py`, `services/cost_monitor.py`) ; c'est
une phase quasi exclusivement frontend, dans l'esprit de la Phase 22
(R&D v2 socle) plutôt que Gaming/Robo Phases 15-20 (qui avaient dû créer de
vraies tables).
**Livré :**
- `web/src/lib/routes.ts` — `ROUTES.marketingV2`/`ROUTES.financesV2`
  (coexistence avec `/marketing`/`/finances`, même pattern que `rndV2`).
- `web/src/components/layout/hub-shell.tsx` — `isMarketingV2`/`isFinancesV2`
  ajoutés au chrome immersif.
- `web/src/app/app-v2/shared.tsx` — nouveau `KpiTile` (tuile chiffre
  réutilisable, 2e usage concret après le `Tile` local de
  `gaming-v2/analytics-tab.tsx` → seuil d'extraction atteint).
- `web/src/app/app-v2/team.tsx` — `INSTRUCTION_HANDLERS.marketing` ajouté
  (`marketingInstruction`, endpoint réel `/agents/marketing/instruction`) ;
  Camille devient le 2e agent (après Théo/dev_app) avec un vrai canal chat.
- `web/src/lib/marketing-api.ts` (nouveau) — `fetchLeaderboard()`, seul
  client API réellement nouveau (aucun nouvel endpoint backend).
- `web/src/app/finances-v2/` — coquille (`page.tsx`, pattern `rnd-v2`) +
  3 onglets neufs (`vue-globale-tab.tsx` : 4 `KpiTile` + résumé IA +
  graphiques Recharts, tous sur données réelles `fetchFinanceDashboard` ;
  `transactions-tab.tsx` : liste/filtre/récurrentes ; `couts-tab.tsx` :
  `ApiCostsCard`). `FinancesAccountingPanel`/`FinancesControllerPanel`/
  `FinancesTransactionModal` embarqués **tels quels** (verbatim, aucune
  réécriture) dans des panneaux `<details>` repliables + la modale
  partagée avec l'action câblée "＋ Nouvelle transaction" de la command bar.
- `web/src/app/marketing-v2/` — même coquille + 3 onglets (`vue-globale-tab.tsx` :
  KpiTile sur `computePostStats`/leaderboard filtré sur les 7 agents du
  bureau/dépenses `category=marketing` réelles, répartition plateforme/secteur
  en `Bar` ; `content-tab.tsx` : lecture seule `posts_queue` groupée par
  statut). Roster Équipe horizontal (7 agents réels, pattern `gaming-v2`) +
  panneau activité temps réel. `MarketingConsole` embarquée telle quelle
  dans un `<details>` + action câblée "＋ Instruction Marketing" (drawer COO
  pré-rempli, pattern `requestNewAgent` de `rnd-v2`).
- Correction du texte de cette phase (référençait à tort
  `rnd-dossier-workspace.tsx`, en réalité la vue détail d'un seul dossier
  R&D — pas un pattern de coquille de département).
**Bug pré-existant trouvé et corrigé (2026-07-31) :** `FinancesTransactionList`
(`web/src/components/finances/finances-transaction-list.tsx`) construisait
sa liste d'options de catégorie pour le filtre "Tout" en concaténant
`categoriesForType("expense")` + `categoriesForType("income")` — les deux
incluent `"autre"`, donc deux `<SelectItem key="autre">` avec la même clé
React dès que `typeFilter === "all"` (le défaut, y compris sur `/finances`
legacy — bug déjà présent avant cette phase, simplement jamais exercé en
observant la console). Corrigé par dédoublonnage (`new Set(...)`) ; bénéficie
aussi à `/finances`.
**Vérifié en live (navigateur réel, `browse`) :** `/marketing-v2` et
`/finances-v2` ouverts en URL directe — chrome plein écran confirmé (aucune
fuite de sidebar/topbar Hub) ; Équipe : 2 agents réels sur Finances (Jules,
Rémi), 7 sur Marketing (Camille, Sofia, Esmée, Kael, Mira + 2 via scroll) ;
Vue globale Finances : 4 tuiles réelles (0,00 € partout, cohérent avec
aucune transaction ce mois), résumé IA généré affiché, graphiques rendus ;
Vue globale Marketing : tuiles réelles dont **Score équipe = 440** (valeur
réelle confirmée identique à `data/agent_scores.json`), répartition
plateforme/secteur honnêtement vide (aucun post) ; Transactions : état vide
honnête + modale "Ajouter une transaction" ouverte et fonctionnelle (vraie
liste de projets) ; Contenu : "0 posts" honnête. Aucune erreur console
bloquante sur les deux pages. `tsc --noEmit` et `next lint` propres sur tous
les fichiers touchés (3 erreurs lint pré-existantes, fichiers non touchés
par cette phase, laissées en l'état).
**Non couvert :** ouverture effective des panneaux `<details>` repliables
(Jules/Rémi, Console Marketing) non capturée en screenshot — l'outil
`browse` est devenu instable en fin de session (redémarrages répétés,
même symptôme déjà documenté en Phase 26) ; risque jugé faible, ces
panneaux réutilisent des composants (`FinancesAccountingPanel`,
`FinancesControllerPanel`, `MarketingConsole`) déjà éprouvés sur les pages
legacy, aucune logique nouvelle dans le `<details>` lui-même (toggle natif
HTML). Deux avertissements console pré-existants et hors scope repérés en
testant (non corrigés, communs à tout `Dialog`/`FinancesTransactionModal`
de l'app, pas spécifiques à cette phase) : ref non transmis sur
`DialogOverlay` (`components/ui/dialog.tsx`) et `DialogContent` sans
description accessible. Bascule `/marketing`→`-v2`/`/finances`→`-v2` en
alias et ajout à la nav principale : hors scope, pattern R&D (cutover final
dans une phase ultérieure).
**Statut :** ✅ Complete, 2026-07-31.

**Correctif (2026-07-31/08-01) — Redesign visuel Vue Globale Marketing/Finance :**
Emilie a partagé une maquette de référence beaucoup plus dense visuellement
(sparklines, donut avec label central, calendrier, tableaux) et signalé que
le premier rendu était trop minimal. Validé explicitement avec elle : design
premium au niveau de la maquette, **jamais de métrique fabriquée** — pour
toute donnée sans source réelle, un état honnête plutôt qu'un chiffre
inventé.
**Découvertes qui ont contraint le design :** `projects.branch` n'a que 4
valeurs (`app/gaming/robotics/other`) — pas de "département" au sens des 9-10
pôles, panneau rebaptisé "Dépenses par branche produit". `GET
/analytics/summary` (sans `project_id`) fait une vraie somme multi-projets
pour le MRR (fiable pour la tuile KPI) ; `GET /analytics/revenue` fait un
`max()` par mois, pas une somme — non utilisé pour la sparkline MRR (aurait
été incohérent avec la tuile). Aucun historique temporel réel côté
Marketing → sparklines = ligne plate honnête (`flatTrend`, précédent déjà
établi dans `web/src/lib/console/rich-data.ts:58-62`). `dashboard.
recurring_expenses` n'est pas filtré par `type` côté backend (peut contenir
des revenus récurrents) — filtré côté client. `controller_agent.
build_forecast` est une génération LLM à la demande, pas un calcul passif —
reste dans le panneau `<details>` Contrôleur, pas remonté en Vue Globale.
**Livré :**
- `web/src/app/app-v2/shared.tsx::KpiTile` — props `trend`/`trendColor`
  (sparkline `Sparkline` de `console/charts.tsx`, déjà existant). Fix au
  passage de la collision d'id de gradient SVG (`console/charts.tsx`,
  nouveau param `idSeed`) — devenue réelle avec 6+ sparklines sur une même
  page.
- Finance Vue Globale : 6 tuiles KPI (Revenus/Dépenses/Résultat net/Burn
  rate moyen/Solde cumulé YTD/MRR — sparklines réelles sur `last_6_months`
  sauf MRR en `flatTrend` ou "Non renseigné" si `null`). `finances-charts.tsx`
  scindé en `FinancesEvolutionChart` (LineChart 3 séries, chrome cockpit) et
  `FinancesExpenseDonut` (`Donut` de `console/charts.tsx` + légende manuelle,
  remplace le `PieChart` recharts) — `FinancesCharts` (composition des deux)
  conservé tel quel pour ne pas casser `/finances` legacy qui l'importe
  encore. 3 nouveaux panneaux réels : `finances-upcoming-panel.tsx`
  ("Prochaines échéances (estimation)", dérivé des transactions récurrentes
  via le nouveau `web/src/lib/finances-recurring.ts`), `finances-recurring-
  preview-panel.tsx` ("Coûts récurrents", pas "Abonnements SaaS actifs" —
  aucun champ de renouvellement en base), `finances-branch-breakdown-panel.tsx`
  ("Dépenses par branche produit", bucket "Sans projet" jamais masqué).
- Marketing Vue Globale : sparklines honnêtes (`flatTrend`) sur les 5 tuiles
  existantes. 2 nouveaux panneaux réels : `campaigns-preview-panel.tsx`
  ("Campagnes actives", top 5 réelles Phase 33, CTA vers l'onglet Campagnes)
  et `today-content-panel.tsx` ("Aujourd'hui", `fetchCalendar` déjà existant
  mais jamais monté sur `/marketing-v2`). Labels/couleurs de campagnes
  extraits de `campagnes-tab.tsx` vers `web/src/components/marketing/
  campaign.constants.ts` (partagés avec le nouveau panneau).
**Hors scope (rappel) :** Runway (fausse précision sans vraie trésorerie
bancaire), Investissements (aucune donnée), Reach/ROI global/entonnoir de
conversion/performances par canal Marketing (aucune source réelle),
nouveaux onglets Social Media/SEO/Ads/Analytics/Automatisation/Brand Center
et Budgets/Prévisions/Facturation/Fiscalité/Salaires/Investissements comme
onglets dédiés — phases futures.
**Vérifié en live :** `tsc --noEmit`/`eslint` propres (mêmes 3 erreurs
pré-existantes hors scope). Navigateur réel (`browse`) : `/finances-v2` Vue
globale — 6 tuiles avec sparklines réelles, MRR "Non renseigné" (honnête,
aucune donnée `/analytics` en base), Évolution financière en LineChart,
donut avec état vide honnête, 3 nouveaux panneaux tous honnêtes (aucune
dépense/récurrence ce mois dans les données de test actuelles).
`/marketing-v2` Vue globale — 5 tuiles avec sparklines plates honnêtes,
répartition plateforme cohérente avec un post de test réel existant,
panneaux Campagnes actives et Aujourd'hui avec états vides honnêtes. Aucune
métrique affichée qui n'existe pas réellement en base sur les deux pages.
**Non couvert :** clic sur le CTA "Voir toutes →" (Campagnes actives → onglet
Campagnes) non capturé en screenshot — outil `browse` redevenu instable en
fin de session (même symptôme récurrent que Phases 26/33) ; risque jugé nul,
c'est un simple `setTab("Campagnes")` déjà identique au clic direct sur
l'onglet, vérifié à de nombreuses reprises dans cette même session.
**Statut :** ✅ Correctif appliqué, 2026-08-01.

### Phase 30 — Workflow engine généralisé + niveaux d'autonomie
**Objectif :** étendre `services/workflow_engine.py` (recettes/étapes déjà
existantes pour ops/ship/watchdog) pour porter des recettes de validation
métier (`content_validation`, `campaign_validation`, `budget_transfer`),
avec un niveau d'autonomie configurable (0-3, cf. brief Emilie) par
type de tâche/département déterminant combien d'étapes s'auto-valident.
`services/event_bus.py` (déjà présent) émet à chaque transition d'étape.
**Décision d'architecture :** un seul moteur générique — voir `DECISIONS.md`
DEC-012 (pas de second moteur de workflow).
**Dépendances :** aucune côté code existant ; conditionne les Phases 31-32.
**Statut :** ✅ Complete (DEC-032 Vague 2, 2026-08-12) — recettes validation +
autonomie ; CEO `/ceo` A_VERIFIER ; Direction `/hub` panneau Company OS (ops /
ship / historique + lien file CEO). `budget_transfer` **hors scope**.

### Phase 31 — Agent Trust System
**Objectif :** indice de confiance par agent, alimenté par l'historique réel
des validations (verdicts Review Board, corrections du premier coup) —
pondéré/décroissant, pas cumulatif. Nouveau service `services/agent_trust.py`
+ table dédiée, endpoint + jauge frontend (réutilisable dans
`model-settings-view.tsx`).
**Décision d'architecture :** strictement séparé de `services/competition.py`
(scoring cumulatif de gamification) — voir `DECISIONS.md` DEC-011.
**Dépendances :** Phase 30 (le trust score se calcule à partir de
l'historique des workflows de validation — sans Phase 30, pas de données à
mesurer).
**Statut :** ✅ Complete (DEC-032, 2026-08-12) — MVP accepté : JSON
`data/agent_trust.json` + `GET /agents/trust` + jauge `/trust` (Vague 1).
Enrichissements historiques optionnels hors tampon 100 %.

### Phase 32 — Review Board générique + Quality Gates
**Objectif :** généraliser `agents/rnd_council_agent.py` (aujourd'hui scopé
Comité R&D) en reviewers configurables par recipe — voir `DECISIONS.md`
DEC-013. Généraliser `services/academy_gate.py` (seuils pondérés →
`gate_open`) en `config/quality_gates.py` avec seuils par département (ex.
Brand ≥ 90 %, Marketing ≥ 85 %, SEO ≥ 80 %), consommés comme condition de
passage par le workflow engine (Phase 30).
**Dépendances :** Phase 30 (les gates bloquent une transition d'étape du
workflow engine) et Phase 31 (un score sous le seuil doit pouvoir peser sur
le trust de l'agent producteur).
**Statut :** ✅ Complete (DEC-032, 2026-08-12) — `config/quality_gates.py` +
`services/review_board.py` + `POST /review-board/evaluate` ; débat LLM optionnel
(`REVIEW_BOARD_LLM`, défaut off). UI mini Review Board sur `/trust`.

### Phase 33 — Marketing Command Center — profondeur (Campagnes + Content Studio)
**Objectif :** livrer deux fonctionnalités précises du brief Emilie —
gestion de Campagnes (budget, statut, dépenses réelles) et Content Studio
(production de contenu par statut, glisser-déposer). Emilie a explicitement
choisi Marketing avant Finance et validé ce MVP maintenant plutôt que
d'attendre Phase 30 (workflow engine) — écart assumé, voir ci-dessous.
**Écart assumé avec la version précédente de cette entrée :** pas de
brancher sur un moteur de workflow générique (Phase 30 toujours
`⏸️ Not started`) — le CRUD Campagnes et les transitions de statut Content
Studio sont directs (`PATCH` immédiat, pas d'étape de validation). À
reprendre si/quand la Phase 30 est livrée. Pas de router `/marketing` dédié
non plus (hors scope de cette itération) ; un nouveau router `/campaigns`
a été créé à la place (voir Livré).
**Règle absolue respectée :** `campaign_roi_report` (ROI/reach/impressions,
`skills/skill_ads.py`) reste un stub explicite retournant des zéros — jamais
exposé côté API ni affiché dans le cockpit. Le seul "dépensé" réel affiché
est calculé en sommant les vraies `transactions` liées à une campagne
(`transactions.campaign_id`, nouvelle colonne).
**Livré :**
- Migration `supabase/migrations/20260731120000_marketing_campaigns.sql`
  (poussée en prod via `supabase db push --linked`) — table `campaigns`
  (objective/platform alignés sur `skills/skill_ads.py::OBJECTIVES`/
  `VALID_PLATFORMS`), `transactions.campaign_id` (nullable FK), RLS
  identique au pattern déjà établi. Reflet dans `database/schema.sql`.
- **Bug pré-existant corrigé au passage :** `posts_queue.content_type` CHECK
  n'incluait pas `"lore"` alors que le type TS le déclare depuis la Phase 26
  — un `POST /posts` avec `content_type: "lore"` échouait en base. Le nom
  réel de la contrainte n'a pas pu être vérifié à l'avance (aucun accès
  direct à la base dans cet environnement — ni MCP Supabase, connecté à une
  autre organisation, ni `psql`, ni Docker pour `supabase db dump`) : la
  migration la retrouve dynamiquement via `pg_constraint` plutôt que de
  supposer son nom.
- `agents/ads_agent.py::AdsAgent.create_campaign` persiste désormais
  réellement une ligne `campaigns` (avant cette phase : dict volatile,
  aucune campagne n'existait après l'appel).
- `api/routers/campaigns.py` (nouveau, monté dans `api/routers/__init__.py`)
  — `GET/POST /campaigns`, `PATCH/DELETE /campaigns/{id}`, `spent_usd`
  calculé à la volée par agrégation des transactions liées.
  `POST /agents/ads/create-campaign` (`agents_pole.py`) — création
  LLM-assistée par Léo (2 variantes créatives A/B), persiste via le même
  chemin. `FinanceTransactionCreate`/`Update` acceptent désormais
  `campaign_id` (`api/routers/finances.py`).
- `web/src/lib/marketing-api.ts` (`Campaign`, `fetchCampaigns`,
  `createCampaign`, `updateCampaign`, `deleteCampaign`) et
  `web/src/lib/pole-api.ts` (`adsCreateCampaign`).
- `web/src/app/marketing-v2/campagnes-tab.tsx` + `web/src/components/
  marketing/campaign-modal.tsx` (calqué sur `finances-transaction-modal.tsx`)
  — grille de cartes, budget alloué vs dépensé réel (barre `Bar`), création
  manuelle. `marketing-console.tsx` — 4e formulaire "Léo — créer une
  campagne (brief)".
- **Content Studio** remplace l'ancien onglet "Contenu" (lecture seule,
  supprimé) : `web/src/components/content/content-kanban.tsx` (calqué sur
  `roadmap-kanban.tsx`, `@hello-pangea/dnd`), `content-card.tsx`,
  `content-studio-create-modal.tsx` (nouveau — pas une réutilisation de
  `post-composer.tsx`, incompatible avec un "+" par colonne). 4 colonnes
  draggables (`draft/pending_approval/approved/published`) ; `rejected`/
  `failed` en lecture seule dans un panneau replié séparé (évite de casser
  `published_at`/`computePostStats` si un post est glissé directement vers
  "Publié" sans passer par le vrai publisher bot). `CONTENT_STUDIO_COLUMNS`/
  `POST_STATUS_LABELS`/`CreatablePostStatus` ajoutés à `content.constants.ts`.
- `marketing-v2/page.tsx` — `TABS` devient Équipe/Vue globale/Content
  Studio/Campagnes (4 onglets).
**Difficulté rencontrée en vérifiant :** le serveur backend réellement
utilisé par le proxy Next.js (`data/hub_active_port.txt` → port **8003**,
lancé avec des flags spécifiques `--limit-concurrency 40
--timeout-keep-alive 5`) est différent du process que j'avais lancé
manuellement pour tester (`--port 8000`, orphelin) — mes premiers tests
`curl` réussissaient contre le mauvais process, laissant `/campaigns` en
404 côté navigateur (`/api/hub/campaigns`) alors que le "vrai" backend
tournait toujours sur l'ancien code. Corrigé en redémarrant le process sur
8003 avec les mêmes flags.
**Vérifié en live :**
- Backend direct (`curl`, port 8003) : `POST /campaigns` (création
  manuelle), `POST /agents/ads/create-campaign` (Léo, brief réel → 2
  variantes + campagne persistée), transaction réelle liée via
  `campaign_id` → `GET /campaigns` renvoie `spent_usd` correct (42.5€ sur
  une dépense de 42.5€), `POST /posts` avec `content_type: "lore"` accepté
  (confirmerait l'échec avant la migration). Données de test nettoyées
  (campagnes, transaction) ; le post de test n'a pas pu être supprimé
  (aucun endpoint `DELETE /posts/{id}` n'existe) — marqué `rejected` à la
  place, visible honnêtement dans le panneau lecture-seule du Content
  Studio.
- Navigateur réel (`browse`) : `/marketing-v2` → onglet Campagnes, création
  manuelle bout en bout via l'UI (formulaire rempli → carte réelle apparue
  avec statut/budget/barre corrects) ; onglet Content Studio, 4 colonnes
  réelles (0 partout, cohérent), panneau "Rejetés / échoués (lecture
  seule — 1)" affichant correctement le post de test marqué `rejected`.
  Aucune erreur console bloquante sur les deux onglets (mêmes avertissements
  `Dialog`/`aria-describedby` pré-existants déjà documentés Phase 29, hors
  scope).
**Non couvert :** création de post via le "+" du Content Studio (modale
`content-studio-create-modal.tsx`) non capturée en direct dans le
navigateur — outil `browse` devenu instable en fin de session (redémarrages
répétés, même symptôme déjà documenté Phase 26) ; risque jugé faible,
`createPost()` est une fonction déjà éprouvée en production (utilisée par
`post-composer.tsx`) et la modale réutilise les mêmes primitives Select/
Input/Textarea que `CampaignModal`, déjà validée en direct. Glisser-déposer
du Kanban non testé en direct pour la même raison (logique client simple,
`onStatusChange` → `updatePost`, déjà utilisée ailleurs). `tsc`/`eslint`
(web/) et `ruff` (backend, scope complet du fichier CLAUDE.md) propres,
zéro nouvelle erreur introduite. `/marketing` (legacy) et route API dédiée
`/marketing/*` : hors scope, `/campaigns` créé séparément à la place.
**Statut :** ✅ Complete, 2026-07-31.

### Phase 34 — Finance Cockpit — profondeur
**Objectif :** nouvelles tables `budgets` (allocation par département — au-
jourd'hui seule `transactions` existe, sans notion d'allocation), `invoices`,
`fiscal_obligations`. Exposer `controller_agent.build_forecast` (déjà codé,
jamais exposé en cockpit). Transfert de budget entre départements validé via
le workflow engine de la Phase 30 (ex. Marketing→App validé par Aria).
**Avancée 2026-08-09 (DEC-016) :** ledger factures JSON + API
(`/finances/invoices`) sans paiement auto ; agrégateur SaaS spend live
(`/finances/saas-spend`) ; connecteur Revolut lecture seule
(`/finances/revolut/status`).
**Vague 3 (2026-08-09) :** ledgers JSON `budgets` + `fiscal_obligations` + API
(`/finances/budgets`, `/finances/fiscal-obligations`) + onglet cockpit
« Budgets & Fiscal ». `budget_transfer` workflow **reporté** (pas stubbé).
**Vague C (2026-08-10) :**
- `GET /finances/cockpit-forecast` — projection déterministe (budgets + fiscal + SaaS)
- `POST /finances/forecast/llm` — Rémi prérempli depuis le cockpit
- UI : résumé, kind/due_date fiscal, dépensé éditable, panneau forecast
**Polish UI (2026-08-10) :** vue globale KPI brand + txs récentes + charts.
Migration Supabase tables optionnelle plus tard — le JSON reste le chemin quotidien.
**Dépendances :** Phase 29 (cockpit) et Phase 30 (transferts — reportés).
**Avancée profondeur 2026-08-10 :** `spent` overlay (computed + manual),
`GET /finances/budget-alerts` (warning ≥80% / critical ≥100% + event_bus),
factures due_date/filtres/overdue, fiscal auto-promote `upcoming→due`.
**Statut :** ✅ Complete sans `budget_transfer` (DEC-032, 2026-08-12) —
alerts / invoices / fiscal / forecast / SaaS ledger. Transfert auto entre
départements = hors scope définitif pour le tampon 100 % Hub (DEC-016).

### Phase 35 — Brand Design transversal
**Objectif :** étendre `agents/brand_agent.py` (aujourd'hui pipeline
image/kit uniquement — analyse + génération de formats) vers un vrai design
system (tokens couleur/typo, guidelines de ton), en fusionnant avec
l'embryon existant `content_company_agent.brand_voice_guide()` plutôt que
de le dupliquer. Rendre Brand reviewer transversal dans les recipes de
contenu de tous les départements (`config/agent_personas.py` à étendre pour
un agent multi-room).
**Dépendances :** Phase 32 (Brand devient un des reviewers du Review Board
générique).
**Livré Vague D (2026-08-10) :**
- `services/brand_design_system.py` — tokens Hub/kit + `BRAND_VOICE_GUIDE`
- `config/review_board_recipes.py` — siège `brand` / `content_company`
- `GET /brand/design-system`, `POST /brand/review` (`brand_system` router)
- Marketing Brand Center réel (plus ComingSoon)
- Hors scope Vague D : persona multi-room Brand, débat LLM, split `brand-view`
**Avancée profondeur 2026-08-11 (Vague C) :** débat LLM Élise↔Anouk
(`services/brand_voice_debate.py`, `POST /brand/debate`, Brand Center UI) ;
Review Board LLM route brand seats vers ce débat ; split `brand-view`
(`use-brand-kit-workflow` + `brand-kit-workspace`).
**Statut :** ✅ Depth+ Complete (débat + split ; design system transversal live).

### Phase 36 — Orchestration inter-départements
**Objectif :** le scénario "validation d'un projet APP → Marketing crée le
plan de lancement, Comptabilité génère le budget prévisionnel, Analytics
prépare les KPIs" du brief Emilie — `services/event_bus.py` a déjà le
mécanisme exact (pub/sub, handlers déjà câblés pour d'autres événements) ;
émettre `project_validated` et câbler des handlers par département. Étendre
`services/daily_briefing.py` pour une synthèse cross-département.
**Dépendances :** Phases 33/34 (les départements doivent avoir une logique
métier réelle à déclencher, pas juste un cockpit d'affichage).
**Statut :** ✅ Depth+ Complete (2026-08-12) — handlers `project_validated` /
`content_validated` / `campaign_validated` → file `data/cross_dept_queue.json` ;
`GET /cross-dept/queue` ; `POST /cross-dept/emit-project` + `POST /cross-dept/drain`
(brouillons Camille/Rémi/Layla ou checklists honnêtes, artifacts JSON) ; UI
`/trust` ; briefing COO (`queued` + `recent_done`). `CROSS_DEPT_DRAIN_LLM=0`
pour squelettes sans LLM.

### Phase 37 — Marketing Command Center : mesure de performance réelle (Reach/Engagement/ROI/Funnel)
**Contexte :** Phase 33/29 avaient explicitement exclu Performances par
canal, Top contenus (avec reach%) et Entonnoir de conversion de la Vue
Globale Marketing faute de source de donnée — traité comme une fin de
non-recevoir. Emilie a demandé explicitement qu'on crée les champs/flux
manquants plutôt que d'attendre qu'ils existent : "si les fonctions
n'existent pas on va les créer."

**Décision de conception :** saisie manuelle réelle (copiée depuis les
dashboards natifs des plateformes/produits) plutôt qu'intégration API
Meta/TikTok/Google/LinkedIn Ads — cette dernière est un chantier séparé
(OAuth apps, vérification business, quotas, multi-semaines par plateforme)
non lancé ici. Toujours zéro métrique fabriquée : tous les nouveaux champs
sont `NULL`/absents tant que personne n'a saisi de vraie valeur, jamais un
0 ou une estimation par défaut.

**Livré :**
- `20260731130000_marketing_performance_tracking.sql` — `campaigns` gagne
  `reach`/`engagements`/`conversions`/`revenue_generated_usd`/
  `stats_updated_at` (saisie manuelle, via `CampaignModal` → section
  "Statistiques") ; `posts_queue` gagne `reach`/`engagement_count`/
  `stats_updated_at` (saisie manuelle post-publication, via
  `PostEditModal`) ; nouvelle table `funnel_snapshots` (saisie mensuelle
  par produit : Visiteurs → Intéressés → Engagés → Abonnés → Clients,
  `source_note` documente d'où vient le chiffre — App Store Connect / Play
  Console / Plausible / GA4 / signups Supabase).
- `GET /campaigns/performance-by-platform` — agrège reach/engagements/
  conversions/spent/ROI réels par plateforme ad (meta/google/tiktok),
  uniquement sur les campagnes où une stat a été saisie ; `sample_size`
  expose combien de campagnes sont comptées (jamais présenté comme une
  couverture complète du canal). ROI (`roi_pct`) calculé côté backend
  uniquement si `revenue_generated_usd` est saisi ET `spent_usd` > 0.
- `POST/GET /marketing/funnel`, `GET /marketing/funnel/latest` — upsert
  mensuel par `(project_id, period_month)`.
- Frontend : `PerformanceByPlatformPanel`, `TopContentPanel` (classe les
  posts publiés par reach réel, sans % de reach — aucune audience totale
  connue par plateforme pour calculer un taux honnête), `ConversionFunnelPanel`
  + `FunnelEntryModal` (vrai entonnoir avec taux de conversion inter-étapes
  calculés à partir des chiffres saisis, sélecteur de produit), tous montés
  sur `/marketing-v2` → Vue globale.

**Hors scope, toujours pas construit :** intégration API temps réel avec
les plateformes ad (Meta/TikTok/Google/LinkedIn Ads) — remplacerait la
saisie manuelle par un pull automatique, mais nécessite des comptes
développeur/business vérifiés par plateforme ; à prioriser séparément si
la saisie manuelle s'avère trop lourde en usage réel.
**Statut :** ✅ Complete (vérification tsc/eslint/ruff faite ; vérification
navigateur réel non effectuée dans ce ticket — même limite que les phases
précédentes utilisant le skill `browse`, instable dans cet environnement).

### Phase 38 — Harmonisation visuelle globale du Hub sur les maquettes ChatGPT
**Contexte :** Emilie a réclamé un rendu visuel fidèle à ses maquettes ChatGPT
(« copier-coller des images »), avec les couleurs/logo ALNUA, et une harmonisation
de toutes les pages. Le rendu visuel est priorisé ; les branchements fonctionnels
seront reconnectés ensuite.

**Décision de conception :** créer un socle visuel unifié `MockupShell` qui
donne à chaque page département la même structure maquette : sidebar encadrée,
topbar avec titre/search/clock/actions, onglets sous le titre, grille de cartes
glassmorphism, sidebar droite activité + métriques, barre de commande flottante
en bas. Palette rétablie sur la charte ALNUA officielle (Obsidienne #0E1014,
Ivoire #F5F2EA, Titane #A7ADB5, Cuivre Rosé #C08A72 en accent uniquement) pour
éviter l'effet « brun orangé style Claude AI ».

**Livré :**
- `web/src/components/mockup/*` — `MockupShell`, `MockupTopbar`,
  `MockupBottomBar`, `MockupRightSidebar`, `MockupDirectory`,
  `MockupDepartmentPage` + 5 vues (overview/team/projects/missions/backlog) +
  widgets réutilisables.
- `web/src/components/layout/hub-shell.tsx` — route tous les départements
  (y compris `/rd`, `/marketing`, `/finances`, `/analytics`, `/brand`,
  `/secretary`, `/ceo`, `/hub`, `/hq`) dans le nouveau shell visuel.
- Remplacement des pages `page.tsx` des départements listés ci-dessus par
  `MockupDepartmentPage` (ou `MockupDirectory` pour `/hq`).
- Palette rétablie dans `web/src/app/globals.css` et `web/tailwind.config.ts`
  sur les tokens ALNUA officiels.

**Fonctionnalités temporairement déconnectées (à rebrancher) :**
- ~~`/rd`~~ — **reconnecté Phase B (2026-08-09)** → `rnd-v2` (+ `RdPageContent` pour deep-links).
- ~~`/marketing`~~ — **reconnecté** → `marketing-v2`.
- ~~`/finances`~~ — **reconnecté** → `finances-v2` (incl. Coûts & Factures DEC-016).
- ~~`/app`, `/gaming`, `/robo`~~ — **reconnectés** → `*-v2`.
- `/analytics` — Analytics agents panel, analytics view
  (anciennement dans `analytics/page.tsx`).
- `/brand` — Brand view / brand kits (anciennement dans `brand/page.tsx`).
- `/secretary` — Nadia Desktop, SAV, assistant chat, secretary console
  (anciennement dans `secretary/page.tsx`).
- `/ceo` — Assistant chat CEO, brief du jour, PRs GitHub, dossiers en attente
  (anciennement dans `ceo/page.tsx`).
- `/hub` — Bureau Office Hero, agents section, workflows, automations,
  CEO cockpit, production ops cockpit, pipeline codage, coûts LLM
  (anciennement dans `hub/page.tsx`).

**Hors scope / prochaines étapes :**
- ~~Reconnecter `/analytics`, `/brand`, `/secretary`, `/ceo`, `/hub`~~ — **live**
  (suite clean 2026-08-09, DeptV2 shells).
- Bascule visuelle optionnelle des `*-v2` sur un `MockupShell` unifié (chrome only).
- Remplacement des données mockées résiduelles dans les maquettes design.
- **Attention WIP local (BUG-019) :** working tree non commité peut remonter
  `/finances`/`/marketing` en maquette VAE — ne pas merger sans décision produit.
**Statut :** ✅ Complete (rendu + routes primaires live au HEAD `7dfad6f` /
  Audit 004). Voir Sprint REM-002 close-out dans `DOC_AUDIT.md`.

### Phase 39 — Idle agent work
**Objectif :** les agents avancent sans brief CEO précis — ops + produits +
initiatives entreprise (L1) + self-dev si trust ≥ 70 — via file hybride COO/CEO
et budget LLM adaptatif (`cost_monitor`).
**Référence :** `docs/specs/SPEC_IDLE_AGENT_WORK.md`, DEC-021.
**Dépendances :** Phase 30 (workflow_engine), Phase 31 (trust), ops scheduler
existant (`run_ops` / `semaine` / academy).
**Livrables cibles :** recettes `idle_plan_day` + `idle_drain` ; UI validation
file du jour sur `/ceo` ; OpenRoom lié aux vrais `workflow_runs` ; tests trust /
budget critical.
**Livré MVP (2026-08-10) :**
- `services/idle_work_queue.py` + `idle_work_recipes.py` (`idle_plan_day` / `idle_drain`)
- Scheduler 08:10 plan + interval drain ; env `IDLE_WORK_*`
- Gates : trust ≥ 0.70 self-dev, L2 ↔ `POST /workflows/idle/validate`, budget adaptatif
- OpenRoom : `runId` / `taskId` / `progress` réel ; `STATUS_LOAD` cosmétique → 0
- P0 parallèle : routes `dev_frontend` / `dev_integrator`, cartes bureau R&D,
  Phase 21 probes 4 gaming, `/analytics` → `AnalyticsAgentsPanel`
**Suite livrée (même jour) :** UI `/ceo` file idle (valider L2 / drain) ;
  L1 company/product = vrais drafts ; dept-v2 + lobby = load réel uniquement.
**Statut :** ✅ Complete (DEC-032 Vague 3, 2026-08-12) — preview livrables `/ceo`,
promote manuel + **auto-tickets [idle-ok] à la 1ʳᵉ validation L2**. Enrichissements
UI optionnels hors tampon 100 %.

### Phase 40 — Agent isolation (AAF Phase A)
**Objectif :** agents parallèles sans overwrite ; concurrence bornée ; merge
protégé (intégrateur).
**Référence :** `docs/specs/SPEC_AGENT_ISOLATION.md`, DEC-022.
**Livré (2026-08-10) :**
- `services/resource_locks.py` + `execution_slots.py` + `merge_policy.py` +
  façade `agent_isolation.py`
- Câblage coding / parallel_runner / plan_executor / fix_pipeline
- API `GET /isolation/status|locks|slots`, `POST /isolation/locks/release`
- Settings `ISOLATION_*` ; tests `tests/test_agent_isolation.py`
**Suite (hors Phase A) :** Loop Engine + Mission Graph (plan AAF B–D).
**Statut :** ✅ Complete.

### Phase 41 — Mission Graph (AAF Phase B)
**Objectif :** graphe Mission → Tasks (`depends_on`) séquentiel/parallèle,
persisté, API + OpenRoom — façade `plan_executor` (DEC-023).
**Référence :** `docs/specs/SPEC_MISSION_GRAPH.md`.
**Livré (2026-08-10) :**
- `services/mission_graph_*.py` + store `data/missions/`
- `POST/GET /missions*` ; `run_coo_plan` → Mission Graph
- OpenRoom `missionId` + overlay tasks EXECUTING/READY
- Client `web/src/lib/missions-api.ts` ; tests `test_mission_graph.py`
**Suite :** Loop Engine (Phase C).
**Statut :** ✅ Complete.

### Phase 42 — Loop Engine (AAF Phase C)
**Objectif :** FSM commun exécute → évalue → feedback → retry (cap) puis
escalade ; brancher fix_pipeline, plan/Mission, workflow `RETRYABLE`.
**Référence :** `docs/specs/SPEC_LOOP_ENGINE.md`, DEC-024.
**Livré (2026-08-10) :**
- `services/loop_engine.py` + models ; settings `LOOP_*`
- `fix_pipeline` via `run_loop_async` ; `_execute_step` via `run_loop`
- `workflow_engine` : `RETRYABLE` → retry puis `ECART` ; `GET /loop/defaults`
- Cap strict branché (`is_strict_loop` / `resolve_max_iterations`) sur merge,
  ship, integrator, fix_pipeline
- Tests `tests/test_loop_engine.py`
**Suite :** Review Chain + merge integrate (Phase D).
**Statut :** ✅ Complete.

### Phase 43 — Review Chain + Merge (AAF Phase D)
**Objectif :** chaîne ordonnée AUTO → BOARD → POLICY → INTEGRATE → DONE ;
autonomie merge staging/main ; integrate si N>1 branches.
**Référence :** `docs/specs/SPEC_REVIEW_CHAIN.md`, DEC-025.
**Livré (2026-08-10) :**
- `services/review_chain*.py` + `merge_autonomy` ; settings
  `REVIEW_CHAIN_STAGING_TRUST_MIN`
- Câblage `coding_pipeline` / `fix_pipeline` ; `ensure_integrate_task` ;
  recipe `mission_ship` ; API `/review-chain/*`
- Tests `tests/test_review_chain.py`
**Suite :** Capabilities + Trust Graph (Phase E).
**Statut :** ✅ Complete.

### Phase 44 — Capabilities + PermissionGuard (AAF Phase E)
**Objectif :** Capability Packs par rôle ; PermissionGuard fail-closed ;
Trust Graph (journal allow/deny) distinct du Trust Score.
**Référence :** `docs/specs/SPEC_CAPABILITY_GUARD.md`, DEC-026.
**Livré (2026-08-10) :**
- `capability_catalog` / `capability_packs` ; `permission_guard` ;
  `trust_graph.jsonl`
- Câblé merge (`assert_can_merge`) + `ads:spend` + worktree/git/PR/mail/
  abort ; API + UI `/trust` décisions récentes ; setting
  `PERMISSION_GUARD_ENABLED`
- Tests `tests/test_permission_guard.py`
**Suite :** Neo4j Trust Graph (hors scope volontaire) ; MCP PermissionGuard
  progressif livré (`X-MCP-Agent` + route map).
**Statut :** ✅ Complete.

### Phase 45 — Context Engine L1–L4 (AAF Phase F)
**Objectif :** compiler L1→L4 dans les prompts ; wipe L4 en fin de task ;
promotion collective L3→L2 (≥3 agents / bureau).
**Référence :** `docs/specs/SPEC_CONTEXT_ENGINE.md`, DEC-027.
**Livré (2026-08-10) :**
- `context_engine` + `working_memory` + `collective_learning` ;
  policies L1 / standards L2
- `inject_learning_context` délégué ; wipe L4 dans `plan_executor` ;
  API `/context/*` ; settings `CONTEXT_ENGINE_*` / `COLLECTIVE_*`
- Tests `tests/test_context_engine.py`
**Suite :** AAF plan A–F terminé — Neo4j hors scope volontaire ;
  MCP PermissionGuard progressif + call-sites catalog MVP câblés.
**Statut :** ✅ Complete.

### Phase 46 — Agent Lounge
**Objectif :** remplacer OpenRoom / « repas & détente » par un **Agent Lounge**
(expérimentation, challenges, collab, gamification) isolé de la compétition
prod et du trust ; agents autonomes en idle filler ; boucle proposition →
départements.
**Référence :** `docs/specs/SPEC_AGENT_LOUNGE.md`, DEC-031.
**Vagues :**
| Vague | Contenu | Statut |
|-------|---------|--------|
| V0 | Spec + DEC-031 + `data/lounge_product.json` (gate Academy) | ✅ 2026-08-11 |
| V1 | Shell `/lounge` + redirect OpenRoom + HQ / SiegeLifeLinks | ✅ 2026-08-11 |
| V2 | `lounge_scores` (reset mensuel) + API + panneau classement | ✅ 2026-08-11 |
| V3 | Activité Puzzle jouable + sessions | ✅ 2026-08-11 |
| V4 | Idle `lounge_session` (L0 filler) + LLM Lounge CN | ✅ 2026-08-11 |
| V5 | Propose → ticket / CEO (pas de write prod) | ✅ 2026-08-11 |
| V6 | Autres espaces (arcade, code, creative…) + tournois | ✅ 2026-08-11 |
**Livré V0 (2026-08-11) :**
- `docs/specs/SPEC_AGENT_LOUNGE.md`
- DEC-031 (deux rails scores, replace OpenRoom, autonomie, UI Hub)
- `data/lounge_product.json` (`status: scaffold`, `mvp_features`)
**Livré V1 (2026-08-11) :**
- `/lounge` shell (hero, 7 activités stubs, présence agents, live, events)
- `/openroom` → redirect `/lounge` (query `?agent=` conservée)
- HQ hotspot + SiegeLifeLinks + nav outils « Agent Lounge »
**Livré V2 (2026-08-11) :**
- `services/lounge_scores.py` + `api/routers/lounge.py` + `web/src/lib/lounge-api.ts`
- Classement Lounge dans le panneau droit (≠ `/competition`)
- Tests `tests/test_lounge_scores.py`
**Livré V3 (2026-08-11) :**
- `services/lounge_activities/puzzle.py` + `lounge_runtime.py`
- Sessions `/lounge/sessions` + panneau Puzzle UI
- Tests `tests/test_lounge_runtime.py`
**Livré V4 (2026-08-11) :**
- Idle kind `lounge_session` (filler en fin de file) + gates budget
- `services/lounge_llm.py` — modèle Lounge dédié
- DEC-031 §7 ; tests `tests/test_lounge_idle.py`
**Livré V5 (2026-08-11) :**
- Défaut LLM = `deepseek/deepseek-chat-v3.2`
- `services/lounge_propose.py` + `POST /lounge/propose` + UI propose
- Ticket `source=lounge` (validation humaine) ; tests `tests/test_lounge_propose.py`
**Livré V6 (2026-08-11) :**
- 7 modules `lounge_activities/*` + catalog unifié ; runtime multi-activité
- Tournois `lounge_tournaments` + `GET /lounge/tournaments` / activities / challenges
- UI : tuiles live + panneau play générique + events API
- Idle rotation activités ; tests `tests/test_lounge_v6.py`
**Statut :** ✅ Complete.

### Phase 47 — Overlay Jarvis (Nadia / Aria)
**Objectif :** dicter à Nadia (quotidien) et Aria (ops) : faits en **texte**,
réplique en **voix**, sans clone Marvel ni graphe n8n. Deux bots inchangés.
**Référence :** `docs/specs/SPEC_JARVIS_OVERLAY.md`, DEC-033.
**Lots :**
| Lot | Contenu | Statut |
|-----|---------|--------|
| 0 | Contrat : split faits/voix, 5 exemples gold, Edge TTS v1, persona reporté | ✅ 2026-08-14 |
| 1 | Telegram Nadia : Whisper STT + overlay LLM + Edge TTS + `filters.VOICE` | ✅ 2026-08-14 |
| 2 | ALNUA Desk : même overlay (ne plus lire le pavé) ; repli sans LLM | ✅ 2026-08-14 |
| 3 | Brief 8h vocal ; research/météo en tool | ✅ 2026-08-14 |
| 4 | Aria : STT ; TTS seulement alerte / action / décision | ✅ 2026-08-14 |
| 5 | ElevenLabs optionnel (voix originales, fallback Edge) | ⏸️ |
| Persona | Recalage Nadia après observation live | ⏸️ volontaire |
**Livré Lot 0 (2026-08-14) :** spec + DEC-033.
**Livré Lot 1 (2026-08-14) :**
- `services/voice_overlay.py` + `services/telegram_voice.py`
- `bots/telegram_secretary_voice.py` + `filters.VOICE`
- Flag `TELEGRAM_VOICE_REPLIES` (off par défaut)
- Tests `test_voice_overlay.py` / `test_telegram_voice.py`
**Livré Lot 2 (2026-08-14) :**
- Desk `spark_shell` : overlay seulement ; stop TTS à chaque envoi
- `spoken_overlay` + `fallback_overlay` ; flag `VOICE_OVERLAY_LLM`
**Livré Lot 3 (2026-08-14) :**
- Brief 8h : overlay vocal après le digest (bot + `run_secretary_morning_notify`)
- Tool météo `services/secretary_weather.py` (wttr.in, sans LLM)
- Overlay contextuel météo / brief / recherche ; keyword fallback si OpenRouter down
**Livré Lot 4 (2026-08-14) :**
- Aria Telegram : Whisper STT ; TTS overlay seulement alerte / action / décision
- `bots/telegram_coo_voice.py` ; bots Nadia et Aria restent séparés
**Statut :** 🔄 In progress (Lots 0–4 done).
