# TODOs — ALNUA Hub

Suivi des travaux identifiés mais explicitement différés lors des reviews de plan
(`/plan-ceo-review`, `/autoplan`, etc.). Chaque entrée doit rester actionnable par
quelqu'un qui n'a pas le contexte de la session où elle a été créée.

---

## Depuis la CEO Review — Refonte UI Départements (`PLAN_DEPARTMENTS_UI_REDESIGN.md`, 2026-07-27)

### TODO-001 — Recherche Cmd+K réelle (topbar)

- **Quoi :** Remplacer le faux champ de recherche du topbar (`web/src/components/console/console-topbar.tsx:109-123`, actuellement un `<input readOnly>` qui redirige juste vers `/agents` au focus) par une vraie recherche indexant agents, tickets et projets.
- **Pourquoi :** Le mockup montre une barre de recherche fonctionnelle ; l'input actuel est un placeholder visuel trompeur (il a l'air de marcher mais ne cherche rien).
- **Pros :** Gain de navigation réel, cohérent avec le motif "Agentic OS" des mockups ; réutilise `hubFetch`/les endpoints existants (`/tickets`, `/projects`, roster agents).
- **Cons :** Nécessite une indexation multi-source (agents statiques + tickets + projets dynamiques) et une UI de résultats (dropdown, navigation clavier) — pas un simple ajout de prop.
- **Contexte :** Découvert pendant la CEO review de la refonte UI départements (Phase 11). Hors blast radius de cette refonte (le topbar est partagé par toutes les pages, pas seulement les pages département) et dépasse le seuil d'1 jour d'effort CC retenu pour un cherry-pick auto-accepté.
- **Effort estimé :** L (humain) → M avec CC+gstack.
- **Priorité :** P2.
- **Dépend de / bloqué par :** Rien — indépendant du reste de la refonte départements.

### TODO-002 — Drag-and-drop réel sur le Kanban Missions

- **Quoi :** Ajouter le drag-and-drop (ex. `dnd-kit`) pour réordonner/changer de colonne les cartes du Kanban Missions, en V1 le changement de statut se fait via des boutons flèches uniquement.
- **Pourquoi :** Le mockup suggère un Kanban glisser-déposer classique ; les boutons flèches (retenus pour la V1) couvrent le besoin fonctionnel mais pas l'expérience "native" d'un board Kanban.
- **Pros :** Expérience plus fluide et familière (Trello-like) ; meilleure lisibilité du geste "faire avancer une mission".
- **Cons :** Nouvelle dépendance npm ; accessibilité clavier/tactile à retravailler proprement (le drag-and-drop casse souvent la navigation clavier si mal fait) ; nécessite un champ d'ordre explicite sur `Ticket` qui n'existe pas aujourd'hui (`web/src/lib/types.ts`).
- **Contexte :** Découvert pendant la CEO review. Les boutons flèches ont été retenus comme scope de base précisément parce qu'ils évitent cette dépendance et cette dette d'accessibilité pour la V1 — voir Section 1/11 du plan.
- **Effort estimé :** M-L (humain, avec le travail a11y) → M avec CC+gstack.
- **Priorité :** P3.
- **Dépend de / bloqué par :** Le Kanban V1 (boutons flèches) doit être livré et stable en premier.

### TODO-003 — ~~Vrai statut "En revue" pour les tickets (backend)~~ — RÉSOLU, absorbé dans le scope de base

- **Statut : décidé par Emilie au gate final (2026-07-27) — plus un TODO différé, dans le
  scope de base de `PLAN_DEPARTMENTS_UI_REDESIGN.md`.** Retiré de la liste des items en
  attente ; conservé ici pour l'historique de la décision.
- **Quoi :** Ajouter un statut `in_review` (`api/routers/core.py:179` — `allowed = {"open", "in_progress", "done", "wont_fix"}` — et `web/src/components/tickets/tickets.constants.ts` — `TicketStatus`).
- **Correction post-décision :** contrairement à l'hypothèse de la Phase 3 CEO review,
  `allowed` est une **validation applicative Python, pas un enum PostgreSQL** — pas de
  migration DB (`ALTER TYPE`) nécessaire. Reste : étendre les 2 définitions de type +
  auditer les consommateurs (`web/src/lib/tickets.ts`,
  `web/src/components/tickets/ticket-detail-panel.tsx`,
  `web/src/components/app/app-tickets-section.tsx`,
  `web/src/components/tickets/ticket-row.tsx`) pour un `case`/mapping badge-couleur manquant
  sur le nouveau statut. Détail complet dans la section "GATE HUMAIN" du plan.
