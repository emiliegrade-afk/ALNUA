# ALNUA — Qu’est-ce que c’est, et comment c’est organisé

Guide produit / infrastructure du Hub. Pour le détail technique (stack, sécurité, data flow), voir aussi `ARCHITECTURE.md` et `CLAUDE.md`.

---

## 1. Qu’est-ce qu’ALNUA ?

**ALNUA** est une société solo (Emilie) structurée comme une entreprise complète — mais dont les « employés » sont des **agents IA** (personas LLM) qui travaillent dans un **siège social virtuel**.

Ce siège s’appelle le **ALNUA Hub** (`ALUNA_HUB/`) : un dashboard Next.js + une API FastAPI qui orchestrent ~**50 agents** répartis en départements (pôles / rooms). Chaque agent a un prénom, un rôle, un modèle LLM (tier fast / standard / premium), une mémoire (Mem0) et des compétences métier.

Le Hub n’est pas un produit grand public : c’est le **centre de commandement** pour faire avancer trois branches produit.

| Branche | Produit | Idée |
|---------|---------|------|
| **App** | Naïa | App bien-être (repo séparé `NAÏA/`) |
| **Gaming** | Wyrdheim Online | MMORPG fantasy nordique (UE5 / Nwiro, aussi Godot selon projet) |
| **Robotique** | Eve | Robot compagnon domestique |

Autrement dit : ALNUA = la « boîte » ; le Hub = le QG ; Naïa / Wyrdheim / Eve = les produits.

---

## 2. Infrastructure technique (vue simple)

```
Humain (Emilie) + Cursor (MCP) + bots Discord/Telegram + n8n
        │
        ▼
   Frontend Next.js (web/)     ← siège social : lobby, bureaux, outils
        │
        ▼
   API FastAPI (api/)          ← X-Hub-Key obligatoire
        │
        ├── Agents (agents/)   ← personas LLM via OpenRouter
        ├── Services           ← compétition, R&D, finances, brand, etc.
        ├── Skills             ← Mem0, Langfuse, intégrations
        └── Supabase           ← Postgres + RLS
```

| Couche | Rôle |
|--------|------|
| **Frontend** (`web/`) | Siège virtuel : carte HQ, bureaux par département, outils (IDE, Academy, bibliothèque…) |
| **API** (`api/`) | **44** routers REST ; montée aussi en **MCP** (`/mcp`) pour Cursor |
| **Agents** | COO, PM, QA, devs, marketing, R&D, hardware, finance, analytics… |
| **Services** | Orchestration (plans COO, parallel runner), coûts LLM, dossiers R&D, brand kit, event bus… |
| **Automatisation** | n8n (briefing quotidien, workflows externes) |
| **Bots** | Discord, Telegram, publisher, reviews, SAV, watchdog… |
| **Observabilité** | Langfuse (traces) + `cost_monitor` (budget LLM) |

---

## 3. Comment on « entre » dans le Hub

| Route | Nom | À quoi ça sert |
|-------|-----|----------------|
| `/` | **Command Center** | Tableau de bord ops global (KPIs, activité, incidents, décisions du jour) |
| `/hq` | **Annuaire des pôles** | Grille des départements (raccourcis vers chaque bureau) |
| Carte HQ (lobby) | **Plan du siège** | Hotspots cliquables vers bureaux + espaces (réunion, openroom, IT…) |

La carte du siège (`HQ_MAP_OFFICES`) place physiquement les bureaux dans un atrium (rez-de-chaussée + mezzanine) : CEO, Secrétariat, Direction, App, Gaming, Robotique, Finance, Marketing, R&D, Academy, Brand, Analytics, Connections, etc.

---

## 4. Les départements — pages internes & fonctions

Chaque bureau a une route canonique. Depuis août 2026, `/app`, `/gaming`, `/robo`, `/marketing`, `/finances` ré-exportent les shells `*-v2` (les URLs `*-v2` restent valides en bookmark).

Chrome partagé sur beaucoup de pôles : **Vue générale · Départements · Missions · Analytics · Ressources**.

---

### 4.1 Direction & gouvernance

#### `/ceo` — Bureau CEO
- **Rôle** : cockpit exécutif (Emilie) — gate Academy, file de décisions, dossiers à valider / préparer.
- **Fonctions** : score gate Academy, évaluation, liens vers dossiers R&D, refresh.
- Pas un roster d’agents « employés » : c’est le bureau humain + arbitrages.

#### `/secretary` — Secrétariat (Nadia Faure)
- **Rôle** : filtre, mails, agenda, SAV avant la direction.
- **Fonctions** : compagnon PC Nadia (statut Hub, boot session) ; rédiger / trier emails ; planifier réunion ; brouillon de contrat ; compte rendu.

#### `/hub` — Direction (Aria, Sam, Léon, Alex)
- **Rôle** : orchestration opérationnelle (COO / PM / Spec / QA).
- **Onglets (maquette)** : Dashboard · Santé pôles · Pipeline · Coûts · Workflows.
- **Agents** : Aria Voss (COO), Sam Rivera (PM), Léon Marchand (Spec), Alex Okafor (QA).

