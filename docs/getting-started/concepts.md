# Concepts ALNUA Hub (produit)

Vocabulaire pour utiliser le Hub au quotidien.  
Pour le mode d’emploi écran par écran → [manuel utilisateur](../guides/user-manual.md).

---

## Architecture en 3 couches (vue simple)

```text
Navigateur (web/)  →  API FastAPI (api/)  →  Agents + services
```

Tu interagis presque toujours avec le **navigateur**. L’API et les agents travaillent derrière.

Ports locaux habituels : web **3000**, API **8003**.

---

## Agent

Un **agent** = un collaborateur virtuel avec :

- un **prénom / persona** (ex. Aria Voss),
- une **room** (bureau),
- un **rôle** (COO, QA, dev…),
- souvent un **tier** de modèle (fast / standard / premium).

Tu lui donnes une intention en langage naturel ; il répond avec un livrable ou un plan.  
Les agents « compétitifs » gagnent des points — c’est du gamification interne, pas une note scolaire pour toi.

---

## Room & pôle

- **Room** = bureau dans le plan HQ (Direction, Secrétariat, APP, Gaming…).
- **Pôle** = département produit (`/app`, `/gaming`, `/rd`…) avec une UI d’équipe + missions.

Même entreprise, plusieurs bureaux : tu changes de contexte en changeant de page / de carte HQ.

---

## Workflow

Un **workflow** = une chaîne d’étapes (souvent multi-agents) avec des points de validation.

Sur `/ceo`, tu vois ce qui **attend ta décision** (approve / reject).  
Ce n’est pas la même chose qu’un ticket : un ticket = une tâche ; un workflow = un processus.

---

## Ticket / mission

Entrée dans le backlog (`/tickets` ou onglet Missions d’un pôle) : qui fait quoi, pour quel projet, éventuellement échéance / points.

---

## Arbre (R&D)

**Mindmap d’hypothèses.** Tu explores des branches autour d’une idée.  
Tu **gardes** ou tu **tues** une branche. Ce n’est pas encore un projet.

Où : `/rd` → onglet **Arbres**.

---

## Dossier (R&D)

Livrable structuré issu d’une branche prometteuse (comité, deck, social, finance…).  
Toujours du **labo** jusqu’à décision CEO puis dispatch vers un pôle de build.

Où : `/rd` → onglet **Dossiers**.

---

## Trust vs compétition

| | **Trust** (`/trust`) | **Compétition** |
|--|----------------------|-----------------|
| Mesure | Fiabilité / autonomie | Points / milestones |
| Usage | Combien le Hub peut laisser l’agent agir seul | Motivation interne agents |

Les deux coexistent ; ne pas les confondre.

---

## Briefing

Synthèse du matin (ops + optionnellement brief COO Aria) sur `/briefing`  
(accès pratique : plan HQ → salle de réunion).

---

## Sécurité (rappel)

- Texte utilisateur / titres externes → assainis avant prompt LLM.
- Clé `X-Hub-Key` pour les appels API protégés.
- **Sentry** = crashs apps ; **Security Sentinel (Hugo)** = hygiène / intrusion Hub.

Détail : [SECURITY_HARDENING.md](../guides/SECURITY_HARDENING.md), [auth](../api/authentication.md).

---

## API — pas de double contrat `/v1`

Les routes utiles sont montées **une seule fois** (ex. `/health`, `/workflows/...`).  
Un préfixe `/v1` peut encore être toléré côté middleware sur certains chemins, mais **documente et utilise les chemins sans `/v1`**.

---

## Mémoire & bibliothèque

Les agents peuvent mémoriser des leçons (Mem0) et s’appuyer sur la **bibliothèque** (`/library`) — sujets / notes, pas un dump de chat brut.

---

## Aller plus loin

- [Manuel](../guides/user-manual.md)
- [Premiers 15 minutes](./first-15-minutes.md)
- [Installation](./installation.md)
- Specs techniques : `docs/specs/` (pour Cursor / dev, pas pour le quotidien CEO)
