# Manuel utilisateur ALNUA Hub

Guide destiné à Emilie (CEO) — **pas** aux développeurs.
Objectif : comprendre **à quoi sert** chaque écran, **où cliquer**, et comment enchaîner une journée sans te noyer.

**Dans le Hub :** bureau CEO (`/ceo`) · Bibliothèque (`/library`) · Documents (`/docs`) → ce manuel s’ouvre en page lisible (`/docs/guides/user-manual`).

**Nadia vs Aria vs Solène :** Nadia = assistante LLM générale (NL réel). Aria = COO ops/stratégie. Solène = avocate d'entreprise (UE/USA/Asie), **indépendante**, en contact avec Nadia pour relecture avant signature.

Si tu n’as pas encore installé le Hub → [Installation](../getting-started/installation.md).  
Templates contrats → [catalogue](./contract-templates-catalog.md).  
Première session courte → [Premiers 15 minutes](../getting-started/first-15-minutes.md).  
Vocabulaire produit → [Concepts](../getting-started/concepts.md).

---

## 1. C’est quoi le Hub ?

Le **ALNUA Hub**, c’est ton **siège social virtuel**.

Tu ne lances pas « 20 apps » : tu lances **une fois** le Hub, puis tu pilotes toute l’entreprise ALNUA depuis le navigateur.

Sous le capot, trois briques tournent ensemble :

| Brique | Rôle simple | Où tu le vois |
|--------|-------------|----------------|
| **API** (cerveau) | Agents IA, workflows, données | Port **8003** (invisible au quotidien) |
| **Dashboard** (bureaux) | Interface Next.js — Command Center, pôles, R&D… | http://localhost:**3000** |
| **Bots** (optionnel) | Telegram Nadia / COO | Sur ton téléphone si configuré |

Les **agents** sont des collaborateurs virtuels (Aria la COO, Nadia la secrétaire, Théo le dev, Mira le game director…). Chacun a un bureau, un rôle, et des compétences. Tu leur donnes des intentions ; eux décomposent, rédigent, proposent — **toi** tu valides ce qui compte.

---

## 2. Installer & démarrer (rappel)

| Action | Comment |
|--------|---------|
| **Installer une fois** | Double-clic `Installer ALNUA Hub.bat` → raccourci Bureau |
| **Démarrer** | Double-clic **ALNUA Hub** sur le Bureau |
| **Interface** | Le navigateur s’ouvre sur http://localhost:3000 |
| **Arrêter** | Double-clic `Arreter ALNUA Hub.bat` |
| **État** | PowerShell : `.\scripts\hub-status.ps1` |

**Aucune fenêtre CMD ne doit rester ouverte** : le raccourci passe par un lanceur silencieux.  
Détail complet (H24, `.env`, dépannage install) : [installation.md](../getting-started/installation.md).

---

## 3. Première visite — parcours recommandé

1. Ouvre http://localhost:3000 → **Command Center** (`/`).
2. Utilise le **tiroir Assistants** (bouton flottant) pour parler à **Aria** (COO) ou **Nadia** (secrétaire).
3. Va dans **Décisions** / **CEO** (`/ceo`) — gate Academy, workflows en attente, autonomie.
4. Ouvre le **plan HQ** (`/hq`) — carte des bureaux : clique un bureau pour y entrer.
5. Explore un pôle dans la sidebar gauche (**Pôles** : Direction, Secrétariat, R&D, APP…).

Tu n’as pas besoin de tout maîtriser le premier jour. Commence par : **parler à Aria**, **lire le briefing**, **regarder `/ceo`**.

---

## 4. Carte des écrans (où cliquer)

### Vue globale (sidebar « Vue Globale »)

| Écran | URL | À quoi ça sert |
|-------|-----|----------------|
| Command Center | `/` | Tableau de bord ops — KPIs, feed, réseau agents |
| Activité en direct | `/activity` | Flux temps réel de ce que font les agents |
| Décisions (CEO) | `/ceo` | Validations, Academy gate, workflows en attente |
| Tous les agents | `/agents` | Roster complet par pôle |

### Pôles (sidebar « Pôles »)