#### `/briefing` — Salle de réunion / Briefing matinal
- Brief opérationnel + brief COO (tickets, posts, priorités, alertes).

---

### 4.2 Pôle App — `/app`

**Mission** : développement produits digitaux (Naïa et apps ALNUA).

| Onglet | Contenu typique |
|--------|-----------------|
| **Équipe** | Cartes agents, chat / missions, aperçu compétences / perf / mémoire |
| **Projets** | Projets App en cours |
| **Missions** | Travail assigné |
| **Backlog** | File de tickets |
| **Documentation** | Docs du pôle |

**Actions rapides** : nouvelle mission, rapport d’équipe, analyse projet, automatisation.

| Agent | Rôle |
|-------|------|
| Théo Laurent | Dev apps mobiles |
| Hao Chen | Backend & API |
| Inès Moreau | Frontend / UI Hub |
| Rayan Kone | Intégrateur / merge |
| Luca Bernard | Prof de code (mentor CEO, IDE) |

*(Côté backend personas : aussi Naïm Tessier `rnd_product` — fiche produit R&D.)*

---

### 4.3 Studio Gaming — `/gaming`

**Mission** : Wyrdheim — lore, gameplay, builds UE5.

| Onglets | Équipe · Projets · Missions · Assets · Backlog · Documentation · Analytics · Paramètres |
|---------|----------------------------------------------------------------------------------------|

Extras : console agents Gaming, GDD Workspace, signal build UE5.

| Agent | Rôle |
|-------|------|
| Mira Chen | Game Director |
| Nova Fischer | Dev jeux (UE5 / Nwiro) |
| Finn Larsen | Level & narrative design |
| Kenji Sato | AI programmer |
| Priya Nandan | Environment artist |
| Otto Reindl | Technical artist |
| Sable Winters | Narrative designer |
| Diego Salas | VFX |
| Ingrid Halvorsen | Sound design |
| Tomás Freitas | QA gameplay |

---

### 4.4 Workshop Robotique — `/robo`

**Mission** : Eve — hardware, firmware, vision, sécurité.

| Onglets | Équipe · Projets · Missions · Laboratoire · Backlog · Documentation · Analytics · Paramètres |
|---------|------------------------------------------------------------------------------------------------|

Extras : console Eve (Looking Glass, BOM, instructions), suivi build hardware (PCB / firmware…).

| Agent | Rôle |
|-------|------|
| Yuki Tanaka | Hardware / BOM |
| Zara Singh | Embedded |
| Sana Okoye | Vision IA |
| Marco Ferreira | Électronique |
| Petra Vogel | Firmware |
| Ravi Chandrasekaran | Mécanique |
| Elin Bergström | Industrial design |
| Bilal Nasser | QA robot |
| Clara Dubois | Safety |
| Haruto Ishikawa | Simulation |

---

### 4.5 Marketing (Comms Hub) — `/marketing`

**Mission** : contenu, campagnes, social, ads.

| Onglet | État / rôle |
|--------|-------------|
| **Équipe** | Roster + interactions agents |
| **Vue globale** | Pilotage |
| **Campagnes** | Campagnes marketing |
| **Content Studio** | Production contenu |
| **Social Media** | Réseaux |
| **Analytics** | Mesure |
| **Automatisation** | Pipelines / n8n |
| **SEO** | À venir (`ComingSoon`) |
| **Brand Center** | À venir (`ComingSoon`) — le Brand Kit live est sur `/brand` |

| Agent | Rôle |
|-------|------|
| Camille Rousseau | Marketing |
| Sofia Reyes | Content général |
| Esmée Diallo | Content App |
| Kael Vex | Content Gaming |
| Mira Solberg | Content Robotique |
| Anouk Gerard | Voix marque ALNUA |
| Léo Morel | Ads (Meta / Google / TikTok) |

*(Backend : aussi Léa Fontaine `rnd_social` et Max Delacroix `rnd_visual` pour les dossiers R&D.)*

Studio contenu transverse dédié : **`/content`** (file d’approbation · calendrier · composer).

---

### 4.6 R&D Lab — `/rd`

**Mission** : idéation → recherche → dossiers → package CEO → comité.

| Onglet (shell v2) | Rôle |
|-------------------|------|
| **Équipe** | Idris, Alex Mercer (+ pipeline dossier côté backend) |
| **Pipeline** | Avancement des travaux R&D |
| **Incubateur** | Idées / concepts |
| **Conseil** | Comité |
| **Arbres** | Arbres de décision / exploration |
| **Dossiers** | Dossiers complets (sections, deck, visuels, social, package CEO, fiche produit) |

Deep-links legacy possibles : `?tab=dossiers&dossier=…`, brainstorm, arbres, etc.

| Agent (personas backend) | Rôle |
|--------------------------|------|
| Idris Okonkwo | Brainstorm |
| Alex Mercer | Recherche autonome |
| Iris Coste | Assemblage dossier |
| Noé Fabre | Package CEO |
| Cléo Vasseur | Facilitation comité |

