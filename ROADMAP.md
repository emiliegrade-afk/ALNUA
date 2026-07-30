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
| 21 | Outils réels (skills) pour les 15 agents spécialisés Gaming/Robotique (Phase 13) | ⏸️ Not started |

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
à leurs voisins `dev_gaming` (Nwiro/UE5), `embedded_dev` (SSH Pi/GPIO) ou `hardware`
(BOM Supabase). Leur brancher de vrais outils : Nwiro/UE5 pour `ai_programmer` /
`technical_artist` / `vfx_artist` ; accès SSH Pi / GPIO pour `vision_ai` / `firmware`
/ `electronics` ; lecture/écriture BOM Supabase pour `mechanical` / `electronics` /
`industrial_design` ; bancs de test connectés pour `qa_robot` / `safety`.
**Dépendances :** s'appuie sur l'infra des phases 16 (build/télémétrie UE5) et 19
(BOM étendu + Laboratoire connecté) — pas de sens de brancher un outil avant que
l'infra sous-jacente existe.
**Statut :** ⏸️ Not started — décidé le 2026-07-30 ("on le fera plus tard").
