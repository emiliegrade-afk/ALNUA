# Test Plan — Refonte UI Départements (ALNUA Hub)

Généré par `/plan-eng-review` (Phase 3 de `/autoplan`) le 2026-07-27.
Branche : `feat/rnd-dossier-hub`.
Plan source : `PLAN_DEPARTMENTS_UI_REDESIGN.md` (Phases 1 CEO, 2 Design, 3 Eng).

Ce fichier est consommable tel quel par `/qa` et `/qa-only`, et sert de check-list
d'implémentation (chaque test doit être écrit **avec** le composant, pas après).

---

## Infra de test confirmée (pas à réinstaller)

- **Composant/unit** : Vitest 2.1 + Testing Library React 16 (`web/vitest.config.ts`,
  `web/package.json` script `test:watch`). Convention de fichier : `*.test.tsx` colocalisé
  ou dans `web/src/__tests__/`. Précédent existant :
  `web/src/__tests__/assistant-chat.test.tsx` (actuellement un simple smoke test de
  chargement de module — à dépasser, pas à imiter, pour les nouveaux composants).
- **E2E** : Playwright 1.60 (`web/playwright.config.ts`, script `test:e2e`), `webServer`
  double (FastAPI sur :8001 + `npm run dev` sur :3000) déjà câblé, `HUB_API_KEY` de test
  déjà injecté. Précédents directs à calquer :
  - `web/e2e/rd-tabs.spec.ts` — switch d'onglets réel sur une page bureau (`/rd`),
    assertions `getByRole("button", { name, exact: true })` puis contenu qui apparaît.
  - `web/e2e/page-audit.spec.ts` — crawle déjà les 9 pages département (+ CEO/Brand) et
    échoue sur crash/erreur JS. **Ne pas casser ce test** — c'est le filet de sécurité
    existant le plus large sur cette zone, gratuit pour ce chantier.
- **Backend** : pytest + `fastapi.testclient.TestClient` (`tests/conftest.py`, fixture
  `hub_client`/`client` avec `FakeDB` + monkeypatch de `get_supabase`). Précédent :
  `tests/test_api_routes_phase4.py`. Aucun fichier de test ne référence `/tickets/`
  aujourd'hui (vérifié, 0 résultat) — le fichier ci-dessous est entièrement nouveau.

---

## Affected Pages/Routes

- `/app`, `/gaming`, `/robo`, `/marketing`, `/finances`, `/rd`, `/analytics`,
  `/secretary`, `/hub` — les 9 pages qui montent `DepartmentWorkspace`. Tester le rendu
  complet (Équipe/Projets/Missions + rail activité) sur au moins 2 d'entre elles
  (App = a un vrai concept de projet ; Marketing = n'en a pas, teste l'empty state).
- `/ceo`, `/brand` — ne montent PAS `DepartmentWorkspace` (pages bespoke). Vérifier
  qu'elles continuent de fonctionner sans régression (déjà couvert par
  `page-audit.spec.ts`, à ne pas casser).
- `/agents` — roster global, consomme `console/agent-card.tsx` (non touché par ce plan).
  Smoke-vérifier après le refactor Approche B pour s'assurer qu'il n'a pas régressé
  (partage `useConsoleData()` avec les pages département désormais).

## Key Interactions to Verify

- Ouvrir une page département → l'onglet Équipe est actif par défaut (première visite).
- Cliquer Projets, puis Missions → le contenu change réellement (pas juste le style du
  bouton actif — régression déjà vue une fois sur `/rd` selon le commentaire de
  `rd-tabs.spec.ts`).
- Changer d'onglet sur `/app` (aller sur Missions), naviguer vers `/gaming` via la
  sidebar, puis revenir sur `/app` via la sidebar → l'onglet Missions doit être encore
  actif (pas de reset à Équipe). C'est le flux le plus à risque de cette refonte du point
  de vue UX (signalé high-severity par la design review indépendante).
- Cliquer une carte agent → panneau détail s'ouvre sur le sous-onglet Aperçu par défaut ;
  cliquer Compétences/Performance/Mémoire → contenu charge à la demande (pas au montage).
- Dans le Kanban Missions, cliquer la flèche "avancer" une fois → la carte change de
  colonne, une seule requête part. Cliquer deux fois très vite sur le même bouton → une
  seule requête PATCH doit partir (pas deux).
- Rétrécir la fenêtre sous ~1024px (breakpoint `lg:`) → le Kanban passe en scroll
  horizontal snap (pas d'empilement vertical des colonnes) ; le rail Activité passe en
  section repliable avec badge de compte (pas caché entièrement).
- Sur un bureau sans concept de projet (ex. `/marketing`), l'onglet Projets affiche un
  texte spécifique au bureau (pas un message générique unique), sans bouton d'action qui
  ne mène nulle part.

## Edge Cases

- Nom d'agent à 47 caractères sur la carte unifiée → tronqué proprement (`truncate`), ne
  casse pas le layout du badge à droite.
- `PATCH /tickets/{id}/status` sur un ticket qui vient d'être supprimé (404 backend, après
  le fix) → la carte Kanban se retire de l'écran + toast d'erreur, pas de carte figée
  silencieuse.