| Écran | URL | À quoi ça sert |
|-------|-----|----------------|
| Direction | `/hub` | Ops direction — liens CEO, trust, admin… |
| Secrétariat | `/secretary` | Bureau Nadia — mails, agenda, coordination |
| CEO | `/ceo` | Cockpit exécutif |
| R&D | `/rd` | Idées, **arbres**, **dossiers**, comité |
| APP | `/app` | Équipe dev, projets, missions |
| Gaming | `/gaming` | Studio Wyrdheim |
| Robotique | `/robo` | Hardware / Eve |
| Marketing | `/marketing` | Contenu, campagnes, social |
| Comptabilité | `/finances` | Trésorerie, coûts LLM, budgets |
| Analytics | `/analytics` | Métriques agents |
| Brand Design | `/brand` | Analyse image → brand kits |

### Outils & autres (souvent via HQ ou URL)

| Écran | URL | À quoi ça sert |
|-------|-----|----------------|
| Plan HQ | `/hq` | Carte immersive des bureaux |
| Briefing | `/briefing` | Synthèse du matin (+ brief COO) — via HQ « Salle de réunion » |
| OpenRoom | `/openroom` | Salon / focus agents (espace détente sur le plan) |
| Academy | `/academy` | Niveaux, sprints, validation agents |
| Bibliothèque | `/library` | Connaissances / archives |
| Documents | `/docs` | Index des guides (ce manuel y est listé) |
| IDE Hub | `/ide` | Éditeur + bac à sable code |
| Missions / tickets | `/tickets` | Backlog tâches |
| Roadmap | `/roadmap` | Timeline produit |
| Studio contenu | `/content` | File d’approbation, calendrier |
| Agent Trust | `/trust` | Fiabilité des agents (≠ scores compétition) |
| Paramètres | `/settings` | Modèles LLM, config agents |
| Admin | `/admin` | Flags, coûts, events (avancé) |

---

## 5. Les pôles — en une phrase chacun

- **Direction (`/hub`)** — Aria (COO), Léon (Spec), Alex (QA), Sam (PM), Hugo (Security Sentinel). Orchestration et qualité transverses.
- **Secrétariat (`/secretary`)** — Nadia filtre le bruit, priorise ton agenda et tes mails avant que ça arrive chez Aria.
- **CEO (`/ceo`)** — *ton* bureau : ce qui attend ta décision (workflows, Academy, autonomie).
- **APP (`/app`)** — Théo, Hao, Inès… livrent le produit logiciel (Naïa, NUAWAY, Hub web…).
- **Gaming (`/gaming`)** — Mira, Nova… studio Wyrdheim / UE5.
- **Robotique (`/robo`)** — Yuki, Zara… Eve, hardware, labo.
- **R&D (`/rd`)** — labo d’idées : brainstorm → arbres → dossiers → package CEO (voir §6).
- **Marketing (`/marketing`)** — Camille, Sofia, Léo… contenu et pubs.
- **Finance (`/finances`)** — Jules / Rémi : budgets, factures, coûts LLM.
- **Analytics (`/analytics`)** — Layla / Axel : chiffres et SQL métier.
- **Brand (`/brand`)** — Élise : design system / kits depuis une image.

Sur chaque pôle v2 tu retrouves en général : **équipe**, **projets**, **missions**, parfois un labo ou des assets métier.

---

## 6. Arbres & dossiers R&D (le plus important à comprendre)

### Analogie

Imagine un **mindmap** sur un tableau blanc :

1. Tu poses une **question / idée**.
2. Le Hub explore des **branches** (hypothèses, recherches).
3. Tu **gardes** une branche prometteuse ou tu la **tues**.
4. Une branche gardée devient un **dossier** — un dossier structuré (pas encore un projet produit fini).
5. Le dossier peut passer en **comité**, puis **décision CEO**, puis dispatch vers un pôle (APP, Gaming…).

```text
Idée → Arbre (hypothèses) → garder → Dossier R&D → décision CEO → pôle
                         ↘ tuer → abandon
```

### Où cliquer

| Besoin | Où |
|--------|-----|
| Labo R&D moderne | `/rd` (ou `/rnd-v2`) |
| Voir / manipuler les **arbres** | `/rd` → onglet **Arbres** |
| Liste / ouvrir un **dossier** | `/rd` → onglet **Dossiers** |
| Éditeur dossier complet | `/rd?tab=dossiers&dossier=ID` |
| Brainstorm Idris | `/rd?tab=brainstorm` (ou `/brainstorm` qui redirige) |

### Ce que ce n’est **pas**

- Pas un ticket Jira.
- Pas un repo Git.
- Pas « le projet Naïa ».

C’est un **labo d’hypothèses** avant d’engager du vrai build. Quand une idée est assez mûre, elle sort du labo vers un pôle.