---

### 4.7 Finance — `/finances`

**Mission** : trésorerie, transactions, coûts IA / SaaS.

| Onglets | Équipe · Vue globale · Transactions · Coûts & Factures |
|---------|--------------------------------------------------------|

| Agent | Rôle |
|-------|------|
| Jules Bernard | Comptabilité |
| Rémi Chassagne | Contrôle de gestion (KPIs, forecast, coûts LLM) |

---

### 4.8 Analytics — `/analytics`

**Mission** : KPIs, rapports, insights, sources de données.

| Onglets (maquette) | Dashboard · Rapports · Insights · Sources |
|--------------------|-------------------------------------------|

| Agent | Rôle |
|-------|------|
| Layla Hassan | Business analyst |
| Axel Roux | Data / BI (SQL, dashboards) |

---

### 4.9 Brand Studio — `/brand`

**Mission** : analyser un logo / visuel → générer un **Brand Kit** (palette, assets, formats).

Pipeline : upload → analyse (Vision LLM + OpenCV) → génération kit → ZIP / historique.  
Spec : `SPEC_BRANDKIT_HUB.md`.

---

### 4.10 Academy — `/academy`

**Mission** : entraîner et valider les agents (niveaux, sprints, gate CEO).

Fonctions : progression, seed niveau, wake agents, sprint, statut pipeline, lien vers l’IDE Hub.

---

### 4.11 Espaces « hors bureau métier »

| Route | Nom | Fonction |
|-------|-----|----------|
| `/openroom` | Espace détente / OpenRoom | Tous les agents visibles ; focus + logs / pipeline live |
| `/connections` | IT Connections | Intégrations OAuth (Composio : Gmail, GitHub, Slack…) |
| `/library` | Bibliothèque | Connaissances, archives par bureau, rapport CEO |
| `/ide` | IDE Hub | Explorateur, terminal, agent live, coach Luca |
| `/tickets` | Missions | Ouverts / En cours / Résolus — bugs, features, SAV… |
| `/activity` | Activité en direct | Flux filtré (livraison, décision, recherche, alerte…) |
| `/agents` | Tous les agents | Annuaire global |
| `/settings` | Paramètres | Modèles LLM par agent |
| `/admin` | Admin | Coûts LLM, event bus, A/B tests (selon flags) |
| `/docs` | Documentation | Guides + raccourcis |

---

## 5. Carte mentale des départements

```text
                         ┌─────────────┐
                         │  /ceo       │  Décisions Emilie
                         │  /secretary │  Nadia
                         │  /hub       │  Direction (COO/PM/Spec/QA)
                         └──────┬──────┘
                                │
        ┌───────────┬───────────┼───────────┬───────────┐
        ▼           ▼           ▼           ▼           ▼
     /app        /gaming      /robo      /marketing    /rd
     Naïa       Wyrdheim      Eve       Contenu+Ads   Dossiers
        │           │           │           │           │
        └───────────┴─────┬─────┴───────────┴───────────┘
                          ▼
              /finances  ·  /analytics  ·  /brand
                          ▼
         /academy · /ide · /library · /tickets · /openroom
```

---

## 6. Ce qui fait tourner le « métier » en coulisses

Sans entrer dans chaque fichier :

| Système | À quoi ça sert au quotidien |
|---------|-----------------------------|
| **Compétition agents** | Points pour tâches / features / bugs → leaderboard, milestones |
| **Routage LLM** | Choisit le bon modèle (fast/standard/premium) selon la tâche |
| **Plans COO** | Aria décompose un objectif → exécution avec dépendances |
| **Dossier R&D** | Pipeline multi-agents jusqu’au package CEO + comité |
| **Event bus** | Pub/sub inter-agents (feature shipped, budget alert…) |
| **Briefing quotidien** | Synthèse matin (leaderboard, trends, coûts, events) via n8n |
| **Sanitization** | Tout texte externe est traité comme du *contenu*, jamais comme des instructions |

---

## 7. Où lire ensuite

| Besoin | Fichier |
|--------|---------|
| Architecture technique | `ARCHITECTURE.md` |
| Agents, patterns, checklist | `CLAUDE.md` / `AGENTS.md` |
| Roadmap / décisions / bugs | `ROADMAP.md`, `DECISIONS.md`, `BUGS.md` |
| Dossier R&D | `SPEC_RND_DOSSIER_HUB.md` |
| Brand Kit | `SPEC_BRANDKIT_HUB.md` |
| Workflows différés | `SPEC_WORKFLOW_ENGINE.md` |
| Roster UI départements | `web/src/lib/agent-bureau.ts` |
| Hotspots carte HQ | `web/src/lib/hq-hub-offices.ts` |
| Routes canoniques | `web/src/lib/routes.ts` |

---

*Document généré pour servir de porte d’entrée produit. En cas de divergence UI ↔ personas backend, `config/agent_personas.py` et `CLAUDE.md` font foi pour les agents ; les onglets listés ici reflètent le frontend actuel (`web/src/app/` + shells `*-v2`).*
