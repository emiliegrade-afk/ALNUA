<!-- /autoplan restore point: none (plan authored fresh in this session, no prior version to restore) -->
# Plan — Refonte UI des pages Département (ALNUA Hub)

**Auteur du rough plan :** Claude (à partir de la demande utilisateur + 3 mockups + exploration du code `web/`)
**Statut :** rough plan — en cours de review via `/autoplan`
**Branche :** `feat/rnd-dossier-hub` (pas de renommage — voir note scope ci-dessous)

## Contexte / demande initiale

> "J'ai codé de nouvelles fonctions dans le hub, de nouveaux codeurs, de nouveaux
> publicitaires, je pense qu'on doit refaire l'UI des différents départements qui
> n'est plus adaptée et pas assez intuitive, voici une idée de nouvelle interface
> à adapter avec mes bonnes couleurs (obsidienne, cuivre rosé, titanium), mon logo."

3 mockups fournis montrent un pattern "Agentic OS" : sidebar gauche (logo, nav,
liste départements numérotée 01-10, outils), topbar (avatar COO + onglets
Vue générale/Départements/Missions/Analytics/Ressources + profil utilisateur),
zone centrale avec 3 vues par département (Équipe / Projets / Missions), panneau
droit "Activité en temps réel" persistant + widgets de synthèse.

## Ce qui existe déjà dans le code (`web/`) — ne pas réinventer