Pipeline hebdo / API avancée : [use-case R&D](./use-case-r-d-pipeline.md).

---

## 7. Une journée type

1. **Démarrer le Hub** (icône Bureau) si ce n’est pas déjà en H24.
2. **Briefing** — `/briefing` (salle de réunion sur `/hq`) : priorités, alertes, opportunités.
3. **CEO** — `/ceo` : valider les workflows en attente, regarder la gate Academy.
4. **Parler à Aria ou Nadia** via le tiroir Assistants : « Priorités du jour », « Relance ce partenaire », etc.
5. **Missions** — `/tickets` ou onglet Missions d’un pôle : qui fait quoi.
6. **Contenu** (si jour comms) — `/content` ou `/marketing` : approuver / planifier.
7. **R&D** (si idée nouvelle) — `/rd` : planter un arbre ou ouvrir un dossier.
8. **Finances** de temps en temps — `/finances` : enveloppes, factures, coûts LLM.
9. **Arrêter** le Hub le soir si tu ne veux pas le laisser tourner (`Arreter ALNUA Hub.bat`).

Tu n’es pas obligée de faire les 9 points chaque jour. Le minimum utile : **briefing + CEO + une conversation Aria**.

---

## 8. Agents en 30 secondes

- **~51 personas** nommées (prénom + rôle), réparties en **rooms** (bureaux) et **teams** (pôles compétitifs).
- La **compétition** (scores, milestones) motive certains agents — transparente pour toi.
- Le **Trust** (`/trust`) mesure la **fiabilité** (autre chose que le score compétition).
- **Hugo Brandt** (Security Sentinel) patrouille la **sécurité du Hub** — pas les crashs apps (ça, c’est Sentry).

Roster visuel : `/agents` ou la carte équipe de chaque pôle.  
Liste technique : `CLAUDE.md` à la racine du repo (pour Cursor / dev).

---

## 9. Sécurité — ce que tu dois retenir

| Règle | Pourquoi |
|-------|----------|
| Ne partage **jamais** ton fichier `.env` | Il contient les clés (Hub, OpenRouter, Supabase…) |
| `HUB_API_KEY` est **obligatoire** | Sans elle, l’API refuse de travailler |
| **Sentry** ≠ **Hugo** | Sentry = crashs apps ; Hugo = intrusion / fuites / lockdown Hub |
| Lockdown actif | Seul le PC local (`127.0.0.1`) passe — utile si suspicion d’attaque |

Checklist VPS / béton armé : [SECURITY_HARDENING.md](./SECURITY_HARDENING.md).

---

## 10. Dépannage rapide

| Symptôme | Que faire |
|----------|-----------|
| Rien ne s’ouvre | Relance l’icône Bureau ; vérifie `.\scripts\hub-status.ps1` |
| Page blanche / web KO | `cd web` puis `npm install` ; relance le Hub |
| Erreurs 401 | Vérifie `HUB_API_KEY` dans `.env` (même valeur côté web si configuré) |
| API morte | Regarde `data\hub_supervisor.log` |
| « venv introuvable » | Refais l’étape Python de [installation.md](../getting-started/installation.md) |
| Lockdown bloquant | `POST /ops/security/lockdown?active=false` avec ta clé, ou fichier `data/security_lockdown.json` → `"active": false` |

Santé API manuelle :

```powershell
Invoke-RestMethod http://127.0.0.1:8003/health
```

(Canonique : `/health` — pas besoin du préfixe `/v1`.)

---

## 11. Aller plus loin

| Guide | Pour quoi |
|-------|-----------|
| [Installation](../getting-started/installation.md) | Installer / H24 / status |
| [Premiers 15 minutes](../getting-started/first-15-minutes.md) | Première session guidée |
| [Concepts](../getting-started/concepts.md) | Vocabulaire produit |
| [Pipeline contenu](./use-case-content-creation.md) | Brief → multi-plateformes |
| [Pipeline R&D](./use-case-r-d-pipeline.md) | Cycle hebdo labo |
| [Pipeline coding](./use-case-coding-pipeline.md) | Academy / code |
| [Auth API](../api/authentication.md) | Clés Hub / headers |
| [MCP Cursor](./MCP_CURSOR_SETUP.md) | Brancher le Hub dans Cursor |
| [Sécurité](./SECURITY_HARDENING.md) | Durcissement VPS |

Suite produit prévue hors ce manuel : VPS / UE / Pi (H6). HQ immersif (H5) est
livré — ouvre `/hq` pour la carte.
