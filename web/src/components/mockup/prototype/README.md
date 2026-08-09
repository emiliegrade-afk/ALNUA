# ALNUA — Department UI Prototype

Ce projet reproduit **l’UI/UX des maquettes des pôles ALNUA**, pas le code métier de l’entreprise.

## Écrans inclus

- **R&D → Brainstorm**
  - session multi-agents
  - conversation naturelle
  - pipeline d’idées
  - score de faisabilité
  - exploration automatisée
  - arbre des idées
  - incubateur
  - décision collective
  - ouverture d’une fiche proposition

- **APP → Projets**
  - filtres Tous / Actifs / Validation / Terminés / Archivés
  - cartes projets
  - progression par phase
  - résumé global
  - activité temps réel
  - métriques

- **APP → Missions**
  - pipeline Kanban
  - backlog / in progress / review / completed
  - équipe
  - mission sélectionnée
  - tâches, discussion et analytics

## Architecture

Le point important est que l’interface est **data-driven** : les cartes, agents, projets et missions sont séparés dans `src/data.js`.

La coquille de département est réutilisable pour Gaming, Robotique, Marketing, Comptabilité, etc. On pourra ensuite remplacer les modules propres à chaque pôle sans refaire toute l’UI.

## Lancer

```bash
npm install
npm run dev
```

Puis ouvrir l’URL Vite affichée dans le terminal.

## Pour Cursor

Copie le dossier dans ton workspace puis donne à Cursor une consigne du type :

> « Prends ce prototype comme référence UI. Ne change pas la direction artistique. Branche les composants sur mon backend/API existant et remplace progressivement les données mock de `src/data.js`. »

### Important

Ce prototype n’essaie pas encore de résoudre :
- l’authentification
- les permissions CEO/COO/directeur/agent
- le moteur d’agents
- OpenRouter
- la persistance DB
- le vrai système de tâches
- les workflows d’approbation

Ces éléments viennent **après** la couche UI.