- Coupure réseau pendant le chargement de l'onglet Projets ou Missions → toast d'erreur +
  état "réessayer", les données déjà chargées avant la coupure ne sont pas effacées de
  l'écran.
- `Project.branch` avec une valeur inattendue (donnée corrompue, ex. une chaîne qui ne
  matche aucun des bureaux gérés) → la grille Projets ignore/loggue, ne plante pas.
- Onglet Mémoire du panneau membre : `GET /library/topics` qui échoue ou renvoie vide →
  état vide explicite, pas un onglet blanc sans explication.
- Onglet Performance du panneau membre pour un agent tout neuf (aucun `agent_logs`) →
  état vide "Pas encore d'historique", pas une erreur.
- Changer d'onglet Équipe→Projets→Missions→Équipe très rapidement (5 fois en 2 secondes)
  → pas de 5 requêtes réseau concurrentes ; les données déjà chargées pour un onglet déjà
  visité ne redéclenchent pas de fetch au retour dessus dans la même session.
- Naviguer en navigation privée stricte (sessionStorage indisponible) → le changement
  d'onglet fonctionne quand même (juste sans persistance au refresh), pas de crash.

## Critical Paths

- **Parcours "scanner un département" (le parcours principal de toute la refonte) :**
  ouvrir `/app` → voir l'onglet Équipe avec les cartes agents (statut/utilization
  cohérents avec ce qu'affiche le panneau détail au clic — pas de libellé contradictoire
  entre carte et panneau, cf. Finding ARCH-1 du rapport eng review) → cliquer Projets →
  voir la grille avec anneaux de progression réels → cliquer Missions → voir le Kanban
  rempli par les vrais tickets du bureau.
- **Parcours "faire avancer une mission" :** onglet Missions → cliquer flèche avancer sur
  un ticket → carte change de colonne → simuler une coupure réseau à ce moment précis →
  la carte revient à sa colonne d'origine + toast d'erreur (pas de mensonge visuel sur
  l'état réel du ticket).
- **Parcours "changer de département sans perdre son contexte" :** `/app` (onglet
  Missions) → sidebar → `/gaming` → sidebar → `/app` → toujours sur Missions. C'est le
  flux dont dépend toute la valeur ajoutée de la mémorisation par store (voir résolution
  Step 0 du rapport eng review).
- **Parcours backend isolé :** `PATCH /tickets/{id}/status` avec un id inexistant →
  404 (et non 200 silencieux ou 500), testé indépendamment du frontend via pytest.

---

## Diagramme de couverture détaillé (référence complète)

Voir `PLAN_DEPARTMENTS_UI_REDESIGN.md`, section "Phase 3 — Eng Review → Section 3 — Test
Review" pour le diagramme ASCII complet chemin-par-chemin (32 chemins mappés, type de
test recommandé, fichier à créer). Résumé des fichiers de test à créer :

| Fichier | Type | Couvre |
|---|---|---|
| `web/src/store/department-workspace-store.test.ts` | Vitest unit | Store : set/lecture avec défaut, persistance |
| `web/e2e/department-workspace-tabs.spec.ts` | Playwright E2E | Switch d'onglets, contenu qui swap réellement, navigation clavier |
| `web/e2e/department-workspace-persistence.spec.ts` | Playwright E2E | Onglet mémorisé entre départements (le flux le plus à risque) |
| `web/src/components/shared/agent-card.test.tsx` | Vitest+RTL | Truncate 47 car., status brut vs mappé (ARCH-1), utilization/model |
| `web/src/components/openroom/member-detail-panel.test.tsx` | Vitest+RTL | Sous-onglet défaut Aperçu, lazy-fetch au clic, empty states Mémoire/Performance |
| `web/src/components/console/project-grid.test.tsx` | Vitest+RTL | Empty state par bureau, progress null vs 0, branch corrompu, erreur réseau |
| `web/e2e/missions-kanban.spec.ts` | Playwright E2E | Avancer un ticket (visuel réel), responsive mobile snap-scroll |
| `web/src/components/console/missions-kanban.test.tsx` | Vitest+RTL | Double-clic → 1 seule requête, rollback+toast sur 404/erreur générique, garde-fous colonnes, aria-label, poll actif seulement |
| `web/src/components/console/activity-rail.test.tsx` | Vitest+RTL | Repli mobile, badge de compte |
| `tests/test_tickets_status.py` | pytest | `PATCH /tickets/{id}/status` sur id inexistant → 404 (écrire rouge avant le fix, vert après — règle de régression) |

**Couverture actuelle : 0/32 chemins (0%).** Aucun de ces fichiers n'existe — c'est
attendu à ce stade (rough plan + 3 reviews, zéro code écrit). L'implémentation doit
inclure ces tests au fil de l'eau, pas en follow-up.