- **Design tokens** : `tailwind.config.ts` + `globals.css` définissent déjà obsidian
  (#111111/#1A1A1A/#232323), copper/cuivre (#B87333/#CF8D50/#6E451F), titanium/titane
  (#A7ADB5), ivory/ivoire (#F5F2EA) — palette des mockups = palette déjà en prod.
- **Logo** : `public/alnua-logo*.png`, `public/logo.svg`, `src/components/brand/alnua-logo.tsx`,
  `src/components/console/alnua-logo.tsx` — déjà utilisé dans `ConsoleSidebar`.
- **Shell partagé** : `ConsoleShell` → `ConsoleSidebar` + `ConsoleTopbar` + `<main>`.
  `ConsoleSidebar` a déjà Navigation / Pôles (11, via `CONSOLE_POLES` dans
  `lib/console/departments.ts`, avec code `01`-`11`) / Outils — proche de la maquette,
  numérotation et présentation à affiner seulement.
- **Shell page département** : `BureauPage` (`components/shared/bureau-page.tsx`) +
  `DepartmentHeader` + `BureauPanel` + `BureauAgentsSection` — utilisé par toutes les
  pages `/app`, `/gaming`, `/robo`, `/marketing`, `/finances`, `/rd`, `/ceo`,
  `/secretary`, etc. **Un seul point de refonte ici propage à tous les départements.**
- **Primitives graphiques** : `components/console/charts.tsx` a déjà Sparkline, Donut,
  Bars, Gauge, Heatmap, CommGraph, LevelBar — couvrent Vélocité (Bars), Bug Rate
  (Sparkline/ligne), Resource Allocation (Bars), Status Distribution (Donut) vus dans
  les mockups. Pas de nouvelle lib de charts à écrire.
- **AgentCard** (`components/console/agent-card.tsx`) : avatar/initiales, rôle,
  spécialité, statut (actif/réflexion/veille/revue), tâche courante, modèle, barre
  d'utilisation % — couvre déjà l'essentiel de la carte "membre d'équipe" des mockups
  (Théo Laurent 78%, Hao Zhang 64%, etc.).
- **ActivityFeed** (`components/console/activity-feed.tsx`) : flux temps réel par
  agent/dept/action déjà backé par `useConsoleData()`. Existe en mode `compact` pour
  widget, et en page dédiée `/activity`. Pas présent en permanence sur les pages
  département (gap réel, voir scope).
- **Data layer pôles** : `fetchProjects`/`fetchTickets` (`lib/api.ts`), `CONSOLE_POLES`
  (`lib/console/departments.ts`), `useConsoleData()` (`components/console/console-provider.tsx`).

## Ce qui manque réellement (gap mockups vs code actuel)

1. Les pages département (`AppPolePage` et équivalents) sont une liste verticale
   plate (agents → tickets → projets → console) — pas de structure à onglets
   Équipe / Projets / Missions comme dans les mockups.
2. Pas de vue **Missions en pipeline Kanban** (Backlog / In Progress / In Review /
   Completed) par département — actuellement les tickets sont un tableau simple
   (`AppTicketsSection`), pas un board.
3. Pas de **panneau détail membre** (mission en cours + checklist tâches + fil de
   discussion + notes privées + onglets Aperçu/Compétences/Performance/Mémoire avec
   charts) — nouveau composant.
4. Pas de **vue Projets en grille** avec anneau de progression %, badges stack,
   lien "voir le projet", ni le panneau de droite "vue d'ensemble du parc"
   (donut + bar chart) — actuellement liste simple de `BureauPanel`.
5. `ActivityFeed` n'est pas persistant en rail droit sur les pages département —
   seulement sur `/activity` et en widget compact du dashboard.
6. Pas de fil de discussion type chat (bulles message + saisie) réutilisable —
   `CooDrawer` a un pattern de drawer conversationnel à vérifier pour réutilisation
   avant d'écrire un nouveau composant.
7. Sidebar : liste `Pôles` actuelle est plate ; mockup groupe sous un header
   "Départements" avec le pôle actif visuellement mis en avant (léger, pas un
   changement structurel).

## Scope proposé (à trancher en review CEO)

**Dans le périmètre :**
- Nouveau composant `DepartmentWorkspace` (ou extension de `BureauPage`) avec
  3 onglets Équipe / Projets / Missions, appliqué via le shell partagé à tous les
  départements existants (P2 boil-the-ocean : un seul point de refonte, effort
  proportionnel au nombre de vues nouvelles, pas au nombre de départements).
- Board Missions (Kanban 4 colonnes) alimenté par `fetchTickets`/projets existants.
- Grille Projets avec anneau de progression, réutilisant `Donut`/`Gauge` de `charts.tsx`.
- Panneau membre (perf/compétences) réutilisant `Sparkline`/`Bars`/`LevelBar`.
- `ActivityFeed` en rail droit persistant sur les pages département (mode `compact`
  existant, juste repositionné dans le layout).
- Toilettage sidebar (numérotation, regroupement visuel "Départements").
- Nettoyage : suppression/fusion des anciens composants de listing (`AppTicketsSection`
  en simple liste) si totalement remplacés par le Kanban, pour éviter la duplication.

**Hors périmètre (à consigner dans TODOS.md, pas à deviner ici) :**
- Nouvelle identité visuelle / palette / logo — déjà en place, aucune demande de
  changement de charte.
- Refonte du dashboard `/hub` (`DashboardView`) — déjà très proche des mockups
  (KPIs, gauges, org network, activité live, heatmap) ; pas mentionné comme
  problématique par l'utilisateur.
- Nouveaux agents "codeurs"/"publicitaires" côté backend — l'utilisateur les
  mentionne comme contexte (déjà codés), pas comme scope de cette tâche.
- Rebasculer la branche sur `main` (889 fichiers d'écart, `main` visiblement très
  en retard) — hors sujet, à traiter séparément si besoin (noté, pas résolu ici).

## Notes de contexte pour la review

- Branche actuelle `feat/rnd-dossier-hub`, 5 commits d'avance sur son propre remote,
  `git diff main --stat` = 889 fichiers / +130k lignes — `main` est très en retard,
  ne pas s'en servir comme référence de base pour cette review.
- Pas de sprint actif au ROADMAP.md ("prochaine phase à définir avec Emilie") — cette
  refonte serait naturellement la Phase 11.
- Aucun doc de design (`*-design-*.md`) trouvé — /office-hours proposé et décliné par
  l'utilisateur (problème déjà bien cadré par les mockups + charte existante).

---

## Phase 1 — CEO Review

**Mode d'exécution :** run `/autoplan` automatisé, sans `AskUserQuestion` — chaque décision
intermédiaire ci-dessous est **auto-décidée** par l'agent selon les 6 principes (P1 Complétude,
P2 Boil-the-lakes, P3 Pragmatisme, P4 DRY, P5 Explicite > clever, P6 Biais vers l'action),
avec le principe moteur noté à chaque fois. Les décisions où deux options étaient
réellement défendables sont marquées **TASTE DECISION** et remontées telles quelles au
gate humain final (voir section dédiée en bas). Codex n'est pas installé sur cette machine
— la voix extérieure (Outside Voice) est **ignorée sur instruction explicite**, pas de repli
sur un sub-agent Claude.

### Audit système préalable

- `git log --oneline -30` : la zone `web/src/components/console/*` a connu **6 commits de
  fix design consécutifs** juste avant ce plan (`d9880cd` FINDING-001 statut API
  contradictoire topbar/sidebar, `7fcd614` FINDING-002 titre topbar écrasé à 1280px,
  `2ff02dc` FINDING-003 lisibilité titres widgets, `ab36242` FINDING-004 sparklines KPI
  fausses sous zéro, `4dec459` FINDING-006 mismatch hydratation SSR sur les coordonnées
  SVG de `CommGraph`, `ddb979e` follow-up FINDING-002). **Zone à re-vulnérabilité
  démontrée** — retrospective check du skill : être plus agressif sur cette zone.
  Deux enseignements concrets pour ce plan : (1) les nouveaux composants SVG (anneaux de
  progression, éventuel mini-graph du Kanban) doivent arrondir leurs coordonnées calculées
  dynamiquement comme le patch SSR de `charts.tsx:283-291` (`CommGraph`) l'a déjà fait —
  sinon même bug d'hydratation garanti ; (2) largeur minimale sur les titres tronqués
  (pattern déjà en place `console-topbar.tsx:90-92` avec commentaire explicite) à répliquer
  sur les nouveaux en-têtes d'onglets.
- `TODOS.md` : absent (confirmé) — créé en fin de review (voir plus bas).
- `BUGS.md` / `ROADMAP.md` / `DECISIONS.md` : présents, aucune entrée ne référence
  Équipe/Projets/Missions/Kanban — pas de travail en conflit ni de décision antérieure à
  respecter sur ce périmètre précis. `ROADMAP.md:16` confirme la Phase 3 ("Dashboard
  Next.js — siège social virtuel") comme ✅ Complete — cette review est bien la suite
  logique (Phase 11).
- Aucun test n'existe sur `web/src/components/console/*` ni `web/src/components/shared/
  bureau-*` — le seul test frontend du repo est `web/src/__tests__/assistant-chat.test.tsx`.
  Section 6 traite ce point en détail — c'est un signal fort, pas un détail.
- Branche `feat/rnd-dossier-hub` a avancé depuis la rédaction du rough plan (nouveau commit
  `2b41297` "real dispatch ownership, cloistered dev team, QA gate, Studio Typefully" en
  tête) — sans impact sur le périmètre de cette review, noté pour traçabilité seulement.

### 0A — Premise Challenge

1. **Est-ce le bon problème ?** Oui, avec une nuance. Emilie décrit le problème comme
   "l'UI n'est plus adaptée et pas assez intuitive" pour des départements qui ont grandi
   (nouveaux codeurs, nouveaux publicitaires). L'exploration confirme la prémisse : les
   pages département sont une liste verticale plate (agents → tickets → projets → console
   ad hoc, ex. `AppConsole` avec ses formulaires `AgentActionConsole` en plus de
   `BureauAgentsSection` et `AppTicketsSection` — **trois motifs UI différents empilés sur
   une seule page** `/app`). Le problème est réel, pas un problème de proxy (ex. ce n'est
   pas "on a besoin de plus d'agents", c'est bien "l'agencement de l'existant est illisible").
2. **Quel est l'outcome réel ?** Une product owner (Emilie, seule utilisatrice humaine du
   Hub) qui peut, en un coup d'œil par département, voir qui travaille sur quoi, où en sont
   les projets, et quelles missions sont en attente/en cours/en revue/terminées — sans
   scroller une liste plate. Le plan (tabs Équipe/Projets/Missions + rail activité) est le
   chemin direct vers cet outcome, pas un détour esthétique. Pas de solution "10x plus
   simple" identifiée qui atteindrait le même outcome sans structure à onglets : une
   simple recoloration ou un réagencement de la liste plate ne résoudrait pas le vrai
   problème (volume d'information croissant avec le nombre d'agents/projets).
3. **Que se passerait-il si on ne faisait rien ?** Douleur réelle et qui s'aggrave, pas
   hypothétique — le rough plan documente déjà 30+ agents dans `agent-bureau.ts` répartis
   sur 9 bureaux opérationnels ; chaque nouvel agent (le plan cite "nouveaux codeurs,
   nouveaux publicitaires" — `dev_integrator`, `coding_coach`, `content_app`,
   `content_gaming`, `content_robo`, `content_company`, `ads` sont tous des ajouts
   relativement récents visibles dans `agent-bureau.ts`) allonge une grille déjà dense sans
   hiérarchie. Le coût de l'inaction croît avec chaque agent ajouté — pas un pic ponctuel.

**Conclusion 0A :** prémisse validée, aucun blocage. Note pour le gate humain final (cf.
consigne de la tâche) : aucune préoccupation de niveau prémisse à signaler — le cadrage
d'Emilie tient face à l'exploration du code.

### 0B — Existing Code Leverage (carte affinée)

Le rough plan avait déjà une bonne première carte. Exploration du code confirme certains
points et **corrige deux erreurs de mapping** (marquées ⚠️ ci-dessous) découvertes en lisant
le code réel plutôt qu'en supposant depuis les noms de fichiers.

| Sous-problème (mockup) | Code existant | Verdict |
|---|---|---|
| Design tokens (obsidienne/cuivre/titanium) | `tailwind.config.ts`, `globals.css`, `lib/dept-colors.ts` (`DEPT_COLORS` — palette cuivre unifiée sur les 11 depts) | ✅ Complet, rien à faire |
| Logo | `alnua-logo.tsx` (brand + console) | ✅ Complet |
| Shell + sidebar + topbar | `console-shell.tsx` (76L), `console-sidebar.tsx` (275L, boucle `CONSOLE_POLES` L166-196), `console-topbar.tsx` (210L) | ✅ Existe, ajustements mineurs seulement |
| Shell page département | `bureau-page.tsx` (46L) + `department-header` + `bureau-panel.tsx` (48L) — **17 pages** l'utilisent | ✅ Un seul point de refonte propage bien, confirmé |
| Primitives graphiques | `charts.tsx` (346L) : Sparkline, Donut, Bars, Gauge, Heatmap, CommGraph, LevelBar | ✅ Complet, aucune lib à écrire |
| ⚠️ **Carte "membre d'équipe"** | Le plan cite `components/console/agent-card.tsx` (134L, prend un `ConsoleAgent` avec `utilization`/`model`/statut 4 états `active/thinking/idle/review`) comme la carte qui "couvre déjà l'essentiel". **C'est inexact pour les pages département** : celles-ci utilisent en réalité `components/shared/agent-card.tsx` (154L, via `BureauAgentsSection` — 9 pages) qui prend `icon/name/role/branch/description/skills/badge/status` avec un **statut à 4 états différent** (`idle/working/waiting/error`), **sans** `utilization`/`model`/couleur par agent (`hue`), mais **avec** un CTA "Déléguer une tâche" (`useCooStore`) absent du composant console. `console/agent-card.tsx` n'est en réalité utilisé que par `agents-view.tsx` (page `/agents`, roster global). **Deux composants `AgentCard` avec deux vocabulaires de statut différents pour le même concept** — violation DRY réelle (Section 5), pas juste une nuance de nommage. Voir 0C-bis pour la décision d'architecture. | ⚠️ Partiel — carte existe mais mauvaise pour le job, doublon à trancher |
| ⚠️ **Panneau détail membre** | Le plan liste ceci comme un gap total ("nouveau composant"). **Faux** : `components/openroom/agent-focus-panel.tsx` (143L) **existe déjà et est câblé** dans `BureauAgentsSection` (state `focusedAgentId`, ouverture au clic sur une carte). Il affiche déjà : avatar, statut live, tâche courante, fichier courant, barre de progression, log récent (10 dernières lignes). Il ne couvre **pas** les onglets Aperçu/Compétences/Performance/Mémoire ni le fil de discussion/notes privées du mockup — mais c'est une **extension** d'un composant existant à 143 lignes, pas une construction from-scratch. Change significativement l'estimation d'effort. | ⚠️ Partiel important — extension, pas création |
| Fil de discussion type chat | `components/shared/coo-drawer.tsx` (75L) — drawer conversationnel `AssistantChat embedded`, piloté par `useCooStore` (zustand), déjà réutilisé sur `/ceo` (`AssistantChat variant="ceo"`) | ✅ Pattern confirmé réutilisable pour le fil de discussion membre |
| Kanban Missions | `AppTicketsSection` (154L) : `fetchProjects` + `fetchTicketsList`, `TICKET_STATUSES` (`tickets.constants.ts`) | ⚠️ **Gap non documenté par le rough plan** : `TicketStatus` = `open \| in_progress \| done \| wont_fix` — **il n'existe aucun état "En revue" dans le modèle de données**. Le kanban 4 colonnes du mockup (Backlog/In Progress/In Review/Completed) ne peut pas se mapper 1:1 sans décision produit. Voir **TASTE DECISION #2**. |
| Grille Projets + anneau progression | `Donut`/`Gauge` (`charts.tsx`) existent visuellement. Progression : `api/routers/dashboard.py:128` a déjà un heuristique `_branch_progress(status)` (mapping statut→%) utilisé par `/branches/app`, `/branches/gaming`, `/branches/robo`. | ⚠️ **Gap non documenté par le rough plan, le plus sérieux trouvé** : `Project` (`lib/types.ts`) n'a **aucun champ `progress`** — il faut réutiliser/exposer l'heuristique `_branch_progress`. Plus grave : `ProjectBranch = "app" \| "gaming" \| "robotics" \| "other"` — **seuls 3 des 9 bureaux opérationnels ont un concept de "projet" filtrable** (App/Gaming/Robo). Marketing, Finances, R&D, Analytics, Secrétariat, Hub n'ont **aucune donnée "projet" par département**. Voir **TASTE DECISION #3**. |
| Rail activité persistant | `ActivityFeed` (92L) a déjà un mode `compact` prêt à l'emploi, alimenté par `useConsoleData()` | ✅ Complet, repositionnement layout seulement |
| Data layer | `fetchProjects`/`fetchTickets` (`lib/api.ts`), `CONSOLE_POLES`/`buildConsoleDepartments` (`departments.ts`) | ⚠️ **Gap non documenté** : `ConsoleDepartment.projects` (`departments.ts:290-293`, `DEFAULT_PROJECTS`) est un **stub statique en dur** ("Pipeline en cours" 62%, "Revue qualité" 38%) — jamais dérivé de `fetchProjects()`. Le pipeline de données "projets par département" n'existe pas encore, contrairement à ce que le rough plan laissait entendre. |
| Périmètre "tous les départements" | `BureauPage` : 17 pages. `BureauAgentsSection` : **seulement 9** (hub, secretary, app, gaming, robo, marketing, finances, rd, analytics). | ⚠️ **`/ceo` et `/brand` sont des pages CONSOLE_POLES mais n'utilisent PAS `BureauAgentsSection`** — `/ceo` est un "Mission Control" bespoke (brief + PR feed + dossiers en attente + chat, `app/ceo/page.tsx`), `/brand` affiche `BrandView` (assets de marque). Le nouveau `DepartmentWorkspace` à onglets Équipe/Projets/Missions s'applique naturellement à **9 des 11 pôles**, pas aux 11 — CEO et Brand gardent leur mise en page dédiée (voir "Hors périmètre"). |

Le plan ne reconstruit rien qui existe déjà en état utilisable — les deux "reconstructions"
identifiées (double `AgentCard`, stub `DEFAULT_PROJECTS`) sont déjà des duplications
*avant* ce plan, pas introduites par lui ; ce plan est l'occasion de les résoudre (P4 DRY).

### 0C — Dream State Mapping

```
  CURRENT STATE                         THIS PLAN                              12-MONTH IDEAL
  ─────────────                         ─────────                              ───────────────
  9 pages département =                 DepartmentWorkspace (Équipe/            Même workspace, mais :
  liste verticale plate                 Projets/Missions) sur les 9             - Kanban avec vrai statut
  (agents → tickets →                   bureaux opérationnels, alimenté         "En revue" (backend)
  projets → console ad hoc,             par une source de données              - Perf réelle par agent
  ex. AppConsole empile 3               d'agent UNIFIÉE (fin du doublon         (dérivée d'agent_logs +
  patterns UI sur /app)                 AgentCard), Kanban 4 colonnes,          cost_monitor, pas un stub)
                                         grille Projets avec anneau %,          - "Projets" par département
  2 AgentCard divergents                panneau membre étendu (4 onglets),      pour TOUS les bureaux
  (console/ vs shared/),                rail activité persistant.               (pas seulement App/Gaming/
  statuts non alignés                                                          Robo) — campagnes marketing,
                                        CEO + Brand restent bespoke              dossiers R&D, etc. comme
  Panneau membre existe                (hors périmètre, cohérent avec           "projets" de leur bureau
  déjà mais minimal                    ce qu'ils sont réellement)
  (AgentFocusPanel, pas de                                                     - Recherche Cmd+K réelle
  tabs/perf/mémoire)                                                            (le champ topbar actuel
                                                                                 est un faux input readonly)
  Projets = stub statique                                                      - WebSocket temps réel au
  en dur, aucune vraie                                                          lieu du polling 12s
  donnée par département
```

Ce plan **avance** vers l'idéal 12 mois — il ne s'en détourne pas — à condition de résoudre
le doublon `AgentCard` maintenant plutôt que d'en ajouter un troisième composant "juste pour
les tabs" (ce qui reculerait sur P4 DRY et rendrait l'unification future plus coûteuse).

### 0C-bis — Implementation Alternatives (obligatoire)

```
APPROCHE A — "Tabs par-dessus l'existant" (minimal viable)
  Résumé : Garder shared/agent-card.tsx + BureauAgentsSection + AgentFocusPanel tels quels.
           Ajouter un composant DepartmentWorkspace qui enveloppe l'existant dans 3 tabs.
           Étendre AgentFocusPanel avec les 4 onglets. Ajouter Kanban (nouveau composant,
           lit fetchTicketsList). Ajouter grille Projets (nouveau composant, lit
           fetchProjects, calcule progress via un port client de _branch_progress).
  Effort : M (fichiers touchés : ~6-8 nouveaux composants + 9 pages à re-brancher)
  Risque : Faible — ne touche pas au pipeline de données agent existant.
  Pour : Diff le plus petit, ship rapide, zéro risque de régression sur console/agent-card.tsx
         (toujours utilisé tel quel par /agents).
  Contre : Le doublon AgentCard (2 vocabulaires de statut) reste en place — la prochaine
           personne qui touche un statut d'agent devra choisir lequel des deux modifier,
           et devinera mal une fois sur deux. N'unifie pas utilization/model sur les pages
           département (ces champs resteront invisibles là où le mockup les montre).
  Reuses : BureauAgentsSection, AgentFocusPanel, AppTicketsSection (logique de fetch),
           charts.tsx en l'état.

APPROCHE B — "Unification du modèle agent" (architecture idéale)
  Résumé : Étendre shared/agent-card.tsx avec utilization/model/statut enrichi (en gardant
           le CTA "Déléguer"), rebrancher BureauAgentsSection pour consommer
           useConsoleData().departments[i].agents (déjà calculé par buildConsoleDepartments,
           déjà dérivé de BUREAU_AGENTS — zéro nouvelle donnée à inventer) au lieu de
           getAgentsForBureau() directement. console/agent-card.tsx (utilisé uniquement par
           /agents) devient soit un alias fin du composant unifié, soit reste tel quel pour
           le cas d'usage "roster compact multi-département" qui est légitimement différent
           visuellement. Un seul vocabulaire de statut partagé (ConsoleAgentStatus).
  Effort : L (touche departments.ts, bureau-agents-section.tsx, shared/agent-card.tsx,
           use-agent-statuses.ts, + validation sur les 9 pages consommatrices)
  Risque : Moyen — buildConsoleDepartments() recalcule déjà tout à chaque poll (12s) ;
           le brancher dans plus de composants signifie plus de re-renders à surveiller
           (voir Section 7 Performance), mais l'aggregation existe déjà, pas de nouveau
           coût réseau.
  Pour : Résout un vrai defect DRY qui existe *avant* ce plan (pas une invention du CEO
         review) ; débloque utilization%/model directement sur les pages département sans
         travail supplémentaire ; une seule source de vérité pour "qu'est-ce qu'un agent
         actif" évite un bug de type "un agent apparaît actif ici et en veille là" (déjà
         vu dans FINDING-001, statut contradictoire topbar/sidebar — même classe de bug).
  Contre : Diff plus large, touche un fichier partagé par 9 pages (risque de régression
           plus étendu s'il y a une erreur), nécessite de vérifier chaque usage de
           `status` (le CTA "Déléguer" dans shared/agent-card.tsx utilise le statut
           différemment que console/agent-card.tsx ne le fait).
  Reuses : buildConsoleDepartments (déjà écrit), ConsoleAgent (type déjà défini),
           useConsoleData (déjà le hook central).

APPROCHE C — non retenue comme approche distincte : "reconstruire from scratch un 3e
  AgentCard dédié aux tabs" a été éliminée d'emblée (violerait P4 DRY frontalement en
  ajoutant un 3e statut/vocabulaire au lieu d'en retirer un — l'inverse de l'objectif).
```

**RECOMMANDATION :** Approche B, avec une précision : ne pas retirer `console/agent-card.tsx`
dans ce chantier (son seul consommateur `/agents` n'est pas dans le périmètre de cette
refonte — retirer ce composant serait une extension hors du blast radius, P2). B est
recommandée parce que le doublon `AgentCard` est un défaut DRY préexistant découvert par
cette review, pas un risque hypothétique — le laisser en place (Approche A) revient à
construire la nouvelle UI phare sur une fondation qu'on sait déjà cassée, ce qui contredit
la préférence d'ingénierie "diff de la bonne taille : ne pas compresser une réécriture
nécessaire en un patch minimal" du skill. L'effort supplémentaire (M→L) est compressé par
CC à quelques heures, pas quelques jours.

**TASTE DECISION #1 (remontée au gate humain) :** Approche A vs B ci-dessus est un choix
d'architecture réel où les deux options sont défendables — A ships plus vite et isole
totalement le risque, B corrige une dette réelle mais touche plus de fichiers partagés.
Auto-décidé **B** pour cette review (P4 DRY + P2, dette préexistante dans le blast radius),
mais c'est un appel de goût, pas une évidence — à confirmer par Emilie avant l'eng review.

### 0D — Mode-Specific Analysis (SELECTIVE EXPANSION)

**Complexity check :** Le plan touche largement plus de 8 fichiers et introduit plus de
2 nouveaux composants (`DepartmentWorkspace`, Kanban, grille Projets, extension du panneau
membre, + retouches sidebar). Normalement un signal d'alerte "à challenger" — mais ici
c'est proportionné : le rough plan applique délibérément le principe boil-the-ocean via
**un seul point de refonte** (`BureauPage`/`BureauAgentsSection`, déjà partagés par 9 pages)
plutôt que de dupliquer le travail par département. Le nombre de fichiers touchés est
justifié par la propagation automatique, pas par de la complexité accidentelle. Pas de
challenge à lever ici.

**Changements minimums pour l'objectif déclaré :** Le strict nécessaire pour "onglets
Équipe/Projets/Missions lisibles par département" serait : (1) `DepartmentWorkspace` avec
3 tabs, (2) Kanban minimal (colonnes = les 4 `TicketStatus` réels, sans inventer "En
revue"), (3) grille Projets minimale (seulement pour App/Gaming/Robo, empty-state honnête
ailleurs), (4) rail `ActivityFeed` repositionné. Tout le reste (extension du panneau membre
à 4 onglets, résolution du doublon AgentCard, perf réelle par agent) est un ajout de valeur
réelle mais **peut être différé sans bloquer l'objectif central** — traité comme cherry-picks
ci-dessous plutôt que comme prérequis bloquant.

**Expansion scan (candidats, pas encore dans le scope) :**

- **10x check :** la version 10x de ce plan transformerait chaque page département en
  poste de pilotage où Emilie ne "consulte" plus mais "agit" — clic sur une carte Kanban →
  panneau détail → bouton "déléguer" pré-rempli avec le contexte de la mission → réponse en
  direct dans le fil de discussion, sans changer de page. Les briques existent déjà
  (`useCooStore.setPrefillMessage`, `CooDrawer`, `AgentFocusPanel`) mais ne sont pas
  connectées entre elles aujourd'hui.
- **Delight opportunities (≥5) :**
  1. Raccourcis clavier 1/2/3 ou ←/→ pour changer d'onglet Équipe/Projets/Missions.
  2. Empty states illustrés et honnêtes (pas juste "aucune donnée") pour les cas réels déjà
     identifiés en code : pôle Brand a **zéro agent** (`agentsForPole` ne matche aucun
     filtre pour `pole.id === "brand"` faute de `bureau` défini sur ce pôle dans
     `departments.ts:159-169`), et 6 des 9 bureaux opérationnels n'ont structurellement
     aucun "projet" (voir TASTE DECISION #3).
  3. Onglet "Mémoire" du panneau membre branché sur le catalogue réel
     (`GET /library/topics`, `skills/skill_library_memory.py` déjà documenté dans
     `CLAUDE.md`) plutôt qu'un texte statique — donnée déjà exposée par le backend.
  4. Sparkline de performance par agent dérivée de données **réelles** existantes
     (`agent_logs` déjà écrit par `log_agent_action`, `services/cost_monitor.py` déjà
     journalisé par jour) plutôt que d'inventer un nouveau modèle de données de séries
     temporelles.
  5. Board Missions cliquable pour avancer un statut (flèches) sans nécessiter de
     drag-and-drop dès la V1.
  6. Cmd+K réel remplaçant le faux champ de recherche `readOnly` du topbar
     (`console-topbar.tsx:109-123`, qui redirige juste vers `/agents` au focus).
- **Platform potential :** un `DepartmentWorkspace` générique bien fait devient
  l'infrastructure que **toute future page département** (et même de futurs bureaux non
  encore créés) réutilise sans réécrire — c'est déjà l'intention du rough plan, confirmée
  saine par l'exploration (`BureauPage` le fait déjà pour le shell).

**Cérémonie cherry-pick (auto-décidée, principe noté) :**

| # | Candidat | Effort | Décision | Principe / raison |
|---|---|---|---|---|
| 1 | Résoudre le doublon `AgentCard` (Approche B) | L (CC: ~1-2h) | **ACCEPTED** — scope de base affiné | P4 DRY + P2 (dette dans le blast radius) — voir TASTE DECISION #1 |
| 2 | Étendre `AgentFocusPanel` à 4 onglets (Aperçu/Compétences/Performance/Mémoire) | M (CC: ~1h) | **ACCEPTED** — scope de base | P1 complétude — sans ça le "panneau membre" du mockup reste à moitié fait ; c'est une extension d'un composant à 143 lignes, pas une création |
| 3 | Onglet Mémoire branché sur `GET /library/topics` réel | S (CC: ~20 min) | **ACCEPTED** | P2 boil-lakes (dans le blast radius du panneau membre, backend déjà prêt) + évite un risque AI-slop (Section 11) : un onglet "Mémoire" à contenu statique/inventé serait pire qu'absent |
| 4 | Sparkline perf agent dérivée de `agent_logs`/`cost_monitor` réels | M (CC: ~45 min) | **ACCEPTED** | P5 explicite > clever — donnée réelle existante, pas de fausse donnée (risque AI-slop direct sinon, cf. Section 11) |
| 5 | Raccourcis clavier tabs (1/2/3, ←/→) | S (CC: ~15 min) | **ACCEPTED** | P2 — trivialement dans le blast radius, largement sous 1 jour |
| 6 | Empty states honnêtes (Brand=0 agent, 6 bureaux sans projet) | S (CC: ~30 min) | **ACCEPTED** — scope de base | P1 complétude — cas réels déjà présents en prod aujourd'hui, pas hypothétiques |
| 7 | Cmd+K réel (recherche agents/tickets/projets) | L (CC: ~1 jour+) | **DEFERRED → TODOS.md** | P2 — hors blast radius (topbar global, pas ce plan) et dépasse le seuil 1 jour (indexation multi-source) |
| 8 | Drag-and-drop réel sur le Kanban (dnd-kit) | M-L (CC: ~half-day+) | **DEFERRED → TODOS.md** | P2/P5 — nouvelle dépendance, a11y clavier/tactile, + nécessite un champ d'ordre sur `Ticket` qui n'existe pas ; boutons flèches (item #5 du scan delight) couvrent le besoin en V1 sans cette dépense |
| 9 | Ajouter un vrai statut "En revue" au modèle `Ticket` (backend) | M (CC: ~1-2h mais cross-cutting) | **DEFERRED → TODOS.md** — voir TASTE DECISION #2 | P2 — touche le schéma backend + tous les consommateurs existants de `TicketStatus` (hors blast radius strict de ce plan frontend) ; relabeling 3 colonnes réelles retenu comme scope de base à la place |
| 10 | Étendre `ProjectBranch` à tous les bureaux + notion de "projet" par bureau (campagnes marketing, dossiers R&D comme projets) | XL | **DEFERRED → TODOS.md** — voir TASTE DECISION #3 | P2 — bien au-delà d'1 jour, redéfinit un concept produit (qu'est-ce qu'un "projet" pour Marketing/R&D/Finance), nécessite arbitrage produit avant tout travail technique |
| 11 | WebSocket temps réel au lieu du polling 12s (`CONSOLE_POLL_MS`) | L (backend + frontend) | **SKIPPED** | P2 — hors blast radius (nouveau endpoint FastAPI + gestion de connexions), le mockup dit "temps réel" mais 12s de polling est déjà perçu comme temps réel dans l'usage actuel (aucune plainte utilisateur documentée dans BUGS.md) |
| 12 | Fusionner le Kanban Missions avec l'état de dispatch live (`services/parallel_runner.py`) | — | **SKIPPED** | P4 DRY — mélangerait deux concepts distincts (ticket produit vs exécution LLM live), qui ont déjà chacun leur surface (`/activity`, `AgentFocusPanel`) ; les confondre créerait une nouvelle duplication au lieu d'en résoudre une |

### 0E — Temporal Interrogation

```
  HOUR 1 (fondations)      — Trancher TASTE DECISION #1 (unification AgentCard) et #2
                              (mapping colonnes Kanban) AVANT d'écrire le premier composant :
                              sinon l'implémenteur devine et re-fait le travail à la review
                              eng. Choisir aussi si DepartmentWorkspace vit dans
                              bureau-page.tsx ou en composant séparé monté par page.
  HOUR 2-3 (logique coeur)  — Ambiguïtés attendues : quel statut `TicketStatus` mappe sur
                              quelle des 3 colonnes retenues (voir TASTE DECISION #2) ; quel
                              sous-ensemble de `stats`/`kpisForPole` reste affiché hors-tabs
                              vs à l'intérieur de l'onglet Projets.
  HOUR 4-5 (intégration)    — Surprises probables : re-render en cascade si
                              `buildConsoleDepartments()` (recalculé à chaque poll 12s) est
                              maintenant consommé par 9 pages au lieu d'1 dashboard — vérifier
                              avec les devtools React Profiler avant de merger (Section 7) ;
                              le composant `AppConsole` (formulaires agent-action) sur `/app`
                              n'a pas de home évidente dans les 3 tabs Équipe/Projets/
                              Missions — décider s'il devient un 4e onglet ou reste hors-tabs.
  HOUR 6+ (polish/tests)    — Ce qui sera regretté si non planifié maintenant : absence totale
                              de tests sur cette zone (Section 6) — écrire au moins un test de
                              rendu par nouveau composant avant de merger, pas après ; audit
                              /design-review post-implémentation pour la même raison que les
                              6 FINDING-XXX précédents sur cette zone.

  Échelle : ces 6h+ humaines se compressent à ~30-60 min avec CC + gstack — mêmes décisions,
  vitesse d'implémentation 10-20x. Les 2 taste decisions ci-dessus doivent être tranchées par
  Emilie AVANT le lancement de l'implémentation, pas pendant.
```

### 0F — Mode Confirmation

**Mode retenu : SELECTIVE EXPANSION** (imposé par la tâche, cohérent avec le contexte :
itération sur un système existant, pas du greenfield). Scope de base du rough plan tenu à
un niveau bulletproof (voir les 11 sections ci-dessous), cherry-picks ci-dessus déjà
tranchés candidat par candidat. Sous ce mode, l'**Approche B** de 0C-bis s'applique
(architecture idéale) — cohérent avec le mode SELECTIVE EXPANSION qui peut favoriser soit
l'approche minimale soit l'idéale selon le contexte ; ici la dette DRY préexistante penche
clairement pour B.

---

## Revue approfondie — 11 sections (`sections/review-sections.md`)

### Section 1 — Architecture Review

**Diagramme système obligatoire (composants nouveaux vs existants) :**

```
  ConsoleShell (existant, inchangé)
   ├─ ConsoleSidebar (existant — retouche mineure : regroupement visuel "Départements")
   ├─ ConsoleTopbar (existant — inchangé dans le scope de base)
   └─ <main> BureauPage (existant, 17 pages)
        ├─ DepartmentHeader (existant, inchangé)
        └─ [NOUVEAU] DepartmentWorkspace  ◄── monté sur les 9 pages "opérationnelles" seulement
             ├─ Tabs (Équipe | Projets | Missions)          (/hub /secretary /app /gaming
             ├─ [Onglet Équipe]                              /robo /marketing /finances
             │    └─ AgentCard unifié (Approche B)            /rd /analytics)
             │         └─ [NOUVEAU] MemberDetailPanel        CEO + Brand : PAS de
             │              (extension de AgentFocusPanel     DepartmentWorkspace —
             │               existant, +4 onglets)            gardent leur page bespoke
             │              ├─ Aperçu (existant)
             │              ├─ Compétences (nouveau, lit BureauAgentDef.skills — déjà là)
             │              ├─ Performance (nouveau, Sparkline/Bars sur agent_logs+cost_monitor)
             │              └─ Mémoire (nouveau, GET /library/topics existant)
             ├─ [Onglet Projets]
             │    └─ [NOUVEAU] ProjectGrid (Donut/Gauge existants, fetchProjects existant,
             │                 progress porté depuis _branch_progress backend existant)
             └─ [Onglet Missions]
                  └─ [NOUVEAU] MissionsKanban (fetchTicketsList existant, colonnes = mapping
                               TASTE DECISION #2)
        └─ [NOUVEAU] ActivityRail (ActivityFeed existant, mode compact existant,
                      repositionné en colonne persistante — pas de nouveau composant)
```

**Data flow — nouveau flux "changement de statut Kanban" (les 4 chemins) :**

```
  UTILISATEUR clique flèche "→"  ──▶  MissionsKanban.onAdvance(ticket)  ──▶  PATCH /tickets/{id}
        │                                    │                                    │
        ▼                                    ▼                                    ▼
   [ticket = null ?]                  [statut suivant                      [échec réseau /
   Ne peut pas arriver — le            n'existe pas ?]                      timeout ?]
   bouton n'est rendu que              La dernière colonne (Terminé)
   pour un ticket réel                 n'a pas de flèche "→" —
   déjà chargé (garde-fou UI)          garde-fou UI, pas de bug             GAP si non géré : optimistic
                                        possible                            update non annulé → l'UI ment
                                                                             sur l'état réel (voir Section 2)
```

**State machine — statuts ticket dans le Kanban :**

```
        ┌────────┐   avance    ┌─────────────┐   avance    ┌──────┐
   ───▶ │  open  │ ──────────▶ │ in_progress │ ──────────▶ │ done │
        └────────┘             └─────────────┘             └──────┘
             │                                                  ▲
             │                    (retour arrière possible,     │
             └───── recule ───────  pas de transition directe ──┘
                                     open → done sans passer
                                     par in_progress — garde-fou
                                     à ajouter côté UI, sinon
                                     transition "impossible" mais
                                     non bloquée)
   `wont_fix` : état terminal séparé, atteint uniquement via une action explicite
   hors-Kanban (pas de colonne dédiée retenue — voir TASTE DECISION #2, option A).
```

**Coupling concerns :** l'Approche B couple `BureauAgentsSection`/`shared/agent-card.tsx` à
`useConsoleData()` (contexte React), alors qu'aujourd'hui ce composant est indépendant du
`ConsoleProvider` — nouveau couplage justifié (élimine un couplage caché pire : deux sources
de vérité pour "un agent est actif"). Avant/après : avant, `BureauAgentsSection` dépend de
`useAgentStatuses()` (`lib/agent-bureau.ts` + `openroom-api`) ; après, elle dépend de
`useConsoleData()` qui elle-même agrège la même source — donc le couplage réel n'augmente
pas le nombre de dépendances externes, il les fait juste transiter par un seul point.

**Scaling :** `buildConsoleDepartments()` recalcule les 9 départements × leurs agents à
chaque poll (12s) et maintenant potentiellement à chaque page département visitée (au lieu
de seulement `/hub` et `/agents`) — à 30 agents et 9 départements, le calcul reste trivial
(`O(n)` sur un tableau statique de ~30 éléments), aucun risque à 10x ni 100x agents dans un
horizon réaliste. Le vrai risque de scaling est ailleurs : `fetchTicketsList({ limit: 100 })`
(`app-tickets-section.tsx:38`) plafonne déjà à 100 tickets sans pagination — un Kanban avec
plusieurs centaines de tickets legacy silencieusement tronquerait la colonne "Terminé".
**GAP** à traiter en Section 4/7.

**Single points of failure :** aucun nouveau SPOF introduit — tout transite par `hubFetch`
(déjà le point unique existant, déjà doté d'un timeout 30s et d'auth uniforme
`hubApiKeyHeaders`).

**Sécurité architecture :** aucun nouvel endpoint d'écriture sensible identifié dans le
scope de base (PATCH statut ticket = déjà un besoin existant, pas nouveau — `AppTicketsSection`
crée déjà des tickets via `CreateTicketModal`). Voir Section 3 pour le détail.

**Scénario de panne production réaliste :** l'API Hub tombe pendant que le Kanban a un
changement de statut optimiste en vol → l'utilisateur voit la carte dans la nouvelle colonne
mais le serveur n'a rien persisté → au prochain poll/refresh, la carte "revient en arrière"
sans explication. Le plan doit spécifier un rollback visuel + toast d'erreur (pattern déjà
utilisé par `AppTicketsSection` via `toast.error`, `sonner`) — **GAP à combler**, voir
Section 2.

**Rollback posture :** changement 100% frontend (aucune migration DB dans le scope de
base) → rollback = revert Git + redeploy Vercel, quelques minutes. Le seul risque de
rollback plus lent serait si TASTE DECISION #2/#3 introduisaient un changement de schéma
backend — d'où leur report explicite en TODOS.md plutôt que leur inclusion silencieuse.

**Ce qui rendrait cette architecture "belle" (SELECTIVE EXPANSION) :** un seul hook
`useDepartmentWorkspace(bureau)` qui retourne `{ agents, projects, missions }` déjà formés
pour les 3 tabs, calculé une fois à partir de `useConsoleData()` + `fetchProjects` +
`fetchTicketsList` — évite que chaque tab refasse son propre fetch/filtre. C'est un
raffinement d'implémentation, pas un changement de scope — à documenter pour l'eng review.

**Potentiel plateforme :** confirmé — `DepartmentWorkspace` bien conçu devient la brique
que toute future page bureau (et bureaux pas encore créés) réutilise sans réécrire.

### Section 2 — Error & Rescue Map

Aucune méthode/service n'est encore écrit (c'est un rough plan, pas du code) — cette
section anticipe les codepaths que l'implémentation va créer, à partir des patterns déjà
en place dans `app-tickets-section.tsx`/`hub-fetch.ts`.

```
  CODEPATH (prévu)                    | CE QUI PEUT MAL TOURNER          | EXCEPTION / GAP
  -------------------------------------|-----------------------------------|------------------
  MissionsKanban#onAdvance             | PATCH /tickets/{id} timeout       | AbortError (déjà géré par hubFetch, 30s)
                                        | API retourne 404 (ticket supprimé | GAP — non géré nulle part aujourd'hui
                                        |   entre chargement et clic)       |
                                        | API retourne 409/validation       | GAP — pas de gestion de conflit prévue
  ProjectGrid#load                     | fetchProjects() réseau échoue      | Déjà catché ailleurs (AppTicketsSection
                                        |                                    |   pattern : catch → tableau vide) — à répliquer
  MemberDetailPanel "Mémoire" tab       | GET /library/topics 404/vide       | GAP — nouveau, doit dégrader proprement
                                        | Mem0/skill_library_memory timeout  | GAP — nouveau
  MemberDetailPanel "Performance" tab   | agent_logs vide (agent jamais      | Cas normal, pas une erreur — empty state
                                        |   loggé, ex. agent tout neuf)      |   requis (pas un GAP si traité comme tel)
  buildConsoleDepartments (Approche B) | liveAgents incomplet pendant le     | Déjà géré — utilizationFor() a un défaut
                                        |   premier poll                     |   (12%) — pattern existant, à conserver
```

```
  EXCEPTION / GAP                       | RESCUED ?  | ACTION DE RESCUE                     | VU PAR L'UTILISATEUR
  ---------------------------------------|-----------|----------------------------------------|------------------------
  PATCH ticket 404 (supprimé entre-temps)| N ← GAP   | —                                      | Rien ne se passe, carte figée en silence ← MAUVAIS
  PATCH ticket 409/validation            | N ← GAP   | —                                      | Idem ← MAUVAIS
  fetchProjects() réseau échoue          | Y (pattern à répliquer) | catch → tableau vide + toast.error | "Impossible de charger les projets"
  GET /library/topics échoue/vide        | N ← GAP   | —                                      | Onglet Mémoire vide sans explication ← MAUVAIS
  agent_logs vide (agent nouveau)        | N/A       | Empty state dédié (pas une erreur)      | "Pas encore d'historique pour cet agent"
```

**Règles à respecter à l'implémentation (déjà actées dans `CLAUDE.md`, rappel ici car ce
plan les touche directement) :** `parse_json_response()` côté backend sur toute sortie LLM
concernée (n/a ici, scope frontend pur) ; côté frontend, pas de `catch { }` vide sans au
minimum un `toast.error` ou un état d'erreur visible — le pattern `AppTicketsSection:48-51`
(`catch { setTickets([]); onTicketsChange?.(0); }`) est **silencieux envers l'utilisateur**
(aucun toast) et ne doit **pas** être copié tel quel dans le nouveau Kanban : c'est un
défaut préexistant à corriger en le répliquant, pas un modèle à suivre à l'identique.
**Décision auto (P1 complétude + Prime Directive #1 "zero silent failures") :** le Kanban et
la grille Projets doivent afficher un `toast.error` + état "réessayer" en cas d'échec réseau,
contrairement au pattern muet actuel d'`AppTicketsSection`. Ajouté au scope de base (pas un
cherry-pick — c'est un standard minimal, pas une extension).

### Section 3 — Security & Threat Model

- **Surface d'attaque :** le seul nouvel endpoint d'écriture plausible est un PATCH statut
  ticket pour le Kanban — vérifié : `api/routers/core.py:179` a déjà `allowed = {"open",
  "in_progress", "done", "wont_fix"}` pour la validation de statut ticket, donc l'endpoint
  PATCH existe probablement déjà côté backend (pas un nouvel endpoint) ; à confirmer par
  l'eng review si le frontend a juste besoin de le consommer ou si un endpoint manque.
- **Validation d'entrée :** rien de nouveau ici que le pattern `hubFetch` ne gère déjà —
  pas de nouveau champ texte libre destiné à un LLM dans ce scope (le Kanban/grille/panneau
  membre sont des vues, pas des formulaires de saisie libre).
- **Autorisation :** ALNUA Hub est mono-utilisateur (Emilie) protégé par `HUB_API_KEY`
  obligatoire (SEC-002, déjà en place) — pas de scoping multi-utilisateur à vérifier ici,
  cohérent avec l'architecture existante. Examiné, rien à signaler de nouveau.
- **Secrets :** aucun nouveau secret introduit.
- **Dépendances :** le cherry-pick #8 (drag-and-drop, `DEFERRED`) aurait introduit une
  nouvelle dépendance (`dnd-kit` ou équivalent) — reporté, donc **aucune nouvelle
  dépendance npm** dans le scope de base retenu. Examiné, rien à signaler.
- **Classification des données :** agents/tickets/projets sont des données business
  internes (déjà couvertes par la note `CLAUDE.md` sur `agents_pole.py` — PII redaction
  désactivée intentionnellement car données business réelles) — cohérent, rien de nouveau.
- **Injection :** aucun nouveau vecteur — pas de requête SQL/template construite dynamiquement
  côté frontend dans ce scope.
- **Audit logging :** un changement de statut ticket (Kanban) est une opération qui mérite
  une trace — vérifier à l'eng review si `PATCH /tickets/{id}` journalise déjà via
  `log_agent_action` équivalent côté ticket (pattern agent) ou s'il faut l'ajouter. **GAP
  potentiel, à vérifier — pas assez d'information dans ce rough plan pour trancher, noté
  pour l'eng review plutôt que deviné ici.**

Rien de sévérité High trouvé — cohérent avec un changement d'UI pur sur un outil interne
mono-utilisateur déjà protégé par clé API obligatoire.

### Section 4 — Data Flow & Interaction Edge Cases

**Traçage de flux (Kanban) :** voir diagramme Section 1. Point non couvert par ce
diagramme et à ajouter : **`fetchTicketsList({ limit: 100 })` plafonne à 100** — pour un
Kanban qui doit montrer une colonne "Terminé" potentiellement volumineuse avec l'historique,
100 tickets se remplissent vite. **GAP** : soit paginer par colonne, soit limiter
explicitement l'affichage "Terminé" aux N derniers avec un lien "voir tout l'historique"
(réutilise `ROUTES.tickets` déjà existant, cf. `app-tickets-section.tsx:80`). **Décision
auto (P3 pragmatique + P5 explicite) :** limiter chaque colonne Kanban aux tickets actifs
non filtrés par le fetch existant (déjà borné à 100 côté API) + lien "Tous les tickets" par
colonne — pas de nouvelle pagination à construire pour la V1, ajouté au scope de base
comme garde-fou explicite plutôt que silencieux.

**Edge cases d'interaction :**

```
  INTERACTION                    | EDGE CASE                          | GÉRÉ ? | COMMENT
  --------------------------------|--------------------------------------|--------|----------------------------------
  Clic carte membre (déjà existe) | Double-clic rapide                  | Oui    | Un seul focusedAgentId (state), pas de race
  Kanban — avancer statut         | Double-clic bouton flèche            | NON ← GAP | Pas de disabled pendant la requête en vol → double PATCH possible
  Kanban — avancer statut         | Utilisateur change d'onglet          | NON ← GAP | Requête PATCH en vol, résultat appliqué à un composant démonté → à garder (AbortController, pattern déjà dans hubFetch) mais le state local du Kanban doit vérifier un flag "still mounted"
  Onglets Équipe/Projets/Missions | Changement rapide d'onglet en boucle | NON ← GAP | Si chaque onglet déclenche son propre fetch au montage (pattern actuel AppTicketsSection), changer d'onglet 5x en 2s = 5 fetch concurrents ; nécessite un cache par bureau (voir hook suggéré Section 1) ou un debounce
  Grille Projets — 0 résultat     | Bureau sans concept "projet" (6/9)   | NON ← GAP (avant ce plan) | Empty state requis — accepté au scope de base (cherry-pick #6)
  Grille Projets — beaucoup       | >20 projets pour un seul bureau      | N/A    | Cas non observé dans les données actuelles (App/Gaming/Robo ont un nombre de projets faible) — pas un GAP réel aujourd'hui, à surveiller si ça change
  Rail activité — 0 événement     | Déjà géré                            | Oui    | `activity-feed.tsx:44-48` a déjà un empty state textuel
```

### Section 5 — Code Quality Review

- **DRY :** le doublon `AgentCard` (`console/agent-card.tsx` vs `shared/agent-card.tsx`,
  deux vocabulaires de statut `active/thinking/idle/review` vs `idle/working/waiting/error`
  pour le même concept) est la violation DRY la plus significative trouvée — déjà traitée
  en 0C-bis/0D (Approche B, cherry-pick #1 ACCEPTED). Deuxième duplication mineure : le
  pattern de fetch "projects filtrés par branch + tickets filtrés par project_id"
  (`app-tickets-section.tsx:36-47`) sera réécrit au moins 2 fois de plus (grille Projets +
  Kanban) sans un hook partagé — **décision auto (P4 DRY) : factoriser dans un hook
  `useDepartmentData(bureau)` unique dès la V1**, plutôt que dupliquer le pattern
  copier-coller une 3e fois. Ajouté au scope de base.
- **Naming :** `DepartmentWorkspace`/`MissionsKanban`/`ProjectGrid`/`MemberDetailPanel`
  cohérents avec les conventions existantes (`BureauPage`, `BureauPanel`, `AgentCard`) —
  rien à signaler.
- **Sur-ingénierie :** aucune abstraction prématurée identifiée dans le scope de base tel
  que resserré par le "minimum changes" de 0D.
- **Sous-ingénierie :** le pattern `catch { setX([]); }` silencieux d'`AppTicketsSection`
  (déjà signalé Section 2) est un exemple de sous-ingénierie préexistant à ne pas répliquer.
- **Complexité cyclomatique :** `MissionsKanban` (mapping 3-4 statuts → 3-4 colonnes +
  gestion optimistic update + erreurs) est le composant le plus à risque de dépasser
  5 branches — à surveiller à l'implémentation, pas un problème du plan lui-même.

### Section 6 — Test Review

```
  NOUVEAUX FLUX UX :        DepartmentWorkspace (tabs), Kanban (avancer statut),
                             ProjectGrid (clic → lien projet), MemberDetailPanel (4 tabs,
                             fil de discussion), raccourcis clavier tabs
  NOUVEAUX FLUX DE DONNÉES : buildConsoleDepartments → BureauAgentsSection (Approche B),
                             fetchProjects → ProjectGrid (+ progress), fetchTicketsList →
                             MissionsKanban, GET /library/topics → onglet Mémoire,
                             agent_logs+cost_monitor → onglet Performance
  NOUVEAUX CODEPATHS :       mapping statut→colonne (TASTE DECISION #2), garde-fou limite
                             100 tickets, empty states (Brand 0 agent, 6 bureaux 0 projet)
  NOUVEAUX JOBS ASYNC :      aucun (tout est fetch synchrone au montage/poll, cohérent avec
                             l'existant — pas de nouveau job d'arrière-plan)
  NOUVELLES INTÉGRATIONS :   GET /library/topics (déjà existant côté backend, nouveau côté
                             frontend), possible PATCH /tickets/{id} (à confirmer existant)
  NOUVEAUX CHEMINS ERREUR :  voir Error & Rescue Registry ci-dessous
```

**Constat le plus important de cette section, à traiter comme un finding à part entière :**
**zéro test n'existe aujourd'hui sur `web/src/components/console/*` ni
`web/src/components/shared/bureau-*`** — le seul test frontend du repo entier est
`web/src/__tests__/assistant-chat.test.tsx`. Construire 4-6 nouveaux composants sur une
zone à taux de régression visuelle démontré (6 commits FINDING-XXX récents, cf. audit
système) **sans aucun test** serait une régression de posture, pas juste une omission.
**Décision auto (P1 complétude + P2 boil-the-lakes, plafonné à l'effort proportionné) :**
ajouter au scope de base un test de rendu minimal (Vitest + Testing Library, déjà
configurés via `vitest.config.ts`) par nouveau composant — happy path + empty state — pas
une suite E2E Playwright complète (ça, c'est un follow-up raisonnable, ajouté à TODOS.md
plutôt qu'imposé maintenant, cf. P2 seuil 1 jour).

- Test qui donnerait confiance à 2h du matin un vendredi : un test qui simule
  `fetchTicketsList` retournant une erreur réseau et vérifie que le Kanban affiche le toast
  + ne perd pas les données déjà chargées.
- Test qu'un QA hostile écrirait : changer 2 fois de statut le même ticket en moins de
  100ms (double-clic) et vérifier qu'une seule requête PATCH part.
- Test chaos : `fetchProjects()` retourne un tableau avec un `Project` dont `branch` ne
  matche aucun des 3 bureaux gérés (ex. donnée corrompue "marketing") — la grille ne doit
  pas planter, juste ignorer/logger.
- Pyramide de tests : majoritairement unitaire/composant (Vitest+RTL) pour cette V1 —
  cohérent avec l'absence totale d'infra E2E actuellement (pas de Playwright configuré
  dans ce repo à ce stade — à confirmer, hors scope de vérifier ici).
- Flakiness : aucun test dépendant du temps réel/horloge attendu ici (le composant
  `console-topbar.tsx` a un `setInterval` d'horloge — si testé, mocker `Date`).

### Section 7 — Performance Review

- **N+1 :** pas de pattern N+1 base de données ici (frontend pur), mais **N+1 réseau**
  possible si chaque onglet (Équipe/Projets/Missions) fetch indépendamment à chaque
  montage sans cache — déjà signalé Section 4/5, résolu par le hook `useDepartmentData`
  proposé.
- **Mémoire :** `buildConsoleDepartments()` reste `O(nombre d'agents)`, négligeable même
  à 10x le nombre actuel d'agents (~30 → ~300 resterait instantané en JS).
- **Caching :** le passage à l'Approche B signifie que 9 pages consomment maintenant
  `useConsoleData()` au lieu d'1 (dashboard) — le contexte recalcule déjà tout au poll
  (12s) indépendamment du nombre de consommateurs (un seul `useMemo` en amont dans
  `console-provider.tsx:155-189`), donc pas de coût multiplicatif réel, juste plus de
  re-renders React à vérifier au profiler (déjà noté en 0E Hour 4-5).
- **Chemins lents (top 3 estimés) :** (1) premier montage d'un onglet Projets sur un
  bureau avec beaucoup de tickets/projets (borné par la limite 100 déjà en place) ; (2) le
  panneau membre "Performance" si l'agrégation `agent_logs`/`cost_monitor` se fait
  côté frontend sur un historique non paginé — **à vérifier à l'implémentation que
  l'agrégation se fait côté backend**, pas en téléchargeant tout l'historique brut ; (3)
  `Sparkline`/`Bars` (SVG pur, déjà utilisés ailleurs) — négligeable, déjà éprouvé en prod.
- **Connexions :** aucune nouvelle connexion DB/Redis/HTTP persistante — tout passe par
  `hubFetch` (HTTP simple, déjà le pattern).

### Section 8 — Observability & Debuggability Review

- **Logging :** aucun logging frontend structuré n'existe aujourd'hui au-delà de
  `console.error` implicite des `catch` — cohérent avec le reste du frontend Next.js (pas
  un défaut introduit par ce plan). Rien de nouveau à ajouter au-delà des toasts déjà
  actés en Section 2 (visibilité utilisateur, pas observabilité opérateur — proportionné
  pour un outil interne mono-utilisateur).
- **Métriques :** pas de nouvelle métrique backend introduite par ce plan (scope frontend).
- **Debuggabilité à 3 semaines :** si un bug de statut Kanban est signalé, la seule trace
  serait l'état actuel de la DB `tickets` (pas d'audit trail de changement de statut) —
  **GAP potentiel**, mais cohérent avec l'absence d'audit trail déjà notée en Section 3 ;
  reporté à la même décision (vérifier à l'eng review si `PATCH /tickets/{id}` journalise
  déjà, sinon c'est un ajout backend hors du scope frontend strict de ce plan).
- **Ce qui rendrait cette feature agréable à opérer (SELECTIVE EXPANSION) :** un simple
  `console.warn` structuré côté frontend quand un fetch de département échoue, taggé par
  bureau — coût quasi nul, utile en dev.

### Section 9 — Deployment & Rollout Review

- **Sécurité migration :** aucune migration DB dans le scope de base retenu (les deux
  changements qui en auraient nécessité une — TASTE DECISION #2 option B, #3 — sont
  reportés à TODOS.md précisément pour cette raison).
- **Feature flag :** pas nécessaire vu l'absence de risque de données — un déploiement
  frontend Next.js/Vercel standard suffit, cohérent avec le reste du repo (`vercel.json`
  déjà présent).
- **Ordre de rollout :**

```
  1. Merger l'unification AgentCard (Approche B) seule d'abord — vérifier les 9 pages
     département au visuel avant d'empiler le reste (isole le risque le plus large).
  2. Merger DepartmentWorkspace (tabs) + ActivityRail repositionné.
  3. Merger ProjectGrid.
  4. Merger MissionsKanban (le plus interactif, le plus risqué en edge cases — dernier).
  5. Merger l'extension MemberDetailPanel (4 onglets) — dépend de 1, indépendant de 2-4.
```

- **Fenêtre de risque déploiement :** aucune (pas de code backend simultané ancien/nouveau
  à gérer — frontend statique/SSR Next.js redeployé atomiquement par Vercel).
- **Vérification post-déploiement (5 premières minutes) :** visiter les 9 pages
  département + `/agents` (vérifier que l'Approche B n'a pas cassé le roster global) +
  `/hub` (vérifier que le dashboard, premier consommateur historique de
  `buildConsoleDepartments`, n'a pas régressé).
- **Smoke test :** un test de rendu par page département (déjà couvert par le cherry-pick
  test minimal de Section 6) sert aussi de smoke test si exécuté en CI avant déploiement.

### Section 10 — Long-Term Trajectory Review

- **Dette technique introduite :** aucune nouvelle dette nette — ce plan **réduit** la
  dette existante (doublon AgentCard, stub `DEFAULT_PROJECTS`) plus qu'il n'en crée, à
  condition que TASTE DECISION #2/#3 soient tranchées consciemment (reportées, pas
  ignorées) plutôt que contournées par un hack silencieux à l'implémentation.
- **Path dependency :** un `DepartmentWorkspace` générique bien conçu **facilite** les
  changements futurs (nouveau bureau = même composant, zéro réécriture) — c'est le sens
  inverse d'un one-way door.
- **Réversibilité :** 4/5 — tout est frontend, revert Git trivial ; le seul aspect
  moins réversible serait si TASTE DECISION #2/#3 étaient tranchées et implémentées
  (changement de schéma), ce qui est précisément pourquoi elles sont reportées à un
  arbitrage produit explicite plutôt que décidées en silence ici.
- **La question à 1 an :** un nouvel ingénieur lisant ce plan dans 12 mois comprendrait
  immédiatement pourquoi CEO/Brand ne sont pas dans le `DepartmentWorkspace` (pages
  bespoke déjà différentes) et pourquoi le Kanban n'a que 3 colonnes réelles au lieu de 4
  (documenté ici, TASTE DECISION #2) — à condition que ces deux notes survivent dans la
  doc finale (elles sont dans ce fichier + TODOS.md, donc oui).
- **Potentiel plateforme (confirmé) :** voir Section 1.
- **Rétrospective cherry-picks :** aucun candidat rejeté ne s'avère porteur pour les
  candidats acceptés — les items différés (Cmd+K, drag-and-drop, statut "En revue", perf
  temps réel) sont tous indépendants des items acceptés, aucune dépendance cachée détectée.

### Section 11 — Design & UX Review (scope UI détecté — obligatoire)

- **Architecture de l'information :** premier regard = statut agents (qui travaille) ;
  deuxième = état des projets (où on en est) ; troisième = missions en attente (quoi
  faire ensuite) — cohérent avec l'ordre Équipe→Projets→Missions du mockup et avec le
  principe "hiérarchie comme service" (que voit l'utilisateur en premier/deuxième/
  troisième).
- **Couverture des états d'interaction :**

```
  FEATURE          | LOADING          | EMPTY                        | ERREUR           | SUCCÈS       | PARTIEL
  -----------------|-------------------|-------------------------------|-------------------|--------------|------------------
  Onglet Équipe    | Skeleton (existant bureau-page-skeleton.tsx à réutiliser) | Brand=0 agent — GAP à combler (cherry-pick #6) | Toast (nouveau, Section 2) | Grille agents | N/A
  Onglet Projets   | GAP — à définir  | 6/9 bureaux — GAP à combler (cherry-pick #6) | Toast (nouveau) | Grille + anneaux | Chargement partiel (projets ok, progress backend down) — GAP non traité
  Onglet Missions  | GAP — à définir  | Bureau sans ticket — état neutre, pas une erreur | Toast (nouveau) | Kanban rempli | Ticket en vol pendant changement statut — GAP Section 2/4
  Panneau membre   | Existant (AgentFocusPanel) | N/A (toujours un agent réel au clic) | GAP nouveau (onglet Mémoire) | 4 onglets | N/A
```

  **GAP transverse :** aucun état "loading" (skeleton) n'est spécifié pour les 3 nouveaux
  onglets dans le rough plan. `bureau-page-skeleton.tsx` existe déjà — **décision auto
  (P4 DRY + P1 complétude) : réutiliser ce skeleton existant pour l'état loading des 3
  tabs plutôt que d'en inventer un nouveau**, ajouté au scope de base.
- **Cohérence du parcours utilisateur :** clic carte → panneau détail → (futur, 10x check
  non retenu au scope de base) délégation en un geste — cohérent avec le ton "cockpit"
  qu'Emilie demande.
- **Risque AI-slop :** deux risques concrets identifiés et déjà neutralisés en amont
  (cherry-picks #3 et #4 ACCEPTED) : un onglet "Mémoire" à texte statique/inventé, ou une
  sparkline "Performance" sur données fictives, seraient tous deux du slop visuel classique
  (jolie charte, données fausses) — **explicitement évité** en branchant sur des données
  réelles existantes (`GET /library/topics`, `agent_logs`/`cost_monitor`) plutôt
  qu'improvisées.
- **Alignement DESIGN.md :** aucun `DESIGN.md`/doc de design formel n'existe dans ce repo
  — les tokens Tailwind + `dept-colors.ts` en tiennent lieu de facto, déjà confirmés
  alignés avec les mockups (0B).
- **Intention responsive :** `ConsoleShell` a déjà un motif mobile complet (`mobileOpen`,
  breakpoints `lg:` partout) — le rough plan ne mentionne pas explicitement le
  comportement mobile du Kanban 4 colonnes (généralement le point le plus dur à rendre
  responsive d'un dashboard "Agentic OS"). **Décision auto (P1 complétude) : le Kanban
  doit dégrader en scroll horizontal snap sur mobile (pattern simple, cohérent avec
  `alnua-scroll` déjà utilisé ailleurs) plutôt que d'empiler 4 colonnes verticalement** —
  ajouté au scope de base comme exigence explicite, pas laissé à l'implémentation de deviner.
- **Accessibilité de base :** navigation clavier des tabs (cherry-pick #5 ACCEPTED
  couvre une partie), mais le Kanban avec boutons flèches (pas de drag-and-drop, décision
  du scope de base) est justement le choix le plus accessible au clavier — bon alignement
  naturel entre la décision d'architecture (pas de dnd-kit) et l'accessibilité, à noter
  positivement plutôt que comme un compromis.

**Recommandation standard du skill :** vu le scope UI significatif de ce plan, lancer
`/plan-design-review` avant implémentation est pertinent — à décider par Emilie, pas
auto-décidé ici (hors du périmètre de cette review CEO).

---

## Error & Rescue Registry (complet)

| Méthode/Codepath | Ce qui peut mal tourner | Exception/Gap | Rescued ? | Action | Vu par l'utilisateur |
|---|---|---|---|---|---|
| `MissionsKanban#onAdvance` | Timeout réseau | `AbortError` | Oui (hubFetch, 30s) | Retry manuel via bouton | "Délai dépassé, réessayer" |
| `MissionsKanban#onAdvance` | Ticket supprimé entre-temps | 404 | **N ← GAP** | À définir : re-fetch + retirer la carte silencieusement + toast | Actuellement rien — à corriger |
| `MissionsKanban#onAdvance` | Conflit/validation serveur | 409/422 | **N ← GAP** | À définir : rollback optimistic update + toast | Actuellement rien — à corriger |
| `MissionsKanban#onAdvance` | Double-clic pendant requête en vol | Race condition | **N ← GAP** | Disabled sur le bouton pendant la requête | Actuellement double PATCH possible |
| `ProjectGrid#load` | Réseau échoue | Erreur générique | Oui (pattern à répliquer) | catch → tableau vide + **toast.error (nouveau, pas juste silencieux)** | "Impossible de charger les projets" |
| `ProjectGrid#load` | `Project.branch` ne matche aucun bureau connu | Donnée inattendue | **N ← GAP** | Filtrer/logger, ne pas planter | À vérifier à l'implémentation |
| `MemberDetailPanel` onglet Mémoire | `GET /library/topics` échoue/vide | 404/timeout | **N ← GAP** | Empty state dédié + pas de crash | Actuellement non spécifié |
| `MemberDetailPanel` onglet Performance | `agent_logs` vide (agent neuf) | Cas normal | N/A (pas une erreur) | Empty state "Pas encore d'historique" | Comportement attendu |
| `useDepartmentData(bureau)` (nouveau hook proposé) | Fetch concurrent multiple (changement rapide d'onglet) | Race condition | **N ← GAP** | Cache/dedupe par bureau | Actuellement non spécifié — à construire dès la V1 |

## Failure Modes Registry

```
  CODEPATH                        | MODE DE PANNE                | RESCUED ? | TEST ? | VU PAR L'UTILISATEUR | LOGGÉ ?
  ----------------------------------|--------------------------------|-----------|--------|------------------------|--------
  MissionsKanban#onAdvance          | 404 ticket supprimé            | N         | N      | Silencieux ← CRITICAL GAP | N
  MissionsKanban#onAdvance          | 409/422 conflit                | N         | N      | Silencieux ← CRITICAL GAP | N
  MissionsKanban#onAdvance          | Double-clic → double PATCH     | N         | N      | Incohérence visuelle ← CRITICAL GAP | N
  ProjectGrid#load                  | branch inconnu                 | N         | N      | Risque de crash silencieux ← CRITICAL GAP | N
  MemberDetailPanel (Mémoire)       | endpoint échoue                | N         | N      | Onglet vide sans explication ← WARNING | N
  useDepartmentData (fetch multi-onglet) | changements rapides d'onglet | N   | N      | Fetch redondants, pas visible utilisateur | N
```

**3 CRITICAL GAPS confirmés** (RESCUED=N + TEST=N + USER SEES=Silencieux) — tous sur le
Kanban, cohérent avec le fait que c'est le composant le plus interactif et le dernier du
plan de rollout (Section 9) précisément pour cette raison. **Décision auto (Prime
Directive #1 "zero silent failures" + P1 complétude) : ces 3 gaps doivent être fermés avant
que le Kanban soit considéré "fini"**, pas laissés en dette — ajoutés au scope de base, pas
à TODOS.md (contrairement aux cherry-picks, ce ne sont pas des extensions, ce sont des
trous dans le scope déjà annoncé par le rough plan lui-même).

---

## Hors périmètre ("NOT in scope")

En plus des 4 exclusions déjà actées par le rough plan (nouvelle identité visuelle,
refonte `/hub` dashboard, nouveaux agents backend, rebase sur `main`), cette review ajoute :

- **CEO et Brand n'entrent pas dans `DepartmentWorkspace`** — ce sont des pages bespoke
  (Mission Control / Brand assets) qui n'ont jamais utilisé `BureauAgentsSection` ;
  découvert par l'exploration du code, pas supposé par le rough plan. Rationale : ne pas
  forcer un moule Équipe/Projets/Missions sur des pages qui ne modélisent pas des équipes.
- **Statut ticket "En revue" (TASTE DECISION #2)** — nécessite un arbitrage produit +
  changement de schéma backend, reporté à TODOS.md.
- **Notion de "projet" pour les 6 bureaux sans `ProjectBranch` (TASTE DECISION #3)** —
  redéfinition de concept produit, reporté à TODOS.md.
- **Cmd+K réel** — hors blast radius (topbar global), reporté à TODOS.md.
- **Drag-and-drop Kanban** — nouvelle dépendance + a11y non triviale, reporté à TODOS.md.
- **WebSocket temps réel** — hors blast radius (backend), skippé (pas de douleur
  utilisateur documentée sur le polling 12s actuel).
- **Fusion Kanban/dispatch live** — skippé, éviterait de résoudre une duplication en en
  créant une autre (P4).
- **Suite E2E Playwright complète** — reportée à TODOS.md ; seul un test de rendu minimal
  par composant est retenu au scope de base (Section 6).

## Ce qui existe déjà (confirmé et étendu)

Le rough plan avait raison sur : design tokens, logo, shell (`ConsoleShell`/`ConsoleSidebar`/
`ConsoleTopbar`), shell de page (`BureauPage`/`BureauPanel`), primitives graphiques
(`charts.tsx`), `ActivityFeed` en mode compact, data layer de base (`fetchProjects`/
`fetchTickets`/`CONSOLE_POLES`).

Le rough plan avait tort ou incomplet sur (corrections de cette review, détaillées en 0B) :
un **panneau détail membre existe déjà** (`AgentFocusPanel`, à étendre — pas à créer) ; il
existe **deux `AgentCard` divergents**, pas un seul composant réutilisable tel quel ; les
**"projets" par département sont un stub statique en dur**, pas une donnée réelle
branchée ; **CEO et Brand ne participent pas au motif agents/tickets/projets** malgré leur
présence dans `CONSOLE_POLES` ; **il n'existe aucun état "En revue"** dans le modèle de
données ticket.

## Dream state delta

Ce plan, avec les cherry-picks acceptés, amène le système à **~80% de l'idéal 12 mois**
décrit en 0C : il résout le doublon AgentCard, étend le panneau membre avec de vraies
données (mémoire + performance), corrige le stub Projets pour les 3 bureaux qui ont de
vraies données, et pose l'infrastructure `DepartmentWorkspace` réutilisable. Les 20%
restants (statut "En revue" réel, notion de projet pour tous les bureaux, recherche Cmd+K,
temps réel WebSocket) sont explicitement nommés et reportés à TODOS.md plutôt que laissés
implicites — cohérent avec la Prime Directive #7 du skill ("everything deferred must be
written down").

---

## TASTE DECISIONS — à trancher par Emilie avant l'eng review

Ces 3 décisions ont été auto-tranchées pour permettre à cette review d'avancer (run
automatisé, pas d'`AskUserQuestion`), mais ce sont des choix où deux options sont
réellement défendables — remontées telles quelles, pas masquées :

1. **Unifier les deux `AgentCard` maintenant (Approche B, 0C-bis) vs les laisser
   coexister (Approche A) le temps de ce chantier.** Auto-décidé : B. Argument pour A :
   ship plus vite, risque isolé à un seul nouveau composant. Argument pour B : corrige une
   dette réelle découverte par cette review, dans le blast radius de ce même plan.
2. **Mapping du Kanban 4 colonnes du mockup sur un modèle de données à seulement 3 statuts
   réels (`open/in_progress/done`, pas de "En revue").** Auto-décidé : relabeler en 3
   colonnes réelles pour la V1, reporter l'ajout d'un vrai statut "En revue" (backend) à
   TODOS.md. Argument pour un 4e statut immédiat : colle exactement au mockup fourni.
   Argument pour 3 colonnes : évite une migration de schéma + mise à jour de tous les
   consommateurs existants de `TicketStatus` dans un chantier qui devait rester frontend.
3. **Que devient l'onglet "Projets" pour les 6 bureaux sans concept de projet
   (Marketing/Finances/R&D/Analytics/Secrétariat/Hub) ?** Auto-décidé : empty state
   honnête pour la V1, report à TODOS.md d'une réflexion produit sur "qu'est-ce qu'un
   projet pour Marketing" (campagnes ?) / "pour R&D" (dossiers ?) / etc. Argument pour un
   empty state simple : évite de deviner un modèle produit qu'Emilie n'a pas validé.
   Argument pour l'inventer maintenant : le mockup montre un onglet Projets rempli sur
   tous les départements, un empty state sur 6/9 bureaux peut sembler incomplet dès le
   ship.

---

## Résumé de complétion

```
+====================================================================+
|            MEGA PLAN REVIEW — COMPLETION SUMMARY                   |
+====================================================================+
| Mode sélectionné      | SELECTIVE EXPANSION                        |
| Audit système         | 6 commits FINDING-XXX récents sur cette    |
|                        | zone (retrospective check) ; 0 test        |
|                        | existant ; TODOS.md absent (créé)          |
| Step 0                | Approche B (0C-bis) retenue ; 3 TASTE       |
|                        | DECISIONS remontées au gate humain          |
| Section 1  (Arch)     | 3 issues trouvées (doublon AgentCard, stub  |
|                        | DEFAULT_PROJECTS, limite 100 tickets)       |
| Section 2  (Erreurs)  | 9 codepaths mappés, 5 GAPS (dont 3 CRITICAL)|
| Section 3  (Sécurité) | 1 point à vérifier (audit trail PATCH       |
|                        | ticket), 0 High severity                    |
| Section 4  (Data/UX)  | 9 edge cases mappés, 6 non gérés            |
| Section 5  (Qualité)  | 2 issues DRY trouvées                       |
| Section 6  (Tests)    | Diagramme produit, 0 test existant sur la   |
|                        | zone touchée — gap le plus sérieux du plan  |
| Section 7  (Perf)     | 2 risques identifiés (N+1 réseau, historique|
|                        | non paginé côté panneau Performance)        |
| Section 8  (Observ.)  | 1 gap (pas d'audit trail statut ticket)     |
| Section 9  (Deploy)   | 0 risque migration, ordre de rollout défini |
| Section 10 (Futur)    | Réversibilité : 4/5, dette nette négative   |
|                        | (ce plan réduit la dette existante)         |
| Section 11 (Design)   | 4 issues (skeleton manquant, mobile Kanban  |
|                        | non spécifié, 2 risques AI-slop neutralisés)|
+--------------------------------------------------------------------+
| Hors périmètre        | écrit (8 items)                             |
| Ce qui existe déjà    | écrit, 5 corrections apportées au rough plan|
| Dream state delta     | écrit — ~80% de l'idéal 12 mois atteint     |
| Registre erreurs      | 9 méthodes, 3 CRITICAL GAPS                 |
| Modes de panne        | 6 total, 4 CRITICAL GAPS (dont 1 warning)   |
| TODOS.md              | créé, 6 items proposés                      |
| Propositions scope    | 12 candidats, 6 ACCEPTED, 4 DEFERRED,       |
|                        | 2 SKIPPED                                   |
| CEO plan              | intégré dans ce fichier (pas de fichier     |
|                        | séparé — run /autoplan, pas de session      |
|                        | interactive ~/.gstack/)                     |
| Voix extérieure       | ignorée sur instruction explicite (Codex    |
|                        | non installé, pas de repli sub-agent)       |
| TASTE DECISIONS        | 3 (listées ci-dessus, à trancher par Emilie)|
| Diagrammes produits    | 6 (architecture, data flow, state machine,  |
|                        | error flow, rollout, couplage)              |
| Diagrammes obsolètes   | 0 trouvé dans les fichiers touchés          |
| Décisions non résolues | 3 TASTE DECISIONS (pas de blocage — notées  |
|                        | pour le gate humain, run auto-décidé)       |
+====================================================================+
```

**Préoccupations de niveau prémisse (0A) pour le gate humain final :** aucune. La
prémisse d'Emilie ("l'UI département n'est plus adaptée") tient face à l'exploration du
code — confirmée, pas juste supposée.

---

## Phase 2 — Design Review

**Mode d'exécution :** `/plan-design-review` via `/autoplan`, run automatisé — pas
d'`AskUserQuestion`, chaque gap est auto-décidé selon les 6 principes (P1 Complétude, P2
Boil-the-lakes, P3 Pragmatisme, P4 DRY, **P5 Explicite > clever, P6 Biais vers l'action** —
ces deux derniers dominent en cas de conflit, comme demandé pour cette phase). Cible de
review : ce fichier plan (Phase 1 incluse), pas le code — le code n'a pas encore été écrit.
Les 3 mockups réels fournis par Emilie (décrits en "Contexte") restent la cible visuelle ;
aucune maquette IA n'a été générée pour cette review — le brief textuel existant + les
tokens déjà en prod suffisent, générer un mockup à partir d'une re-description avec perte
des images réelles aurait été redondant, pas additif.

### Step 0 — Design Scope Assessment

**0A. Note initiale de complétude design : 6/10.**
La Phase 1 (CEO review) a déjà fait un travail design inhabituellement rigoureux pour une
review de scope/stratégie — table d'états loading/empty/error/success/partial (Section 11),
2 risques AI-slop identifiés et neutralisés (onglet Mémoire, sparkline Performance), et une
recommandation explicite de lancer `/plan-design-review`. Mais évalué avec la grille dédiée
design (7 passes ci-dessous) plutôt que comme une sous-section parmi 11, des trous concrets
apparaissent : aucun wireframe ASCII de la composition d'écran réelle, aucun storyboard du
parcours émotionnel, plusieurs états "partiel" explicitement notés GAP et non résolus, des
trous d'accessibilité concrets et vérifiables dans le code existant (voir Pass 6), une
incohérence de troncature de nom déjà présente dans `shared/agent-card.tsx` qui serait
héritée telle quelle par l'Approche B, et une décision de dépendance (primitive Tabs)
absente du Section 3 "zéro nouvelle dépendance". Ce sont des trous réels, pas de la
sévérité — d'où 6/10, pas 3/10.
**Ce que serait un 10 pour ce plan précis :** un wireframe ASCII de la page département
complète (sidebar + topbar + ligne KPI + tabs + rail activité) à ≥1280px ET en mobile, un
storyboard émotionnel explicite (5 secondes / 5 minutes / 5 ans) pour Emilie, chaque état
"partiel" de la table Section 11 résolu (pas juste listé GAP), la sémantique ARIA du Kanban
et des tabs explicitement spécifiée, et le bug de troncature vérifié corrigé avant que
l'Approche B ne le propage à 9 pages.

**0B. Statut DESIGN.md : absent** (confirmé par la Phase 1 — aucun fichier `*-design-*.md`
au repo). Pas de blocage : la palette obsidienne/cuivre/titanium/ivoire (`tailwind.config.ts`,
`globals.css`, `web/src/lib/dept-colors.ts`) + le vocabulaire de composants existant
(`BureauPage`, `AgentCard` ×2, `charts.tsx`, `ActivityFeed`) tiennent lieu de système de
design de facto et sont suffisamment décrits par le mockup + cette review pour calibrer les
décisions ci-dessous. `/design-consultation` resterait recommandé en tâche de fond
(consigné, pas bloquant).

**0C. Levier design existant — à réutiliser, ne pas réinventer** (au-delà de ce que la
Phase 1 avait déjà cartographié en 0B) :
- `web/src/components/shared/bureau-page-skeleton.tsx` — skeleton déjà générique, déjà
  décidé réutilisable pour le loading des 3 tabs (Phase 1, Section 11).
- `web/src/components/tickets/tickets.constants.ts` (`STATUS_STYLES`, `TICKET_STATUSES`) —
  couleurs de statut déjà définies et déjà utilisées par `/tickets` et
  `AppTicketsSection` ; **non mentionné par la Phase 1 comme source de vérité pour les
  couleurs de colonnes Kanban** — voir Pass 5.
- `web/src/components/console/activity-feed.tsx:44-48` — empty state textuel déjà géré,
  rien à faire.
- `web/src/components/console/agent-card.tsx:84` — a déjà `truncate` sur le nom agent ;
  `web/src/components/shared/agent-card.tsx:103` ne l'a **pas** — précédent direct à copier
  lors de l'unification Approche B (voir Pass 6).
- `web/src/lib/dept-colors.ts` — palette cuivre unifiée déjà en place, confirmé aligné.
- Aucune primitive `Tabs` accessible dans `web/src/components/ui/` (vérifié : glob
  `components/ui/tabs*.tsx` = 0 résultat) — `DepartmentWorkspace` partira de zéro sur ce
  point précis, voir Pass 5.

**0D. Focus de cette review :** les 7 passes ci-dessous sont traitées intégralement (pas de
réduction de scope) conformément à la règle anti-skip de `review-sections.md` — aucune
n'est écartée au motif que la Phase 1 a déjà "fait du design".

### Pass 1 — Information Architecture : 6/10 → 9/10

**Ce qui existe déjà de bien :** la Phase 1 (Section 11) établit un ordre de lecture
défendable — Équipe (qui travaille) → Projets (où on en est) → Missions (quoi faire
ensuite) — cohérent avec l'ordre du mockup et avec le principe "hiérarchie comme service".

**Gaps trouvés :**
1. **Aucun wireframe ASCII** de la composition d'écran réelle (sidebar 270px fixe déjà
   vérifiée dans `console-sidebar.tsx:97` + topbar 64px + ligne KPI (`kpisForPole`,
   `departments.ts:237-288`) + tabs + rail activité). Le diagramme Section 1 de la Phase 1
   montre l'arbre de composants, pas la disposition visuelle — les deux sont différents et
   le second manque.
2. **Ambiguïté non résolue** : la Phase 1 (Section 1, "Ce qui rendrait cette architecture
   belle") note elle-même "quel sous-ensemble de `stats`/`kpisForPole` reste affiché
   hors-tabs vs à l'intérieur de l'onglet Projets" comme une question pour Hour 2-3 — c'est
   une décision de hiérarchie de premier ordre, pas un détail d'implémentation, et elle
   n'est jamais tranchée dans le plan.
3. **Aucun tab par défaut spécifié** à l'ouverture d'une page département.

**Décisions auto (P5 explicite > clever) — ajoutées au scope de base :**
- La ligne KPI (`kpisForPole`) **reste au-dessus des tabs, inchangée** — elle mélange des
  métriques agents/projets/finances qui ne correspondent à aucun tab unique ; la replier
  dans l'onglet Projets casserait la lecture "vue d'ensemble en un coup d'œil" que la ligne
  KPI sert déjà.
- **Tab par défaut à l'ouverture = Équipe**, toujours (pas de mémorisation du dernier tab
  visité en V1 — cohérent avec l'ordre de lecture Équipe→Projets→Missions déjà acté ;
  mémoriser le dernier tab est un raffinement, déféré à TODOS.md).
- Wireframe ASCII à produire par l'implémenteur avant le premier commit de
  `DepartmentWorkspace` (≥1280px et mobile) — pas à générer ici en mockup IA (hors mandat de
  cette review, cf. note en tête de section), mais explicitement requis comme livrable
  d'implémentation.

### Pass 2 — Interaction State Coverage : 7/10 → 9/10

La table d'états de la Phase 1 (Section 11) est déjà une réussite rare pour un plan à ce
stade — la plupart des plans sautent complètement cette dimension. Deux cases sont
explicitement marquées GAP et **non résolues** dans le fichier :

1. **Onglet Projets, état "Partiel"** : "chargement partiel (projets ok, progress backend
   down) — GAP non traité". **Décision auto (P1 complétude + P5 explicite) :** `ProjectGrid`
   doit distinguer `progress: null/undefined` (backend `_branch_progress` indisponible —
   afficher un anneau neutre/tireté + "—") de `progress: 0` (vrai 0% réel) — confondre les
   deux mentirait à Emilie sur l'état réel d'un projet (elle croirait qu'il n'a pas démarré
   alors que la donnée est juste indisponible). Ajouté au scope de base.
2. **`MemberDetailPanel`, sous-onglets Compétences/Performance/Mémoire** : le plan ne dit
   pas si les 4 sous-onglets fetchent tous au montage du panneau (coût réseau immédiat) ou
   à la demande au clic (lazy). **Décision auto (P3 pragmatique) :** lazy — fetch au premier
   clic sur chaque sous-onglet, pas au montage du panneau ; cohérent avec le hook
   `useDepartmentData` déjà proposé par la Phase 1 (Section 1/5) pour éviter le N+1 réseau,
   même logique appliquée un niveau plus bas.
3. **Cadence de poll vs tab actif non spécifiée** : `buildConsoleDepartments()` tourne déjà
   toutes les 12s (`CONSOLE_POLL_MS`, `console-provider.tsx:42`) indépendamment du tab
   affiché — mais `fetchProjects`/`fetchTicketsList` (Projets/Missions) n'ont pas de cadence
   de poll définie. **Décision auto (P2 boil-lakes, effort trivial) :** ces deux fetchs ne
   pollent QUE si leur tab est actif (pas de fetch en tâche de fond pour un tab non affiché)
   — évite un Kanban qui change de colonne sous les yeux d'Emilie pendant qu'elle est sur
   l'onglet Équipe, sans qu'elle sache pourquoi au retour.

**Ce qui était déjà résolu et ne doit pas être re-flagué :** le skeleton transverse
(Section 11 "GAP transverse", déjà décidé) et le rollback/toast Kanban (Sections 2/4, déjà
décidé) — crédité, pas répété comme un nouveau gap.

### Pass 3 — User Journey & Emotional Arc : 4/10 → 8/10

Aucun storyboard explicite n'existe dans le plan (ni Phase 1 ni rough plan). La Phase 1
mentionne le "ton cockpit" une fois (Section 11) sans le dérouler. Storyboard reconstruit
pour Emilie, seule utilisatrice humaine :

```
ÉTAPE                          | ÉMOTION VISÉE                | PLAN LE SPÉCIFIE ?
--------------------------------|-------------------------------|---------------------
Arrive sur /app                 | "Je scanne en 5s, pas de      | Non avant cette review —
                                 |  liste plate à dérouler"      | fixé Pass 1 (tab par défaut)
Scanne l'onglet Équipe          | Réassurée (qui travaille)     | Oui (AgentCard existant)
                                 | ou alertée (agent bloqué)     | Non — pas de signal de
                                 |                                | "statut figé trop longtemps"
                                 |                                | (delight différé, pas bloquant)
Clique une carte agent           | "Pas besoin de cliquer 4 fois | Non avant cette review —
                                 |  pour voir l'essentiel"       | fixé ci-dessous (tab défaut)
Ouvre un bureau sans projet      | "Ce n'est pas cassé, c'est    | Non avant cette review —
(6/9 bureaux)                    | juste un bureau différent"    | fixé ci-dessous (copie empty state)
Avance un ticket au Kanban       | Satisfaction / frustration si | Oui (rollback+toast, Phase 1)
                                 | échec réseau                  |
```

**Gaps concrets :**
1. **Tab par défaut du `MemberDetailPanel`** non spécifié. `AgentFocusPanel` actuel
   (`agent-focus-panel.tsx`) n'a qu'une seule vue (de facto "Aperçu") — sans décision
   explicite, l'implémenteur pourrait faire ouvrir le panneau sur "Performance" (le plus
   récemment construit) au lieu de "Aperçu", cassant la continuité avec le comportement
   actuel. **Décision auto (P5 explicite, compatible avec l'existant) :** sous-onglet par
   défaut = **Aperçu**.
2. **Empty state = case cochée, pas une spec.** Le cherry-pick #6 de la Phase 1 accepte
   "empty states honnêtes" mais ne spécifie aucune copie. Design Principle #1 ("Empty
   states are features") : "aucune donnée" n'est pas un design. **Décision auto (P5
   explicite) — copie ajoutée au scope de base :** pour les 6 bureaux sans `ProjectBranch`,
   l'onglet Projets affiche une icône neutre + *"Ce bureau ne suit pas encore de projets
   structurés."* + une phrase de contexte différenciée par bureau (ex. Marketing :
   *"Le suivi de campagnes n'est pas encore modélisé comme projet ici."*) — **sans CTA
   factice** : il n'existe aujourd'hui aucune action réelle qu'Emilie puisse déclencher
   depuis cet onglet vide (TASTE DECISION #3 non tranchée), donc un bouton "Créer un
   projet" qui ne mènerait nulle part serait pire qu'absent. C'est une dérogation
   volontaire au réflexe "toujours une action primaire" du Design Principle #1, tracée ici
   plutôt que laissée à l'improvisation de l'implémenteur.

### Pass 4 — AI Slop Risk : 8/10 → 9/10

Déjà un point fort de la Phase 1 : 2 risques identifiés et neutralisés à la source (onglet
Mémoire sur données réelles `GET /library/topics`, sparkline Performance sur
`agent_logs`/`cost_monitor` réels plutôt qu'inventés). Contre-vérification via la checklist
dédiée AI-slop de ce skill :

- **Grille de cards générique ?** Non — vérifié dans `bureau-agents-section.tsx` et les
  deux `agent-card.tsx` : chaque carte est un point de clic réel vers un panneau détail
  (pas décoratif), avec statut/tâche/compétences propres à chaque agent — passe le litmus
  "la carte est-elle vraiment nécessaire ?" (oui).
- **Icônes en cercles colorés décoratifs ?** Non — les avatars sont fonctionnels
  (initiales + teinte par agent dans `console/agent-card.tsx:62-80`), pas de la déco.
- **Bordure gauche colorée, blobs, emoji-décor ?** Aucun trouvé dans le code existant.
- **Police système par défaut ?** Non — `font-title`/`font-body` custom déjà en usage
  (`shared/agent-card.tsx:103,115`), pas de repli `system-ui`.
- **Trouvé et à corriger — discipline d'échelle typographique :** le code existant utilise
  massivement `text-[10px]`/`text-[11px]` pour le contenu **meta** (labels, timestamps —
  `activity-feed.tsx:81`, `agent-card.tsx` footer), ce qui est défendable pour un outil
  dense. Le risque réel est que les **nouveaux** composants (titres de ticket sur le
  Kanban, noms de projet sur `ProjectGrid`) copient ces tailles minuscules pour du contenu
  **primaire** plutôt que meta. **Décision auto (P1 complétude, Design Hard Rule "no small
  low-contrast body text") — ajouté au scope de base :** titres de ticket (Kanban) et noms
  de projet (ProjectGrid) doivent être en `text-sm` (14px) minimum, les tailles
  `text-[10px]`/`text-[11px]` restant réservées au contenu meta (statut, timestamp,
  badge de branche) — codifie une convention aujourd'hui implicite pour qu'elle ne se
  perde pas dans les nouveaux composants.

Verdict global : risque AI-slop **faible**, cohérent avec un outil interne mono-utilisateur
réutilisant un système établi plutôt qu'improvisant une nouvelle identité visuelle.

### Pass 5 — Design System Alignment : 7/10 → 9/10

Pas de `DESIGN.md` formel (voir 0B) — calibré contre le vocabulaire de facto. Les noms
`DepartmentWorkspace`/`MissionsKanban`/`ProjectGrid`/`MemberDetailPanel` sont cohérents
avec `BureauPage`/`BureauPanel`/`AgentCard` (déjà validé Phase 1 Section 5).

**Gaps trouvés, non couverts par la Phase 1 :**
1. **Couleurs de colonnes Kanban non sourcées explicitement.** `STATUS_STYLES`/
   `TICKET_STATUSES` (`tickets.constants.ts:28-95`) définissent déjà copper/bleu/émeraude/
   zinc pour open/in_progress/done/wont_fix, utilisés par `/tickets` et
   `AppTicketsSection`. Sans directive explicite, `MissionsKanban` risque d'inventer sa
   propre palette de colonnes — recréant exactement la classe de bug FINDING-001 déjà
   corrigée une fois sur ce même repo (même concept, couleur/statut incohérent entre deux
   endroits de l'UI). **Décision auto (P4 DRY) — ajouté au scope de base :** `MissionsKanban`
   réutilise `STATUS_STYLES`/`TICKET_STATUSES` tels quels pour la théma­tique des colonnes.
2. **Aucune primitive `Tabs` accessible n'existe** dans `web/src/components/ui/` (vérifié,
   0 résultat). `DepartmentWorkspace` doit soit en construire une à la main (risque ARIA,
   voir Pass 6), soit introduire `@radix-ui/react-tabs` (primitive légère, largement
   éprouvée, sémantique ARIA tablist/tab/tabpanel + navigation clavier gratuites).
   **Décision auto (P3 pragmatique + "search before building" — layer 1 tried-and-true) :**
   utiliser Radix Tabs. **Amendement à noter pour l'eng review :** ceci introduit
   **une** nouvelle dépendance npm, ce qui nuance légèrement l'affirmation "zéro nouvelle
   dépendance" de la Phase 1 Section 3 (qui parlait du Kanban/drag-and-drop, pas des tabs) —
   à valider explicitement en eng review, pas glissé silencieusement.
3. **`MemberDetailPanel` onglet "Mémoire"** : aucun pattern visuel existant pour un
   catalogue de sujets/topics. **Décision auto (P4 DRY) :** réutiliser le pattern pill/badge
   déjà en place pour les `skills` (`shared/agent-card.tsx:117-126`) plutôt que d'inventer un
   nouveau composant visuel pour afficher les topics de mémoire — cohérence avec le
   vocabulaire existant plutôt qu'un 5e langage visuel.

### Pass 6 — Responsive & Accessibility : 5/10 → 8/10

La Phase 1 a déjà 3 bons acquis : Kanban en scroll horizontal snap sur mobile (Section 11),
raccourcis clavier tabs 1/2/3 (cherry-pick #5), et la remarque que les boutons flèches
(plutôt que drag-and-drop) sont un choix nativement plus accessible. Mais plusieurs points
concrets, vérifiables dans le code, manquent :

1. **Bug de troncature déjà présent, vérifié en code.** `web/src/components/shared/
   agent-card.tsx:103` (`<h3 className="font-title text-base font-semibold
   text-ivoire">{name}</h3>`) n'a **aucune classe `truncate`/`line-clamp`**, contrairement à
   `web/src/components/console/agent-card.tsx:84` qui a déjà `truncate` sur le nom. Avec un
   nom d'agent à 47 caractères (edge case explicitement demandé pour cette review), le
   `<h3>` de `shared/agent-card.tsx` déborderait ou pousserait le badge hors du flex
   `justify-between` (ligne 101). Comme l'Approche B (TASTE DECISION #1) unifie les deux
   composants, ce bug serait **hérité tel quel sur les 9 pages département** s'il n'est pas
   corrigé maintenant. **Décision auto (P1 complétude, fix vérifié à quelques minutes) —
   ajouté au scope de base :** l'`AgentCard` unifié doit porter `truncate` sur le champ nom,
   reprenant le précédent déjà établi dans `console/agent-card.tsx`.
2. **Cibles tactiles des boutons Kanban non spécifiées.** Design Principle 7 / règle mobile
   : 44px minimum. Rien dans le plan ne garantit que les boutons flèches d'avancement ne
   seront pas de petits boutons icône (24-32px), un piège classique. **Décision auto (P1
   complétude) :** boutons avancer/reculer du Kanban = zone de clic ≥44×44px sur tous les
   breakpoints (padding, pas juste la taille de l'icône).
3. **Sémantique ARIA du Kanban absente.** Le plan affirme (Section 11) que l'absence de
   drag-and-drop "s'aligne bien avec l'accessibilité" — c'est une assertion, pas une spec.
   **Décision auto (P1 complétude) — ajouté au scope de base :** les boutons avancer/reculer
   sont de vrais éléments `<button>` (pas des `<div onClick>`) avec anneau de focus visible
   (`:focus-visible`, déjà le pattern copper/bronze existant) ; chaque colonne Kanban porte
   un `aria-label` annonçant son nom + nombre de cartes ; chaque carte ticket a un nom
   accessible complet ("Ticket : {titre}, statut {X}, projet {Y}") plutôt qu'un div cliquable
   nu.
4. **Comportement mobile du rail `ActivityFeed` non spécifié.** Le Kanban a une réponse
   mobile actée ; le rail persistant n'en a aucune. **Décision auto (P4 DRY + P5 explicite) :**
   sous le breakpoint `lg:`, le rail devient une section repliable **sous** le contenu de
   l'onglet (pas caché entièrement — ça supprimerait silencieusement une fonctionnalité),
   repliée par défaut avec un badge "N nouveaux événements" pour préserver l'awareness sans
   coût de scroll permanent sur petit écran.
5. **Risque de contraste sur le texte meta des nouveaux composants.** Le code existant
   utilise abondamment des opacités réduites sur `titane` (`/40`, `/45`, `/50`, `/60`) pour
   le texte meta — un pattern qui a déjà causé FINDING-003 ("lisibilité titres widgets") sur
   cette même zone. **Décision auto (P1 complétude) :** tout nouveau texte meta introduit par
   `ProjectGrid`/`MissionsKanban`/les nouveaux sous-onglets doit repasser par `/design-review`
   après implémentation avant merge, avec un focus spécifique sur les tokens `/40`-`/50` —
   ajouté explicitement à l'étape de rollout (Section 9, déjà prévue) plutôt que supposé
   couvert.
6. **Sémantique tabs.** Voir Pass 5 point 2 — Radix Tabs résout à la fois l'alignement
   design-system ET la navigation clavier native/lecteurs d'écran de `DepartmentWorkspace`
   (pas seulement les raccourcis 1/2/3 déjà actés, qui sont une couche en plus, pas un
   substitut à la sémantique `role="tablist"`).

### Pass 7 — Unresolved Design Decisions

**Décisions auto-résolues par cette review (pas des TASTE DECISIONS — un défaut correct
existe, pas un vrai dilemme) :**

| Décision | Si différée, ce qui se passe | Résolution auto | Principe |
|---|---|---|---|
| Tab par défaut page département | Choix arbitraire dev, incohérent avec l'ordre Équipe→Projets→Missions documenté | Équipe | P5 |
| Sous-onglet par défaut `MemberDetailPanel` | Casse la continuité avec le panneau actuel à vue unique | Aperçu | P5 |
| Couleur colonnes Kanban | Nouvelle palette inventée, récidive de FINDING-001 | Réutiliser `STATUS_STYLES` | P4 |
| Progress `null` vs `0` sur `ProjectGrid` | 0% affiché mentirait sur l'état réel d'un projet | État neutre distinct | P1/P5 |
| Troncature nom agent (47 car.) | Layout cassé, hérité par les 9 pages via Approche B | `truncate`, précédent `console/agent-card.tsx` | P1 |
| Rail activité sur mobile | Fonctionnalité silencieusement supprimée ou layout cassé | Section repliable sous le contenu | P4/P5 |
| Primitive Tabs | ARIA cassée si codée à la main | Radix Tabs (1 dépendance, à noter en eng review) | P3 |

**TASTE DECISION #4 (nouvelle, surfacée par cette review design — à trancher par Emilie en
plus des 3 de la Phase 1) :** le rail `ActivityFeed` doit-il rester **toujours visible** sur
desktop (fidèle au mockup, ~280-320px de largeur fixe en permanence) ou **repliable même en
desktop** ? Ce n'est pas un simple gap — les deux options sont réellement défendables :
- **Pour "toujours visible"** : colle exactement au mockup "Agentic OS" fourni, cohérent
  avec l'intention "cockpit" de toute la refonte (tout voir d'un coup d'œil).
- **Pour "repliable"** : la largeur d'écran à 1280-1440px est un point de fragilité **déjà
  documenté sur ce repo précis** — `console-topbar.tsx:90-92` porte un commentaire explicite
  sur un `min-w` ajouté après que le titre de page ait été écrasé à 2-3 caractères à 1280px
  (FINDING-002). Ajouter un tab-workspace fixe + un rail fixe sur la même largeur d'écran
  recrée le même budget de largeur contraint qui a déjà cassé une fois. Un rail toujours-on
  n'est pas juste esthétique ici, c'est un risque de régression concret sur une largeur déjà
  fragile.
Auto-décision **non appliquée ici** — remontée telle quelle au gate humain, à trancher par
Emilie avant l'eng review, au même titre que les 3 décisions de la Phase 1.

### AI-Slop Risk Check (synthèse)

Risque **faible**, confirmé (voir Pass 4 pour le détail). Litmus checks appliqués : cartes
nécessaires ? Oui (interaction réelle, pas déco). Police custom ? Oui. Dégradés violets /
bordures gauche colorées / blobs décoratifs ? Aucun trouvé. Seul point d'action : discipline
d'échelle typographique sur le contenu primaire des nouveaux composants (Pass 4), déjà
ajoutée au scope de base.

### Ajouts actés au scope de base (fixes structurels de cette review design)

En plus des ajouts déjà actés par la Phase 1 (toasts d'erreur, skeleton transverse,
rollback optimistic update), cette review design ajoute au scope de base — pas à TODOS.md,
ce sont des omissions évidentes à effort proportionné (P2), pas des extensions :

1. Tab par défaut = Équipe ; sous-onglet par défaut `MemberDetailPanel` = Aperçu.
2. Ligne KPI (`kpisForPole`) reste au-dessus des tabs, non repliée dans Projets.
3. `ProjectGrid` distingue progress `null`/indisponible de `0` réel (état neutre dédié).
4. `MissionsKanban` réutilise `STATUS_STYLES`/`TICKET_STATUSES` — pas de nouvelle palette.
5. Radix Tabs (ou équivalent accessible) pour `DepartmentWorkspace` — 1 dépendance à noter
   en eng review, amendement à la Section 3 de la Phase 1.
6. `AgentCard` unifié (Approche B) porte `truncate` sur le nom — précédent déjà dans
   `console/agent-card.tsx:84`.
7. Boutons Kanban avancer/reculer : vrais `<button>`, ≥44×44px, `aria-label` par colonne,
   nom accessible par carte.
8. Rail `ActivityFeed` : repliable sous le contenu sur mobile, badge de compte si replié.
9. Titres de ticket / noms de projet en `text-sm` minimum (pas les tailles meta 10-11px).
10. Copie d'empty state spécifiée pour les 6 bureaux sans projet (Pass 3) — sans CTA
    factice.
11. Fetch Projets/Missions ne polle que si son tab est actif ; sous-onglets
    `MemberDetailPanel` en lazy-fetch au clic, pas au montage du panneau.
12. **Constat backend, hors remit design mais découvert pendant cette review, à transmettre
    tel quel à l'eng review :** `api/routers/core.py:177-183`
    (`update_ticket_status`) ne vérifie **pas** l'existence du ticket avant `db.update`,
    contrairement à `update_ticket` (lignes 164-169, mêmes fichier, qui fait
    `rows = db.select(...); if not rows: raise HTTPException(404)`). Ceci confirme et
    précise le CRITICAL GAP #1 déjà noté par la Phase 1 ("PATCH ticket 404, supprimé
    entre-temps") — le endpoint existe déjà (répond à l'incertitude "à confirmer" de la
    Phase 1 Section 3), mais son absence de garde-fou est la cause racine exacte du gap. Fix
    à 10 minutes, même pattern que la fonction juste au-dessus dans le même fichier.

### Implementation Tasks

Synthétisées à partir des findings ci-dessus. Chaque tâche dérive d'un finding précis.

- [ ] **T1 (P1, humain : ~15 min / CC : ~5 min)** — `shared/agent-card.tsx` — Ajouter
  `truncate` sur le `<h3>{name}</h3>` (ligne 103), précédent déjà dans `console/agent-card.tsx:84`.
  - Surfacé par : Pass 6, point 1. Fichiers : `web/src/components/shared/agent-card.tsx`.
  - Vérifier : rendu avec un nom de 47 caractères ne casse pas le layout flex du header de carte.
- [ ] **T2 (P1, humain : ~2h / CC : ~20 min)** — `DepartmentWorkspace` — Utiliser Radix Tabs
  (`role="tablist"`/`tab`/`tabpanel`) au lieu de boutons stylés à la main.
  - Surfacé par : Pass 5 point 2, Pass 6 point 6. Fichiers : nouveau
    `web/src/components/console/department-workspace.tsx` (ou équivalent), `package.json`.
  - Vérifier : navigation clavier native (flèches) + lecture correcte au lecteur d'écran.
- [ ] **T3 (P1, humain : ~1h / CC : ~15 min)** — `MissionsKanban` — Réutiliser
  `STATUS_STYLES`/`TICKET_STATUSES` (`tickets.constants.ts`) pour les couleurs de colonnes.
  - Surfacé par : Pass 5 point 1. Fichiers : nouveau `MissionsKanban`, `tickets.constants.ts`.
  - Vérifier : même statut = même couleur entre `/tickets` (liste) et le nouveau Kanban.
- [ ] **T4 (P1, humain : ~1h / CC : ~20 min)** — Boutons Kanban : vrais `<button>`,
  ≥44×44px, `aria-label` par colonne + carte.
  - Surfacé par : Pass 6 points 2-3. Fichiers : nouveau `MissionsKanban`.
  - Vérifier : navigation Tab + Enter/Espace sans souris, focus visible.
- [ ] **T5 (P2, humain : ~30 min / CC : ~10 min)** — `ProjectGrid` : état neutre distinct
  pour `progress` null/indisponible vs `0` réel.
  - Surfacé par : Pass 2 point 1. Fichiers : nouveau `ProjectGrid`.
  - Vérifier : projet avec heuristique `_branch_progress` en échec affiche "—", pas "0%".
- [ ] **T6 (P2, humain : ~30 min / CC : ~10 min)** — Tab par défaut = Équipe ; sous-onglet
  `MemberDetailPanel` par défaut = Aperçu.
  - Surfacé par : Pass 1, Pass 3. Fichiers : `DepartmentWorkspace`, `MemberDetailPanel`.
  - Vérifier : première visite d'une page département ouvre sur Équipe sans état persisté.
- [ ] **T7 (P2, humain : ~45 min / CC : ~15 min)** — Rail `ActivityFeed` : section repliable
  sous le contenu des tabs en `<lg:`, badge de compte si replié.
  - Surfacé par : Pass 6 point 4. Fichiers : layout `BureauPage`/`DepartmentWorkspace`.
  - Vérifier : à 375px, le rail n'est ni caché silencieusement ni cassé visuellement.
- [ ] **T8 (P1, humain : ~15 min / CC : ~10 min)** — Backend : ajouter la vérification
  d'existence (404) à `update_ticket_status`, même pattern que `update_ticket`.
  - Surfacé par : Ajouts actés #12. Fichiers : `api/routers/core.py:177-183`.
  - Vérifier : `PATCH /tickets/{id}/status` sur un id inexistant renvoie 404, pas un succès
    silencieux.
- [ ] **T9 (P3, follow-up)** — Copie d'empty state par bureau pour l'onglet Projets (6/9
  bureaux) — texte différencié par bureau, pas un message générique unique.
  - Surfacé par : Pass 3. Fichiers : nouveau `ProjectGrid` (contenu, pas composant).
  - Vérifier : revue de copie avec Emilie avant merge (contenu produit, pas juste code).

_Aucune tâche générée pour Pass 4 au-delà de la discipline typographique (déjà T-adjacent,
couverte implicitement par T3/T5 au moment de styliser le contenu primaire) — pas de tâche
dédiée pour éviter la duplication._

### Résumé de complétion

```
+====================================================================+
|         DESIGN PLAN REVIEW — COMPLETION SUMMARY                    |
+====================================================================+
| Audit système        | DESIGN.md absent (non bloquant) ; primitive |
|                       | Tabs accessible absente du repo ; bug de    |
|                       | troncature vérifié dans shared/agent-card   |
| Step 0                | 6/10 initial — bonnes fondations Phase 1,   |
|                       | trous concrets en storyboard/a11y/wireframe |
| Pass 1  (Info Arch)   | 6/10 → 9/10                                 |
| Pass 2  (États)       | 7/10 → 9/10                                 |
| Pass 3  (Parcours)    | 4/10 → 8/10                                 |
| Pass 4  (AI Slop)     | 8/10 → 9/10                                 |
| Pass 5  (Design Sys)  | 7/10 → 9/10                                 |
| Pass 6  (Responsive)  | 5/10 → 8/10                                 |
| Pass 7  (Décisions)   | 7 auto-résolues, 1 nouvelle TASTE DECISION  |
+--------------------------------------------------------------------+
| NOT in scope          | Aucun nouvel item (déjà couvert Phase 1) ;  |
|                       | audit a11y automatisé (axe/pa11y) et        |
|                       | indicateur de statut agent "figé" reportés  |
|                       | à TODOS.md (voir ci-dessous)                |
| Ce qui existe déjà    | 6 leviers supplémentaires cartographiés     |
|                       | (0C) au-delà de la carte Phase 1            |
| TODOS.md              | 2 items ajoutés (append, pas d'écrasement)  |
| Implementation Tasks  | 9 tâches actionnables (8 scope de base +    |
|                       | 1 follow-up P3)                             |
| Decisions ajoutées au | 12 (voir "Ajouts actés au scope de base")   |
| plan                  |                                              |
| Decisions différées   | 1 nouvelle TASTE DECISION (#4, rail mobile) |
| Overall design score  | 6/10 → 8.5/10                               |
+====================================================================+
```

**Note sur le 8.5/10 (pas 10) :** cohérent avec le skill — "Plan is design-complete" à
partir de 8+, mais un plan de review ne peut jamais atteindre 10 avant implémentation réelle
(contraste effectif, navigation clavier testée en vrai, copie d'empty state validée avec
Emilie). `/design-review` (audit visuel post-implémentation) reste recommandé une fois le
code écrit — déjà noté par la Phase 1, confirmé ici.

### Décisions non résolues (gate humain final)

4 TASTE DECISIONS au total à trancher par Emilie avant le lancement de l'implémentation
(les 3 de la Phase 1 + 1 nouvelle ci-dessus) :
1. Unifier les deux `AgentCard` maintenant (Approche B) vs coexistence temporaire (Phase 1).
2. Kanban 3 colonnes relabelées vs vrai statut "En revue" backend (Phase 1).
3. Empty state honnête vs invention d'un concept "projet" pour 6 bureaux (Phase 1).
4. **Rail `ActivityFeed` toujours visible sur desktop vs repliable** — nouvelle, cf. Pass 7
   ci-dessus, motivée par la fragilité de largeur déjà documentée à 1280px (FINDING-002).

Aucune n'est silencieusement résolue ou perdue — les 4 sont documentées ici et dans
`TODOS.md`/la section TASTE DECISIONS de la Phase 1 pour le gate humain final.

---

## Phase 3 — Eng Review

**Mode d'exécution :** `/plan-eng-review` via `/autoplan`, run automatisé — pas
d'`AskUserQuestion`, chaque gap est auto-décidé selon les 6 principes, **P5 Explicite >
clever et P3 Pragmatisme dominants** en cas de conflit (consigne explicite pour cette
phase). Cible : le code réel a été lu directement pour cette review (pas seulement le
plan) — `bureau-page.tsx`, `console-provider.tsx`, `departments.ts`, `api.ts`, `types.ts`,
`api/routers/core.py`, les deux `agent-card.tsx`, `agent-focus-panel.tsx`,
`bureau-agents-section.tsx`, `use-agent-statuses.ts`, `app-tickets-section.tsx`,
`app/page.tsx`, `console-shell.tsx`, `console-topbar.tsx`, `console-sidebar.tsx`,
`activity-feed.tsx`, `tickets.constants.ts`, `tickets.ts`, `rd-page-content.tsx` (précédent
tabs), `store/coo-store.ts` + `store/quick-capture-store.ts` (précédent Zustand),
`playwright.config.ts` + `e2e/*.spec.ts`, `tests/conftest.py` + `tests/test_api_routes_phase4.py`.
Plusieurs affirmations des Phases 1/2 sont **corrigées** ci-dessous sur la base du code
réellement lu, pas seulement confirmées.

### Step 0 — Scope Challenge (Eng)

**Scope confirmé bien dimensionné.** Les Phases 1 et 2 ont déjà fait remonter au scope de
base les vrais trous (doublon `AgentCard`, gap PATCH ticket 404, 3 CRITICAL GAPS Kanban,
hook `useDepartmentData`) plutôt que de les glisser en `TODOS.md`. Rien à retirer ni à
ajouter au périmètre — cette review durcit l'existant (architecture, edge cases, tests,
perf, sécurité), elle ne le rouvre pas.

**Deux corrections factuelles au dossier, vérifiées en code, qui changent le coût réel
de deux décisions déjà actées (pas leur bien-fondé) :**

1. **Playwright est déjà configuré** (`web/playwright.config.ts`, script `test:e2e`,
   6 specs dans `web/e2e/`) — contrairement à l'hypothèse non vérifiée de la Phase 1
   Section 6 ("pas de Playwright configuré... à confirmer, hors scope de vérifier ici").
   Mieux : `web/e2e/rd-tabs.spec.ts` est un **précédent direct** pour tester
   `DepartmentWorkspace` (switch d'onglets sur une page bureau, memes assertions
   `getByRole("button", ...)`), et `web/e2e/page-audit.spec.ts` **visite déjà les 9 pages
   département** (`/app /gaming /robo /marketing /finances /rd /analytics /secretary /hub`
   + `/ceo /brand`) et échoue si une page crashe ou lève une erreur JS. C'est un filet de
   régression déjà en place, gratuit pour ce chantier — il suffit de ne pas le casser. Ceci
   change le calibrage de la Section 3 ci-dessous : l'infra E2E n'est pas un risque
   d'investissement, c'est une capacité existante à étendre. (Le TODO-005 déjà écrit dans
   `TODOS.md` avait noté ce point comme "à vérifier" avec un effort humain "M" — laissé tel
   quel par consigne de non-écrasement, mais sa vraie base d'effort est plus basse ; voir
   Section 3.)
2. **Radix Tabs est bien absent du repo**, confirmé (`grep "@radix-ui" web/package.json`
   → 0 résultat) — la Phase 2 avait raison, ceci n'est pas une correction mais une
   **confirmation** : la dépendance à ajouter (Section 5 Phase 2, amendement Section 3
   Phase 1) est réelle et unique, pas déjà satisfaite ailleurs dans le repo.

**Résolution de la question tab-persistence (mécanique, pas un vrai choix de goût) :**

Question posée par la Design Review indépendante : l'onglet actif (Équipe/Projets/
Missions) doit-il se souvenir de sa dernière position par département quand on navigue
entre départements via la sidebar, ou repartir à zéro (Équipe) à chaque fois ? Signalé
comme high-severity si non traité (9 clics/jour si ça reset).

**Réponse : oui, ça doit persister — et le mécanisme est un nouveau petit store Zustand,
pas une query param d'URL ni du state de composant.** Raisonnement, ancré dans le code
existant :

- **State de composant seul ne marche pas.** Chaque département (`/app`, `/gaming`, ...)
  est une **route Next.js distincte** (`web/src/app/{dept}/page.tsx`), pas une seule page
  paramétrée. Naviguer de `/app` vers `/gaming` démonte l'arbre de composants de `/app` —
  un `useState` dans `DepartmentWorkspace` repart donc à `undefined`/défaut à chaque retour
  sur un département déjà visité. C'est précisément le bug que le reviewer design a
  identifié.
- **Query param d'URL (`/app?tab=missions`) est rejeté, pas juste "moins bien".** Le
  précédent existe déjà dans le repo — `web/src/app/rd/rd-page-content.tsx:55-71`
  (`useSearchParams().get("tab")` + `useState(resolveInitialTab)`) — mais ce précédent
  résout des onglets **à l'intérieur d'une seule route** (`/rd`), pas la mémoire
  **inter-routes** qu'il faut ici. Pour porter ce pattern à 9 routes distinctes, les liens
  statiques de la sidebar (`CONSOLE_POLES[i].href`, `web/src/lib/console/departments.ts:38-170`,
  consommés tels quels par `console-sidebar.tsx:166-196` en `<Link href={pole.href}>`)
  devraient être réécrits dynamiquement par département pour injecter le bon `?tab=...` —
  ce qui oblige la sidebar à lire l'état mémorisé **depuis un store de toute façon**. La
  query param n'élimine donc pas le besoin d'un store, elle ajoute une couche de
  sérialisation URL par-dessus sans bénéfice réel ici (personne ne partage/bookmark un
  onglet département précis — utilisatrice unique, un seul poste). Rejeté par P5 (explicite
  > clever : la solution la plus directe gagne) et P3 (pragmatique : ne pas résoudre un
  besoin de partage de lien qui n'existe pas).
- **Store Zustand est le pattern déjà établi pour exactement ce besoin.**
  `web/src/store/coo-store.ts` et `web/src/store/quick-capture-store.ts` existent déjà
  pour du state UI éphémère partagé entre composants sans prop-drilling, sans passer par
  `ConsoleProvider` (qui, lui, recalcule sa `value` mémoïsée à chaque poll 12s —
  `console-provider.tsx:155-189` — donc y ajouter du state UI pur créerait des re-renders
  non liés au vrai besoin, un souci déjà noté Section 7 de la Phase 1). Un store séparé,
  souscrit par sélecteur Zustand (donc pas de re-render pour les départements non affichés),
  est strictement meilleur.

**Spec concrète (nouveau fichier `web/src/store/department-workspace-store.ts`, même
forme que `quick-capture-store.ts`) :**

```ts
type WorkspaceTab = "equipe" | "projets" | "missions";

interface DepartmentWorkspaceStore {
  activeTabByDept: Partial<Record<string, WorkspaceTab>>;
  setActiveTab: (deptId: string, tab: WorkspaceTab) => void;
}

// activeTabByDept[deptId] ?? "equipe" au point de lecture (défaut Équipe,
// cohérent avec la décision Phase 2 Pass 1/7 pour la toute première visite)
```

Persistance : **sessionStorage via le middleware `persist` de Zustand** (10 lignes,
trivial, P2 — sous le seuil 1 jour, ajouté au scope de base directement plutôt que déféré) —
même logique de survie-au-refresh que le précédent déjà dans le repo
(`rd-page-content.tsx:78-79`, `sessionStorage.getItem("rd_agents_open")`), mais pas de
`localStorage` : pas besoin de survivre au-delà de la session navigateur, garde le
comportement "retour à Équipe" propre après un vrai redémarrage plutôt que de la dette
d'état qui traîne indéfiniment.

### Section 1 — Architecture Review

**Diagramme de composition + propriété du state (affine le diagramme Phase 1 avec la
localisation exacte du state, pas seulement l'arbre de composants) :**

```
ConsoleShell (existant, inchangé)
 │  <main> ne rend que {children} tel quel (console-shell.tsx:51-59) — confirmé : aucun
 │  rail persistant n'existe à ce niveau aujourd'hui. Bon call architectural de la Phase 1
 │  de placer ActivityRail DANS BureauPage plutôt qu'ici : ConsoleShell enveloppe aussi
 │  /hub, /agents, /activity — un rail ici dupliquerait l'activité déjà affichée en natif
 │  sur ces 3 pages.
 │
 ├─ ConsoleSidebar (existant — CONSOLE_POLES statique, hrefs figés, departments.ts:38-170)
 ├─ ConsoleTopbar (existant, inchangé scope de base)
 └─ <main> BureauPage (existant, 17 pages)
      ├─ DepartmentHeader (existant, inchangé)
      ├─ [NOUVEAU] DepartmentWorkspace — monté sur 9/11 pôles seulement
      │    │  state onglet actif ──▶ department-workspace-store (NOUVEAU, Zustand,
      │    │                          sessionStorage-persisted) — PAS dans ConsoleProvider
      │    │
      │    ├─ Radix Tabs (Équipe | Projets | Missions), défaut = Équipe (1ère visite)
      │    ├─ [Onglet Équipe]
      │    │    └─ BureauAgentsSection (existant, rebranché Approche B)
      │    │         data: nom/rôle/spécialité/utilization/model ◄── useConsoleData()
      │    │                                                        .departments[i].agents
      │    │         data: status (idle/working/waiting/error)   ◄── useConsoleData()
      │    │                                                        .liveAgents[id] (BRUT,
      │    │                                                        PAS ConsoleAgent.status
      │    │                                                        — voir finding ARCH-1)
      │    │         └─ AgentCard unifié (extension shared/agent-card.tsx)
      │    │              └─ onClick → [NOUVEAU] MemberDetailPanel
      │    │                   (extension de AgentFocusPanel existant, 143L)
      │    │                   state: sous-onglet actif ── useState local (PAS un store —
      │    │                          se referme au clic X, ré-ouverture = Aperçu par
      │    │                          défaut, rien à faire persister entre navigations)
      │    │                   ├─ Aperçu (existant, inchangé)
      │    │                   ├─ Compétences (nouveau, lazy-fetch au 1er clic)
      │    │                   ├─ Performance (nouveau, lazy-fetch, agent_logs+cost_monitor)
      │    │                   └─ Mémoire (nouveau, lazy-fetch, GET /library/topics)
      │    ├─ [Onglet Projets]
      │    │    └─ [NOUVEAU] ProjectGrid ◄── useDepartmentData(bureau).projects
      │    │         fetch actif SEULEMENT si cet onglet est monté/actif (pas de poll
      │    │         en tâche de fond pour un onglet non affiché — Phase 2 Pass 2)
      │    └─ [Onglet Missions]
      │         └─ [NOUVEAU] MissionsKanban ◄── useDepartmentData(bureau).tickets
      │              PATCH via lib/tickets.ts::updateTicket() → /tickets/{id}/status
      │              (endpoint existant, fix 404 requis — Section 2)
      └─ [NOUVEAU] ActivityRail = ActivityFeed existant (mode compact), repositionné
           ◄── useConsoleData().activityFeed (poll 12s, INDÉPENDANT du tab actif —
               le rail n'est pas un tab, il tourne toujours)
```

**Finding ARCH-1 (nouveau, non détecté par les Phases 1/2) — un risque de régression que
l'Approche B introduirait si implémentée naïvement, exactement la classe de bug que
l'Approche B est censée éliminer (confiance 9/10, vérifié en code) :**

`ConsoleAgent.status` (`web/src/lib/console/types.ts:3,10` — type `ConsoleAgentStatus =
"active"|"thinking"|"idle"|"review"`) est une projection **avec perte** du statut brut,
calculée par `mapStatus()` (`departments.ts:172-183` : `working→active`,
`waiting→thinking`, `error→review`, sinon `idle`). `AgentFocusPanel`
(`web/src/components/openroom/agent-focus-panel.tsx:66-83`) — que ce plan étend en
`MemberDetailPanel` sans le réécrire — consomme, lui, le statut **brut** `AgentStatusKind`
(`"idle"|"working"|"waiting"|"error"`, `openroom-api.ts:3`) directement via
`agentStatuses[focused.id]` (`bureau-agents-section.tsx:78`). Aujourd'hui les deux
consomment la même donnée brute (`useAgentStatuses()` renvoie
`consoleData?.liveAgents ?? localStatuses` — `use-agent-statuses.ts:51` — donc, dans le
shell, littéralement le même objet que `useConsoleData().liveAgents`) : carte et panneau
sont d'accord.

**Si l'AgentCard unifié lit son prop `status` depuis `ConsoleAgent.status` (mappé) au lieu
du statut brut**, un agent en `waiting` afficherait "Réflexion" sur la carte unifiée mais
"En attente..." dans le panneau ouvert en cliquant sur cette même carte
(`agent-focus-panel.tsx:76-83`) — deux libellés différents pour le même état réel, sur
deux composants directement liés par un clic. C'est la même classe de bug que
FINDING-001 (statut contradictoire topbar/sidebar) que la Phase 1 cite justement comme la
raison de choisir l'Approche B — sauf que ce chemin précis la réintroduirait plutôt que de
la corriger.

**Décision auto (P5 explicite, P4 DRY) — précise/corrige l'implémentation de l'Approche B,
ne la remet pas en cause :** `shared/agent-card.tsx`'s prop `status` **reste typé
`AgentStatusKind`** (inchangé — pas de nouveau vocabulaire à introduire). `utilization` et
`model` (nouveaux props optionnels) viennent de `useConsoleData().departments[i].agents`,
mais **`status` et `currentTask` continuent de venir de `useConsoleData().liveAgents[id]`
brut** (déjà disponible dans le contexte, zéro fetch supplémentaire) — pas de
`ConsoleAgent.status` mappé, pas de fonction d'adaptation à écrire. `console/agent-card.tsx`
(seul consommateur `/agents`, non touché par ce plan) garde sa propre projection
`ConsoleAgentStatus` pour son usage roster différent — légitimement distinct, pas un
doublon à résoudre ici (cohérent avec la décision déjà actée de ne pas y toucher).

**Finding ARCH-2 (précision de scope, confiance 9/10) — le sous-item "Brand = 0 agent" du
cherry-pick #6 n'a aucun point d'attache dans les fichiers que ce plan touche.**
`agentsForPole()`/`buildConsoleDepartments()` (`departments.ts`) ne sont PAS consommés par
`/brand` (`app/brand/page.tsx` rend `BrandView`, pas `BureauAgentsSection` — confirmé Phase 1
0B) — donc `DepartmentWorkspace`/`BureauAgentsSection`/`AgentCard` ne rendent jamais l'état
"Brand a 0 agent". Vérifié où ce 0 est réellement visible aujourd'hui :
`dashboard-view.tsx:347-348` (`/hub`, mini-cartes par pôle, `load = agents.reduce(...) /
Math.max(agents.length, 1)` — division déjà protégée, pas de crash, juste "0%" affiché pour
Brand). **Décision auto (P5) :** retirer ce sous-item spécifique du scope de base de
`DepartmentWorkspace` (il n'y a rien à corriger dans les fichiers que ce plan touche) ; si
Emilie veut un traitement plus explicite du "0%" de Brand sur `/hub`, c'est un changement
d'une ligne hors périmètre de cette refonte, à noter dans TODOS.md seulement si elle le
demande (pas ajouté ici — non prioritaire, cosmétique, non cassé). La partie "6/9 bureaux
sans projet" du même cherry-pick #6 reste, elle, entièrement dans le blast radius
(`ProjectGrid`, onglet Projets) — inchangée.

**Finding ARCH-3 (nouvelle duplication DRY, confiance 8/10) — une 3e implémentation
indépendante du même besoin "projets+tickets filtrés par bureau" existe, non vue par les
Phases 1/2 qui n'avaient regardé que `app-tickets-section.tsx`.** `web/src/app/app/page.tsx:26-46`
(`loadProjects`, dans `AppPolePage`) refait, **indépendamment** du pattern déjà signalé dans
`app-tickets-section.tsx:33-54`, son propre `fetchProjects()` + filtre `branch === "app"` +
`fetchTickets(project.id)` par projet pour compter les tickets actifs. C'est une 3e
implémentation du même besoin (après `AppTicketsSection` et le futur `ProjectGrid`/
`MissionsKanban`). Puisque l'intention du plan est que `DepartmentWorkspace` **remplace**
la composition manuelle actuelle de `/app/page.tsx` (agents → tickets → projets → console
empilés), le rollout (Phase 1 Section 9) doit explicitement supprimer ce bloc
(`app/page.tsx:16-46,91-135`) en même temps que `AppTicketsSection`, pas seulement
"si totalement remplacé" (formulation conditionnelle actuelle du rough plan) — **rendu
inconditionnel ici** : le hook unique `useDepartmentData(bureau)` doit être la seule
source de projets/tickets sur les 9 pages, sans laquelle la nouvelle grille Projets et
l'ancien bloc `/app/page.tsx` afficheraient deux fois la même info avec deux logiques de
fetch différentes.

**Scénario de panne production (nouveau, spécifique au store de tab) :** `sessionStorage`
plein/désactivé (navigation privée stricte, quota dépassé) → le `persist` middleware de
Zustand échoue silencieusement à l'écriture dans certains navigateurs. **Dégradation
attendue et acceptable :** le store retombe en mémoire pure pour la session (perte de la
persistance au refresh uniquement, pas de crash — `zustand/persist` catch déjà ses erreurs
de storage en interne). Rien à coder en plus, à vérifier une fois en QA manuelle après
implémentation (pas un test automatisé dédié, effort disproportionné pour ce risque mineur).

**Couplage, SPOF, sécurité architecture :** rien à ajouter aux constats déjà justes de la
Phase 1 (couplage `ConsoleProvider` déjà unique, `hubFetch` point unique existant, aucun
SPOF nouveau).

### Section 2 — Code Quality Review

**DRY violations (agressif, comme demandé par la méthodologie) :**

1. **Doublon `AgentCard`** — déjà traité en 0C-bis/Section 1 Phase 1 (Approche B,
   TASTE DECISION #1). Fix de troncature exact, vérifié en code :
   - `web/src/components/shared/agent-card.tsx:103` :
     `<h3 className="font-title text-base font-semibold text-ivoire">{name}</h3>`
     → ajouter `truncate` : `className="truncate font-title text-base font-semibold text-ivoire"`.
   - Précédent exact déjà dans le repo : `web/src/components/console/agent-card.tsx:84` :
     `<h4 className="font-semibold text-ivoire truncate tracking-wide">`.
   - Vérifié : le conteneur parent est `flex items-start justify-between gap-2`
     (`shared/agent-card.tsx:101`) avec un `badge` optionnel à droite (`shrink-0`) — sans
     `truncate` + `min-w-0` sur le conteneur du nom (`shared/agent-card.tsx:100`,
     `<div className="min-w-0 flex-1">` — déjà présent, bon), un nom à 47 caractères pousse
     le badge hors du flex. `min-w-0` est déjà là ; il ne manque que `truncate` sur le
     `<h3>` lui-même. Fix à une ligne, déjà identifié T1 en Phase 2 — confirmé correct ici.
   - Fix status/vocabulaire : voir Finding ARCH-1 ci-dessus (Section 1) — pas de fonction
     d'adaptation à écrire, juste router le bon champ (`liveAgents` brut, pas
     `ConsoleAgent.status`).

2. **Fetch dupliqué "projets+tickets par bureau"** — 3 implémentations indépendantes
   confirmées (Finding ARCH-3) : `app-tickets-section.tsx:33-54`, `app/page.tsx:26-46`, et
   le futur `ProjectGrid`/`MissionsKanban` s'il était écrit en 4e version indépendante.
   **Décision auto (P4 DRY, déjà actée en principe Phase 1 Section 5, précisée ici avec les
   fichiers exacts à supprimer) :** `useDepartmentData(bureau)` unique, et suppression
   inconditionnelle de `app-tickets-section.tsx` + du bloc `loadProjects`/rendu Projets de
   `app/page.tsx:16-46,91-135` dans le même PR que l'introduction de `DepartmentWorkspace`
   (pas laissé "si totalement remplacé" — ça l'est, par construction du scope de base).

**Fix du gap ticket 404 (CRITICAL GAP #1 du registre, confirmé en code, confiance 10/10) :**

`api/routers/core.py:177-183` :
```python
@router.patch("/tickets/{ticket_id}/status")
def update_ticket_status(ticket_id: str, status: str) -> dict[str, Any]:
    allowed = {"open", "in_progress", "done", "wont_fix"}
    if status not in allowed:
        raise HTTPException(status_code=400, detail=f"status must be one of {allowed}")
    db = get_supabase()
    return db.update("tickets", ticket_id, {"status": status})
```
ne vérifie pas l'existence du ticket, contrairement à `update_ticket` juste au-dessus
(`api/routers/core.py:164-174`) qui fait déjà exactement le garde-fou attendu :
```python
@router.patch("/tickets/{ticket_id}")
def update_ticket(ticket_id: str, body: TicketUpdate) -> dict[str, Any]:
    db = get_supabase()
    rows = db.select("tickets", filters={"id": ticket_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ...
```
**Fix (même pattern, à copier tel quel) :**
```python
@router.patch("/tickets/{ticket_id}/status")
def update_ticket_status(ticket_id: str, status: str) -> dict[str, Any]:
    allowed = {"open", "in_progress", "done", "wont_fix"}
    if status not in allowed:
        raise HTTPException(status_code=400, detail=f"status must be one of {allowed}")
    db = get_supabase()
    rows = db.select("tickets", filters={"id": ticket_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return db.update("tickets", ticket_id, {"status": status})
```
Confirme et clôt CRITICAL GAP #1 du Failure Modes Registry (Phase 1). Déjà spécifié T8 en
Phase 2 — vérifié correct ici, aucune modification nécessaire à cette tâche.

**Simplification pour CRITICAL GAP #2 (409/422 conflit) — le plan sur-spécifie un cas qui
n'existe pas encore côté backend (P5 explicite, P3 pragmatique) :** `update_ticket_status`
n'a aucune logique de concurrence optimiste (pas de champ `version`/`updated_at` vérifié
avant écriture) — il ne peut donc **structurellement pas** renvoyer un 409 aujourd'hui,
seulement 400 (statut invalide) ou, après le fix ci-dessus, 404 (ticket supprimé). **Décision
auto :** `MissionsKanban#onAdvance` n'a pas besoin d'une branche 409/422 dédiée pour la V1 —
`hubFetch` (`hub-fetch.ts:29-32`) lève déjà une erreur générique sur tout statut non-2xx ;
un seul `catch` générique → rollback optimistic update + `toast.error` couvre 404 actuel et
tout futur code d'erreur sans branche spécifique à deviner. Rien à construire pour un
statut que le backend ne peut pas encore émettre — le CRITICAL GAP #2 se ferme avec le même
mécanisme générique que le #1, pas un mécanisme séparé.

**Fix du double-clic (CRITICAL GAP #3) :** `MissionsKanban` doit garder un état local
`pendingTicketId: string | null` — bouton flèche `disabled` tant que
`pendingTicketId === ticket.id`, remis à `null` dans le `finally` du `catch`/`then` du PATCH.
Pattern standard, rien de spécifique au repo à réutiliser ici (pas de précédent existant
pour du debounce de mutation dans le code actuel — première fois que ce plan introduit une
mutation utilisateur directe sur cette zone).

**Naming, sur/sous-ingénierie :** rien à ajouter aux constats déjà justes des Phases 1/2.

### Section 3 — Test Review

**Correction de calibrage (Step 0) :** l'infra E2E existe déjà (Playwright configuré,
6 specs, dont un précédent tabs direct). Le seul test Vitest existant
(`web/src/__tests__/assistant-chat.test.tsx`) est un test **★ smoke** (il importe le module
et vérifie que l'export existe — il ne rend jamais le composant, cf. lignes 21-26 du
fichier) — la zone `console/*`/`shared/bureau-*` a donc bien **zéro test de rendu réel**,
confirmant le constat Phase 1, mais avec les deux infra de test (Vitest+RTL, Playwright)
déjà entièrement câblées et fonctionnelles (`web/vitest.config.ts`,
`web/playwright.config.ts` avec `webServer` FastAPI+Next déjà configuré) — le coût
d'écriture des tests est donc uniquement le test lui-même, pas l'infra.

**Diagramme de couverture (chaque flux demandé + les flux déjà actés par les Phases 1/2,
tous tracés jusqu'au fichier de test à créer) :**

```
CODE PATHS                                          TYPE       EXISTE ?   FICHIER À CRÉER
──────────────────────────────────────────────────────────────────────────────────────────
[+] department-workspace-store.ts (NOUVEAU)
  ├─ setActiveTab(dept, tab) → persist sessionStorage  unit       [GAP]    store.test.ts
  ├─ lecture avec défaut "equipe" si jamais set         unit       [GAP]    (idem)
  └─ [→E2E] switch onglet PUIS navigation département   E2E        [GAP]    department-workspace-
       PUIS retour — onglet mémorisé, pas reseté                            persistence.spec.ts
                                                                             (précédent direct :
                                                                             e2e/rd-tabs.spec.ts)

[+] DepartmentWorkspace (NOUVEAU)
  ├─ [★★★] Rendu Radix Tabs, défaut = Équipe            E2E        [GAP]    department-workspace-
  ├─ [★★★] Clic Projets/Missions → contenu swap                              tabs.spec.ts (calque
  │        (régression connue : "bouton actif mais                          direct de rd-tabs.spec.ts,
  │         panneau ne monte pas" — déjà arrivé une                         même fichier commenté
  │         fois sur /rd selon le commentaire de                            "régressé une fois")
  │         rd-tabs.spec.ts:4-7)
  ├─ [GAP]  Raccourcis clavier 1/2/3 et ←/→              unit/E2E   [GAP]    department-workspace-
  └─ [GAP]  Navigation clavier tablist (Tab/flèches,     E2E        [GAP]    tabs.spec.ts (a11y
             ARIA géré par Radix — vérifier le résultat)                    assertions incluses)

[+] AgentCard unifié (extension shared/agent-card.tsx)
  ├─ [★★★] Nom 47 caractères → classe truncate présente  unit       [GAP]    agent-card.test.tsx
  ├─ [★★  ] status brut (liveAgents) affiché, PAS         unit       [GAP]    (idem — couvre
  │         ConsoleAgent.status mappé (Finding ARCH-1)                       directement ARCH-1)
  └─ [★★  ] utilization/model rendus quand fournis         unit       [GAP]    (idem)

[+] MemberDetailPanel (extension AgentFocusPanel)
  ├─ [★★  ] Sous-onglet par défaut = Aperçu                unit       [GAP]    member-detail-panel.
  ├─ [★★★] Clic Compétences/Performance/Mémoire → fetch    unit       [GAP]    test.tsx
  │        déclenché au clic, PAS au montage du panneau
  │        (lazy — décision Phase 2 Pass 2 point 2)
  ├─ [GAP]  Mémoire : GET /library/topics échoue/vide →    unit       [GAP]    (idem)
  │         empty state, pas de crash
  └─ [GAP]  Performance : agent_logs vide (agent neuf) →   unit       [GAP]    (idem)
             empty state "Pas encore d'historique"

[+] ProjectGrid (NOUVEAU)
  ├─ [★★★] 6/9 bureaux sans ProjectBranch → copie          unit       [GAP]    project-grid.test.tsx
  │        spécifique par bureau (pas générique,                            (couvre cherry-pick #6
  │        Design Pass 3 point 2), sans CTA factice                         moitié "6 bureaux")
  ├─ [★★  ] progress null/indisponible → état neutre "—",  unit       [GAP]    (idem — couvre
  │        PAS "0%" (Design Pass 2 point 1)                                  directement le fix T5)
  ├─ [GAP]  Project.branch corrompu (valeur inconnue) →     unit       [GAP]    (idem — test chaos
  │         filtré/loggé, pas de crash (chaos test Phase 1                  explicitement demandé
  │         Section 6)                                                      par Phase 1)
  └─ [★★  ] fetchProjects() réseau échoue → toast.error +   unit       [GAP]    (idem)
             tableau vide (pas de state fantôme)

[+] MissionsKanban (NOUVEAU) — zone la plus à risque, cf. CRITICAL GAPS
  ├─ [★★★] [→E2E] Avancer un ticket (bouton →) → colonne   E2E        [GAP]    missions-kanban.spec.ts
  │        change, PATCH part une seule fois
  ├─ [★★★] Double-clic rapide (<100ms) même bouton →        unit       [GAP]    missions-kanban.
  │        UNE SEULE requête PATCH (CRITICAL GAP #3)                         test.tsx (mock fetch,
  │                                                                          assert call count===1)
  ├─ [★★★] PATCH renvoie 404 (ticket supprimé entre-temps) → unit       [GAP]    (idem — mock hubFetch
  │        rollback visuel + toast, carte retirée                           rejetant, CRITICAL GAP #1)
  ├─ [★★  ] PATCH échoue (réseau/générique) → rollback +     unit       [GAP]    (idem — couvre
  │        toast (CRITICAL GAP #2, mécanisme générique)                     "test qui rassure à 2h
  │                                                                          du matin", déjà nommé
  │                                                                          Phase 1 Section 6)
  ├─ [★★  ] Bouton "→" absent sur dernière colonne (Terminé) unit       [GAP]    (idem)
  ├─ [GAP]  Vrais <button>, aria-label par colonne+carte,    unit/E2E   [GAP]    (idem — Design T4)
  │         cible tactile ≥44px, focus-visible
  ├─ [GAP]  Couleurs colonnes = STATUS_STYLES existant,      unit       [GAP]    (idem — Design T3,
  │         pas une palette réinventée                                       assert même classe CSS
  │                                                                          que /tickets)
  ├─ [★★  ] Mobile (<lg:) → scroll horizontal snap, pas      E2E        [GAP]    (viewport mobile
  │         d'empilement vertical                                           dans le spec E2E)
  └─ [GAP]  Onglet Missions fetch/poll SEULEMENT si actif    unit       [GAP]    (mock timers, assert
             (pas de fetch en tâche de fond, Phase 2 Pass 2)                 0 appel réseau tab non actif)

[+] ActivityRail (repositionnement, ActivityFeed existant)
  ├─ [Oui] Empty state 0 événement — déjà géré, non re-testé  —          ✓ existant  (activity-feed.tsx:44-48,
  │        crédité, pas un gap                                                       pas de nouveau test requis)
  └─ [GAP]  Mobile (<lg:) → repliable, badge "N nouveaux",    unit       [GAP]    activity-rail.test.tsx
             pas caché entièrement (Design T7)

[+] api/routers/core.py::update_ticket_status (backend)
  └─ [★★★] PATCH /tickets/{id}/status sur id inexistant →     pytest     [GAP]    tests/test_tickets_status.py
           404, pas un succès silencieux ni un 500                                  (0 fichier de test
           (CRITICAL GAP #1, root cause exacte)                                     "tickets" existant
                                                                                     aujourd'hui — vérifié,
                                                                                     0 résultat)

COUVERTURE ACTUELLE : 0/32 chemins testés (0%)  |  Code paths: 0/24 (0%)  |  User flows: 0/8 (0%)
GAPS : 32 (7 marqués [→E2E], 25 unitaires/composant, 1 backend pytest)
```

**Règle de régression (IRON RULE) appliquée :** le fix `update_ticket_status` (Section 2)
modifie un comportement existant (silencieux → 404 explicite) sans qu'aucun test ne couvre
aujourd'hui l'ancien comportement — **le test `tests/test_tickets_status.py` doit être
écrit AVANT le fix et rouge (assert 404, obtient 200/500) pour prouver le bug, puis vert
après le fix**, pas ajouté après coup comme simple complément. Ajouté au scope de base
comme prérequis du fix, pas une nice-to-have.

**Pyramide de tests retenue pour cette V1 :** majoritairement composant (Vitest+RTL, mocks
`hubFetch`/`fetchProjects`/`fetchTicketsList`) pour la logique interne (double-clic, empty
states, statut, lazy-fetch) ; **7 flux marqués `[→E2E]`** pour les parcours qui traversent
plusieurs composants réels dans un vrai navigateur (switch d'onglet, persistance
inter-département, avancement Kanban visuel, responsive mobile) — cohérent avec la matrice
de décision E2E du skill (flux commun 3+ composants, ou trop important pour ne faire
confiance qu'à des tests unitaires) ; **1 test pytest backend** pour le fix 404. Aucun test
`[→EVAL]` : aucun appel LLM n'est introduit par ce plan (scope frontend + un endpoint CRUD).

**Test plan artifact écrit séparément** (voir ci-dessous) :
`c:\Dev\ALUNA_HUB\TEST_PLAN_DEPARTMENTS_UI_REDESIGN.md`.

### Section 4 — Performance Review

- **N+1 réseau (confirmé, pas juste théorique) :** sans `useDepartmentData(bureau)`,
  `ProjectGrid` + `MissionsKanban` + l'ancien bloc `app/page.tsx` (Finding ARCH-3)
  fetcheraient chacun indépendamment — jusqu'à 3 fetch réseau redondants au montage d'une
  seule page département. **Confirmé résolu par le hook déjà proposé Phase 1**, à condition
  que la suppression de `app/page.tsx:26-46` (Section 2) soit bien inconditionnelle —
  sinon le N+1 persiste par un chemin que les Phases 1/2 n'avaient pas vu.
- **Cadence de poll — confirmation + précision.** Phase 2 Pass 2 point 3 a déjà décidé
  "poll seulement si l'onglet est actif". Précision manquante : à quelle fréquence, une
  fois actif ? **Décision auto (P3 pragmatique, cohérence avec l'existant) :** aligner sur
  `CONSOLE_POLL_MS` (`console-provider.tsx:42` = 12 000 ms), pas une nouvelle constante —
  Projets/Missions repollent au même rythme que le reste du shell quand leur onglet est
  affiché ; à l'arrêt du poll (changement d'onglet), ne PAS refetcher immédiatement au
  retour sur l'onglet (`useDepartmentData` doit garder les données en cache pendant la
  session, pas les jeter au démontage) — évite un flash de skeleton à chaque va-et-vient
  Équipe↔Missions, déjà un edge case nommé Section 4 Phase 1 ("changement rapide d'onglet
  en boucle").
- **Pagination panneau Performance — confirmée nécessaire côté backend, pas seulement "à
  vérifier".** Aucun endpoint dédié à un historique paginé d'`agent_logs`/`cost_monitor`
  agrégé par agent n'a été trouvé dans `api/routers/` lors de cette review (recherche
  ciblée non exhaustive, cohérent avec le "à vérifier à l'implémentation" déjà noté Phase 1
  Section 7) — **décision auto (P5 explicite) :** si un tel endpoint agrégé n'existe pas
  encore au moment de l'implémentation, le panneau Performance doit appeler un endpoint qui
  retourne un résumé déjà agrégé (ex. moyenne/j sur N jours), jamais les lignes brutes
  d'`agent_logs` téléchargées puis agrégées côté client — sinon le "chemin lent #2" déjà
  identifié Phase 1 se matérialise dès le premier agent avec un historique de plusieurs
  semaines. Si l'endpoint agrégé manque, son ajout (backend, quelques lignes sur un
  `GROUP BY`/équivalent Supabase déjà pratiqué ailleurs dans `services/cost_monitor.py`)
  reste dans le blast radius de `MemberDetailPanel` et donc dans le scope de base — pas un
  TODO différé, contrairement à l'audit trail (voir TODOS ci-dessous).
- **Coût de rendu Kanban à l'échelle :** borné à 100 tickets par le fetch existant
  (confirmé), répartis sur 3-4 colonnes — quelques dizaines de cartes max par colonne dans
  ce cas, rendu React trivial (pas de `Sparkline`/SVG coûteux dans une carte Kanban,
  contrairement à `AgentCard`). Aucune virtualisation nécessaire pour cette V1 ; à
  surveiller seulement si le volume de tickets par bureau dépasse largement 100 dans le
  futur (à ce moment-là la vraie question sera la pagination backend de `/tickets`, pas le
  rendu — voir TODO ajouté ci-dessous).
- **Mémoire/caching :** rien à ajouter aux constats déjà justes de la Phase 1
  (`buildConsoleDepartments()` reste `O(n)` négligeable).

### Failure Modes Registry — mise à jour

```
CODEPATH                              | MODE DE PANNE                  | RESCUED ? | TEST ? | VU PAR L'UTILISATEUR | LOGGÉ ?
----------------------------------------|-----------------------------------|-----------|--------|------------------------|--------
AgentCard unifié × MemberDetailPanel    | status mappé (ConsoleAgentStatus) | N → fix   | GAP    | Libellé contradictoire | N
  (Finding ARCH-1)                       | au lieu de brut (AgentStatusKind)  | spécifié  |        | carte/panneau ← NOUVEAU|
                                          |                                    | Section 1  |        | CRITICAL (si non corrigé)|
department-workspace-store (persist)    | sessionStorage plein/désactivé    | Y (zustand | GAP    | Dégradation silencieuse | N
                                          |                                    | persist    |        | acceptable — pas un    |
                                          |                                    | catch      |        | GAP critique           |
                                          |                                    | interne)   |        |                        |
useDepartmentData (nouveau hook)         | app/page.tsx pas nettoyé →         | N → fix   | GAP    | Double affichage        | N
  (Finding ARCH-3)                       | 2 fetch indépendants persistent    | spécifié   |        | incohérent des projets  |
                                          |                                    | Section 2  |        | ← NOUVEAU si non traité |
MemberDetailPanel (Performance)          | Agrégation côté client sur         | N → décision| GAP   | Chargement très lent    | N
                                          | historique brut non paginé         | Section 4  |        | sur agent ancien        |
                                          |                                    | (agrégat   |        | ← à vérifier à l'impl.  |
                                          |                                    | backend)   |        |                        |
```

**Nouveau CRITICAL GAP confirmé (ARCH-1) :** RESCUED=N + TEST=GAP + USER SEES=régression
visible → même sévérité que les 3 CRITICAL GAPS déjà actés en Phase 1 sur le Kanban.
**Ajouté au scope de base** (pas TODOS.md) : c'est un trou dans l'implémentation de
l'Approche B déjà annoncée, pas une extension. Les 3 CRITICAL GAPS Kanban de la Phase 1
restent CRITICAL — leur fix est spécifié précisément en Section 2 ci-dessus (mécanisme
générique, pas 3 mécanismes séparés).

### Complétion — résumé

```
+====================================================================+
|              ENG REVIEW — COMPLETION SUMMARY (Phase 3)             |
+====================================================================+
| Step 0 (Scope)        | Scope confirmé bien dimensionné, rien       |
|                        | retiré ni ajouté. 2 corrections factuelles  |
|                        | (Playwright existe, Radix absent confirmé). |
|                        | Tab-persistence résolu : Zustand store      |
|                        | dédié + sessionStorage persist              |
| Section 1  (Arch)     | 3 nouveaux findings (ARCH-1 CRITICAL vocab  |
|                        | statut, ARCH-2 précision scope Brand,       |
|                        | ARCH-3 3e duplication fetch)                |
| Section 2  (Qualité)  | 2 fix exacts confirmés (truncate, PATCH 404)|
|                        | + 1 simplification (409/422 → mécanisme     |
|                        | générique) + suppression inconditionnelle   |
|                        | app/page.tsx + AppTicketsSection actée      |
| Section 3  (Tests)    | Diagramme complet, 32 chemins mappés, 0%    |
|                        | couverts. Infra E2E/unit déjà en place      |
|                        | (correction factuelle). Test plan artifact  |
|                        | écrit séparément.                           |
| Section 4  (Perf)     | 4 points : N+1 confirmé résolu (sous        |
|                        | condition), cadence poll précisée (12s,     |
|                        | cache conservé au changement d'onglet),     |
|                        | agrégation backend Performance requise,     |
|                        | Kanban sans risque à l'échelle V1           |
| Failure Modes          | 1 nouveau CRITICAL (ARCH-1), 3 existants    |
|                        | confirmés + fix mécanisme unique            |
| TODOS.md               | 2 nouveaux items ajoutés (append)            |
+====================================================================+
```

**Aucune nouvelle TASTE DECISION** — tous les findings de cette phase ont une réponse
mécanique correcte (pas un vrai choix de goût à deux options défendables), contrairement
aux 4 déjà remontées par les Phases 1/2 qui restent ouvertes telles quelles pour le gate
humain final.

---

## Findings de la voix indépendante (eng) — ajoutés au scope de base

Deux findings de la review indépendante (voix "Explore", zéro contexte des reviews
précédentes) dépassent la sévérité "à noter" et sont auto-acceptés dans le scope de base
(principe P2 — même fichier déjà touché par ce chantier, effort < 1 jour) :

1. **Sécurité — absence de scoping bureau sur les tickets (Medium-High).**
   `api/routers/core.py` (`update_ticket`/`update_ticket_status`) n'a ni l'un ni l'autre de
   vérification que le `ticket_id` appartient au bureau appelant. `agents/tools/hub_tools.py`
   expose cette même fonction à tous les agents QA/dev/spec, tous authentifiés avec le même
   `HUB_API_KEY` partagé (voir SEC-002 dans `BUGS.md`) — un agent d'un bureau peut donc
   modifier (ou halluciner un `ticket_id` et modifier) le ticket d'un autre bureau, sans
   qu'aucun signal ne remonte. Le nouveau Kanban fait de cette donnée la source de vérité
   visuelle d'Emilie — élève le blast radius d'un mauvais tool-call agent. **Auto-décidé
   ACCEPTÉ** : ajouter la vérification `project_id`/bureau dans le même correctif que le
   404 déjà prévu (Phase 3, Section 2) — un seul passage sur ces ~10 lignes, pas un chantier
   séparé.
2. **`ActivityFeed` n'a aucun filtrage réel par bureau.** `buildActivityFeed`
   (`web/src/lib/console/activity.ts:28`) code en dur `dept: "Hub"` sur chaque entrée, quel
   que soit l'agent/bureau source réel. Le rail "persistant par département" tel que
   suggéré par le mockup (activité contextualisée au bureau affiché) ne peut pas fonctionner
   tel quel — c'est un vrai chantier de plomberie (attribuer un bureau réel à chaque event),
   pas juste un repositionnement de layout comme noté en Phase 2. **Auto-décidé ACCEPTÉ**
   dans le scope de base (le rail existe déjà, blast radius contenu à ce fichier + son
   call-site) : le rail reste affiché en mode "toute activité" (comme aujourd'hui) tant que
   le filtrage par bureau n'est pas câblé ; filtrage réel par bureau reporté à TODOS.md
   (dépend d'un mapping agent→bureau fiable côté backend, hors périmètre frontend de ce plan).

---

## Decision Audit Trail (consolidé, 3 phases)

| # | Phase | Décision | Classification | Principe | Rationale | Rejeté |
|---|-------|----------|-----------------|----------|-----------|--------|
| 1 | CEO | Mode SELECTIVE EXPANSION | Mécanique | P6 | Itération sur système existant, pas greenfield | EXPANSION/REDUCTION/HOLD |
| 2 | CEO | Approche B (unification architecturale) vs Approche A (minimale) | Goût → tranché | P1+P2 | Corrige une dette réelle (doublon AgentCard) découverte dans le blast radius de ce même plan | Approche A seule |
| 3 | CEO | 6 cherry-picks ACCEPTÉS sur 12 candidats (DepartmentWorkspace unifié, unification AgentCard, extension AgentFocusPanel, etc.) | Mécanique | P2 | Blast radius + < 1 jour CC | 4 DEFERRED (TODOS.md), 2 SKIPPED (hors blast radius) |
| 4 | CEO | Kanban 4 colonnes du mockup → TASTE DECISION #2 (non auto-décidée à 100%, cf. ci-dessous) | Goût | — | Deux options défendables | — |
| 5 | Design | Fix truncation `agent-card.tsx:103` ajouté au scope de base indépendamment du choix d'unification | Mécanique | P5 | Bug trivial, corrigé une fois quel que soit le sens de TASTE DECISION #1 | — |
| 6 | Design | Radix Tabs comme primitive `Tabs` (aucune n'existe dans `ui/`) | Mécanique | P4 (DRY) | Évite de réinventer ARIA + clavier ; signalé explicitement (pas glissé en silence) car nouvelle dépendance | Composant tabs maison |
| 7 | Design | `progress: null` distingué de `0` réel sur `ProjectGrid` | Mécanique | P1 | Complétude — état "en cours de calcul" ≠ "0% fait" | — |
| 8 | Design | Polling limité à l'onglet actif | Mécanique | P3 | Évite 3x le trafic réseau pour un gain UX nul (onglets non visibles) | Polling des 3 onglets en continu |
| 9 | Eng | Tab actif persistant par département via nouveau store Zustand (`department-workspace-store.ts`, `sessionStorage`) | Mécanique | P5 | Chaque département est une route Next.js distincte (démonte au changement) — ni URL query param (contraintes sidebar) ni `useState` local (perdu au changement de route) ne fonctionnent | URL query param, `useState` local |
| 10 | Eng | Carte unifiée lit le statut brut (`useConsoleData().liveAgents`) et non `ConsoleAgent.status` mappé | Mécanique | P5 | Évite de réintroduire la classe de bug FINDING-001 (perte d'info au mapping statut) | Lire le statut déjà mappé |
| 11 | Eng | Suppression de la 3e implémentation dupliquée du fetch "projets+tickets par bureau" (`app/page.tsx:26-46`) au profit de `useDepartmentData` | Mécanique | P4 (DRY) | 3 implémentations indépendantes du même besoin dans le blast radius de ce plan | Garder les 3 implémentations |
| 12 | Eng | Sous-item "Brand" retiré du cherry-pick #6 (aucun point d'attache réel dans `DepartmentWorkspace`) | Mécanique | P5 | Brand n'utilise jamais `BureauAgentsSection` ; le vrai gap est sur `/hub`, hors périmètre | Forcer Brand dans le scope |
| 13 | Cross-phase | Vérification ownership bureau ajoutée au fix PATCH ticket 404 déjà prévu | Mécanique | P2 | Même fichier, même passage, < 1 jour | Traiter séparément / différer |
| 14 | Cross-phase | Rail `ActivityFeed` reste en mode "toute activité" (pas de filtrage par bureau) pour cette V1 | Mécanique | P2 (scope contenu) | Filtrage réel dépend d'un mapping agent→bureau backend hors périmètre frontend | Construire le filtrage maintenant |

**4 décisions restent de vrais choix de goût, non auto-décidées, remontées telles quelles au gate humain final** (voir section TASTE DECISIONS ci-dessus + finding rail collapsible/toujours-visible de la Phase 2) :
1. Unifier les deux `AgentCard` maintenant (Approche B) vs les laisser coexister (Approche A)
2. Kanban relabelé à 3 statuts réels pour la V1 vs ajouter un vrai statut "En revue" (migration backend)
3. Empty state honnête pour 6/9 bureaux sans concept de projet vs inventer ce concept maintenant
4. Rail `ActivityFeed` toujours visible sur desktop vs repliable (contrainte réelle : sidebar + rail + workspace se compressent sous ~1440px)

**Question stratégique de niveau CEO, distincte des 4 taste decisions ci-dessus** (voir
synthèse finale hors de ce fichier, présentée par l'orchestrateur `/autoplan`) : périmètre
complet (3 onglets + Kanban + panneau membre) maintenant, vs. tranche minimale (sidebar +
rail persistant seulement) en premier, le reste gated sur données d'usage réel.

---

## GATE HUMAIN — Décisions actées par Emilie (2026-07-27)

1. **Périmètre : tout maintenant, en un seul passage.** Le périmètre complet (3 onglets +
   Kanban + panneau membre) est confirmé tel que scopé par les Phases 1-3, pas de tranche
   minimale préalable. Les fixes déjà actés (AgentCard, sécurité ticket, dédup fetch)
   s'appliquaient de toute façon quel que soit ce choix.
2. **Kanban : un vrai statut "En revue" est ajouté maintenant** (pas 3 colonnes relabelées).
   **Vérification de la surface de migration réelle** (faite après la décision, avant
   implémentation, car cette décision inverse l'hypothèse "relabel frontend seulement" de
   la Phase 3) :
   - Backend : `api/routers/core.py:179` — `allowed = {"open", "in_progress", "done",
     "wont_fix"}` → ajouter `"in_review"`. C'est une **validation applicative Python, pas
     une contrainte enum PostgreSQL** — pas de `ALTER TYPE` / migration Supabase nécessaire,
     juste étendre ce set.
   - Frontend : `web/src/components/tickets/tickets.constants.ts:3` — `export type
     TicketStatus = "open" | "in_progress" | "done" | "wont_fix";` → ajouter `"in_review"`.
   - Consommateurs à vérifier pour un `case`/mapping couleur-badge manquant sur le nouveau
     statut : `web/src/lib/tickets.ts`, `web/src/components/tickets/ticket-detail-panel.tsx`,
     `web/src/components/app/app-tickets-section.tsx`, `web/src/components/tickets/ticket-row.tsx`.
   - **Conclusion : la migration est plus légère que redouté en Phase 3** (pas de schéma
     DB à toucher) — reste dans le périmètre frontend + un set Python à étendre, pas un
     chantier backend séparé. Le TODO correspondant dans `TODOS.md` (statut "En revue")
     est **résolu par cette décision**, à retirer de la liste différée.
3. **Onglet Projets : empty state honnête pour les 6/9 bureaux sans concept de projet**
   (recommandation suivie, pas d'invention de modèle produit).
4. **Rail ActivityFeed : repliable, replié par défaut sous 1440px** (recommandation suivie).

**Aucune décision restante ouverte.** Plan prêt pour implémentation.