- **Effort réel (plus faible que l'estimation initiale) :** S avec CC+gstack — pas de
  migration DB, juste 2 unions de types + 4 fichiers consommateurs à vérifier.

### TODO-004 — Notion de "projet" pour tous les bureaux (pas seulement App/Gaming/Robo)

- **Quoi :** Définir et implémenter ce qu'est un "projet" pour les bureaux Marketing, Finances, R&D, Analytics, Secrétariat et Hub — aujourd'hui `ProjectBranch` (`web/src/lib/types.ts`) ne couvre que `"app" | "gaming" | "robotics" | "other"`, donc l'onglet "Projets" de ces 6 bureaux sur 9 n'a structurellement aucune donnée réelle à afficher (empty state honnête retenu pour la V1).
- **Pourquoi :** Le mockup montre un onglet Projets rempli sur tous les départements. Sans ce travail, 6 bureaux sur 9 auront un onglet visuellement vide en permanence, ce qui peut sembler incomplet malgré l'intention.
- **Pros :** Complète la cohérence visuelle du mockup sur 100% des bureaux ; donne à chaque bureau une vraie unité de suivi (campagnes pour Marketing, dossiers pour R&D, clôtures pour Finances, etc.).
- **Cons :** Redéfinit un concept produit avant tout travail technique — "qu'est-ce qu'un projet pour Marketing" n'est pas une évidence (une campagne ? un calendrier de contenu ?), pareil pour R&D (un dossier existant du Centre R&D ?) — nécessite un arbitrage produit avec Emilie avant toute implémentation, pas une extension mécanique du schéma.
- **Contexte :** **TASTE DECISION #3** de la CEO review. Le plus gros des items différés — effort XL, largement au-delà du seuil "boil-the-lake" d'1 jour retenu pour un cherry-pick auto-accepté.
- **Effort estimé :** XL (humain) → L avec CC+gstack (le code va vite, l'arbitrage produit ne se compresse pas).
- **Priorité :** P2.
- **Dépend de / bloqué par :** Arbitrage produit préalable avec Emilie sur la définition de "projet" par bureau — bloque tout travail technique.

### TODO-005 — Suite de tests E2E (Playwright) sur les pages département

- **Quoi :** Au-delà des tests de rendu minimaux (Vitest + Testing Library) retenus au scope de base de la refonte UI départements, construire une suite E2E couvrant les parcours complets (changer d'onglet, avancer un ticket au Kanban, ouvrir le panneau membre, naviguer ses 4 sous-onglets).
- **Pourquoi :** `web/src/components/console/*` et `web/src/components/shared/bureau-*` n'ont aujourd'hui **aucun test** (le seul test frontend du repo est `web/src/__tests__/assistant-chat.test.tsx`), sur une zone qui a déjà connu 6 commits de fix design consécutifs (FINDING-001 à FINDING-006) juste avant cette refonte — signal de fragilité visuelle récurrente.
- **Pros :** Filet de sécurité réel sur une zone à risque de régression démontré ; permet de merger la refonte avec confiance sur la durée, pas juste au moment du ship.
- **Cons :** Effort non trivial si le repo n'a pas encore d'infra Playwright configurée (à vérifier) ; maintenance continue des sélecteurs E2E si l'UI change souvent (ce qui est précisément le cas de cette zone).
- **Contexte :** Section 6 (Test Review) de la CEO review. Les tests de rendu minimaux sont au scope de base (pas différés) ; c'est la couverture E2E complète qui est différée pour rester sous le seuil d'effort d'1 jour du cherry-pick.
- **Effort estimé :** M (humain, si infra Playwright déjà en place ailleurs dans le repo) → S-M avec CC+gstack.
- **Priorité :** P3.
- **Dépend de / bloqué par :** La refonte UI départements doit être livrée en premier (rien à tester avant).

---

## Depuis la Design Review (Phase 2, `/plan-design-review` via `/autoplan`) — Refonte UI Départements (`PLAN_DEPARTMENTS_UI_REDESIGN.md`, 2026-07-27)

### TODO-006 — Audit accessibilité automatisé (axe-core / pa11y) sur les nouveaux composants

- **Quoi :** Ajouter un test d'accessibilité automatisé (ex. `axe-core` intégré aux tests Vitest/Testing Library, ou `pa11y` en CI) ciblant spécifiquement `DepartmentWorkspace`, `MissionsKanban`, `ProjectGrid` et `MemberDetailPanel` — contraste, rôles ARIA, navigation clavier.
- **Pourquoi :** La Design Review (Pass 6) a trouvé plusieurs trous d'accessibilité concrets déjà corrigés au niveau du plan (cibles tactiles 44px, `aria-label` par colonne Kanban, vrais `<button>`, primitive Radix Tabs) — mais un fix "au plan" n'est pas un fix "vérifié". Sans test automatisé, une régression future (nouvelle carte, nouveau sous-onglet) peut réintroduire silencieusement les mêmes trous. La zone a déjà un historique de 6 commits FINDING-XXX de régressions visuelles (Phase 1, audit système) — l'a11y est le même type de risque, pas testé aujourd'hui.
- **Pros :** Filet de sécurité automatisé sur une dimension qu'un test de rendu classique (happy path) ne couvre pas ; détecte les régressions de contraste/ARIA dès la CI, pas au audit manuel post-ship.
- **Cons :** Nouvelle dépendance de test (`axe-core` ou `pa11y`) + configuration initiale ; whitelist à établir pour les faux positifs connus (ex. contraste sur des tokens `/40`-`/50` déjà acceptés ailleurs dans le repo).
- **Contexte :** Découvert pendant la Design Review (Phase 2) de la refonte UI départements — distinct de TODO-005 (E2E Playwright, parcours utilisateur complet) qui ne couvre pas spécifiquement l'accessibilité.
- **Effort estimé :** M (humain, configuration initiale + baseline) → S-M avec CC+gstack.
- **Priorité :** P2.
- **Dépend de / bloqué par :** Les composants de la refonte (Kanban, ProjectGrid, MemberDetailPanel) doivent exister pour être audités.

### TODO-007 — Indicateur de statut agent "figé" (staleness) sur l'onglet Équipe

- **Quoi :** Ajouter un signal visuel quand un agent reste dans le même statut (ex. "Réflexion"/"En cours") anormalement longtemps sans changement de tâche — au-delà d'un seuil à définir.
- **Pourquoi :** Surfacé pendant le storyboard émotionnel de la Design Review (Pass 3) : Emilie scanne l'onglet Équipe pour être "réassurée ou alertée" ; aujourd'hui rien ne distingue un agent normalement actif d'un agent bloqué depuis des heures dans le même statut affiché.
- **Pros :** Transforme l'onglet Équipe d'un simple statut instantané en un vrai outil de supervision ("qui a besoin d'attention") ; s'aligne avec le ton "cockpit" de toute la refonte.
- **Cons :** Nécessite un nouveau modèle de données (timestamp de dernier changement de statut par agent, pas seulement le statut courant) — pas une extension mécanique de l'existant ; le seuil "anormalement long" varie probablement par type de tâche, pas un chiffre universel évident.
- **Contexte :** Delight opportunity identifiée en Pass 3 (User Journey), explicitement notée comme hors scope de base (nouveau modèle de données requis, au-delà du seuil P2 boil-the-lakes d'1 jour).
- **Effort estimé :** M-L (humain, modèle de données + UI) → M avec CC+gstack.
- **Priorité :** P3.
- **Dépend de / bloqué par :** Rien de bloquant côté refonte départements — indépendant, peut arriver après.

---

## Depuis l'Eng Review (Phase 3, `/plan-eng-review` via `/autoplan`) — Refonte UI Départements (`PLAN_DEPARTMENTS_UI_REDESIGN.md`, 2026-07-27)

### TODO-008 — Audit trail sur les changements de statut ticket

- **Quoi :** Journaliser qui a changé le statut d'un ticket et quand (ex. table
  `ticket_status_history` ou colonnes `status_changed_by`/`status_changed_at` sur
  `tickets`), consultable si un bug de Kanban est signalé plus tard.
- **Pourquoi :** La CEO review (Section 8) avait déjà noté ce gap sans le résoudre ni le
  loguer explicitement ("reporté à la même décision"). L'eng review confirme : après le
  fix du gap 404 (`api/routers/core.py:177-183`), `update_ticket_status` reste une
  écriture sans trace — si un ticket change de statut de façon inattendue (bug Kanban,
  double-clic non intercepté, etc.), la seule preuve disponible dans 3 semaines serait
  l'état courant de la ligne en DB, pas son historique.
- **Pros :** Debuggabilité réelle sur une zone interactive nouvelle (Kanban) qui n'existait
  pas avant cette refonte ; utile aussi pour un futur statut "En revue" (TODO-003) si
  celui-ci se concrétise (traçer qui a validé une revue).
- **Cons :** Migration DB (nouvelle table ou colonnes) + modification de
  `update_ticket_status` et potentiellement `update_ticket` pour rester cohérents entre
  les deux endpoints d'écriture ticket ; pas un simple ajout frontend, dépasse le seuil
  d'1 jour retenu pour un cherry-pick auto-accepté.
- **Contexte :** Découvert/confirmé pendant l'Eng Review (Phase 3), Section 4/8. Distinct
  du fix 404 lui-même (T8, scope de base, déjà accepté) — celui-ci ajoute une garde-fou
  d'existence, pas une trace d'audit.
- **Effort estimé :** M (humain, migration + 2 endpoints à auditer) → S-M avec CC+gstack.
- **Priorité :** P3.
- **Dépend de / bloqué par :** Le fix 404 (`update_ticket_status`, scope de base de cette
  refonte) doit être livré en premier — l'audit trail s'ajoute sur un endpoint déjà
  correct, pas sur un endpoint encore silencieusement cassé.

### TODO-009 — Pagination backend réelle sur `/tickets` (au-delà de la limite 100 actuelle)

- **Quoi :** Ajouter une pagination cursor-based (ou offset) à l'endpoint `/tickets`
  (`api/routers/core.py`, consommé par `fetchTicketsList` — `web/src/lib/tickets.ts:21-32`)
  pour que le Kanban Missions (et `/tickets`, `AnalyticsView`, qui utilisent le même
  `limit: 100` codé en dur) ne plafonnent plus silencieusement l'historique visible.
- **Pourquoi :** L'eng review confirme le GAP déjà noté en Section 1/4 de la CEO review :
  `fetchTicketsList({ limit: 100 })` est déjà utilisé à l'identique dans 3 endroits
  (`app-tickets-section.tsx:38`, `analytics-view.tsx:49`, `tickets-view.tsx:50`) — un
  Kanban avec beaucoup d'historique dans la colonne "Terminé" tronquerait silencieusement
  au-delà de 100 tickets. La V1 de cette refonte mitige avec un lien "Tous les tickets" par
  colonne (scope de base, pas une vraie pagination) — suffisant tant que le volume reste
  sous 100 par bureau, mais pas une solution durable si le volume grandit.
- **Pros :** Résout le plafond à la racine pour tous les consommateurs de
  `fetchTicketsList`, pas seulement le nouveau Kanban ; rend `/tickets` (page dédiée)
  également plus correct pour un historique long.
- **Cons :** Touche un endpoint partagé par au moins 3 consommateurs frontend existants +
  potentiellement `AnalyticsView` — nécessite de vérifier que chacun gère bien un résultat
  paginé (pas juste un tableau complet) ; pas un simple changement de paramètre, un
  changement de contrat d'API.
- **Contexte :** Découvert/précisé pendant l'Eng Review (Phase 3), Section 4 (Performance).
  Non bloquant pour le ship de cette refonte — le garde-fou "lien Tous les tickets par
  colonne" (scope de base) couvre le besoin réel au volume actuel (confirmé : App/Gaming/
  Robo ont un nombre de projets/tickets faible aujourd'hui).
- **Effort estimé :** M-L (humain, contrat d'API partagé par plusieurs pages) → M avec
  CC+gstack.
- **Priorité :** P3.
- **Dépend de / bloqué par :** Rien de bloquant — à réévaluer si le volume de tickets par
  bureau approche réellement 100 dans les mois suivant le ship de cette refonte.
