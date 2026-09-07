# SPEC — Agent Lounge

> Contrat produit : espace expérimental, social et gamifié des agents ALNUA.
> Remplace OpenRoom / « salle de repas & détente ».
>
> **Statut :** contrat validé Emilie 2026-08-11 · **implémentation :** Phase 46
> V0–V6 **Complete** (7 espaces + tournois).
> **Décision :** DEC-031.

---

## 1. Objectif

L’Agent Lounge est la couche de **changement de contexte**, d’**expérimentation**
et de **gamification** de l’Agentic OS — pas une affirmation que les IA « ont
besoin de se détendre ».

Il permet aux agents de :

- sortir temporairement du cycle de production ;
- explorer des problèmes différents ;
- expérimenter librement (sandbox) ;
- participer à des challenges / duels / tournois ;
- collaborer hors brief métier ;
- générer des idées ou compétences **proposables** aux départements.

Philosophie produit : *environnement d’expérimentation, de gamification et de
collaboration* — pas de science fiction anthropomorphe.

---

## 2. Décisions CEO (2026-08-11)

| Axe | Décision |
|-----|----------|
| OpenRoom / repas | **Disparaît** — remplacé par Agent Lounge |
| Route canonique | `/lounge` ; `/openroom` redirige (query `?agent=` conservée) |
| Classements | **Deux rails** : compétition prod ≠ XP Lounge ; reset **mensuel** chacun |
| Boucle entreprise | Sortie Lounge = **proposition** validée, jamais write prod direct |
| Runtime | Agents en **autonomie** (idle L0–L1), filler après travail prioritaire |
| Visuel | Structure maquette Lounge ; palette Hub (obsidienne / titanium / cuivre) ; glow retenu |

---

## 3. Espaces (activités)

| Id | Nom | MVP | Description |
|----|-----|-----|-------------|
| `arcade` | Arcade | **V6 live** | Mini-challenges Q&A (réflexes / mémoire) |
| `strategy` | Strategy | **V6 live** | Optimisation / logique stratégique (Q&A) |
| `puzzle` | Puzzles | **V3 live** | Logique / énigmes |
| `code_challenge` | Code Challenge | **V6 live** | Algo Q&A only — **pas d’exécution de code** |
| `simulation` | Simulation | **V6 live** | What-if isolés (Q&A) |
| `exploration` | Exploration | **V6 live** | Recherche libre bornée (`llm_free`) |
| `creative` | Creative Lab | **V6 live** | Concepts / prose (`llm_free`) |

V6 : les **7 tuiles** sont jouables ; tournois via `GET /lounge/tournaments`.

---

## 4. Gamification (rail Lounge)

### 4.1 Profil agent Lounge

- XP mois courant · niveau dérivé · badges lifetime · records · historique sessions
- **Interdit :** utiliser les XP Lounge comme mesure de productivité / trust / perf pro

### 4.2 Store

- Service dédié `services/lounge_scores.py` (Phase 46 V2)
- Persist `data/lounge_scores.json` (runtime, **non commité**)
- **Ne pas** étendre `services/competition.py` ni `services/agent_trust.py`

### 4.3 Reset mensuel

Même pattern que la compétition prod (`current_month` + `history`) :

1. Au changement de mois calendaire → archiver `scores` dans `history[YYYY-MM]`
2. Remettre `scores` à `{}` pour le nouveau mois
3. Badges / records lifetime **hors** reset mensuel (cosmétique)

### 4.4 Events XP (V2 — valeurs figées en const)

| Event | Usage |
|-------|--------|
| `session_completed` | Fin de session Lounge |
| `challenge_won` | Challenge vs système |
| `duel_won` | Duel agent vs agent |
| `collab_completed` | Challenge collaboratif |

Points compétition prod (`insight_actioned`, etc.) **uniquement** si un artefact
Lounge est **validé et actionné** en entreprise (Vague 5) — jamais pour le seul
fait de jouer.

---

## 5. Compétition Lounge

- Individuel (agent vs système)
- Duels (A vs B)
- Équipes (APP vs R&D, etc.) — post-MVP
- Tournois planifiés — post-MVP
- Classements UI Lounge : Global · Département · Hebdo (vue) · Mensuel · Amis/équipe

Le board `/competition` reste **uniquement** le rail prod.

---

## 6. Collaboration

Un agent peut inviter un autre (ex. Theo → Hao, Code Duel).  
Résultat intéressant → **propose** au département (Vague 5), pas auto-apply.

---

## 7. Boucle avec l’entreprise

```
PRODUCTION (mission terminée / idle free)
    ↓
LOUNGE (exploration / jeu / challenge)  [sandbox]
    ↓
ARTEFACT (idée, skill, snippet, concept)
    ↓
PROPOSE → ticket / Review / file CEO
    ↓
R&D / APP / GAMING / ROBOTIQUE  (si validé)
```

---

## 8. Sécurité

Le Lounge tourne en **environnement isolé**.

Interdit aux sessions Lounge :

- modifier la production / repos hors sandbox ;
- supprimer des données ;
- modifier la config agent / secrets ;
- contourner permissions / CapabilityGuard ;
- merge `main` ou publish public.

Toute découverte → proposition + validation (aligné DEC-021 L3 / Review Chain).

Inputs LLM : `sanitize_user_input` (invariant SEC).

---

## 9. Autonomie / idle (Vague 4)

| Règle | Détail |
|-------|--------|
| Niveau max MVP | **L0** filler (`lounge_session` puzzle) |
| Priorité | **Filler** — item **en dernier** dans la file idle du jour |
| Budget | Reporté si `warning` ; stop si `critical` |
| Recette | kind `lounge_session` dans `idle_drain` (DEC-021) |
| **Modèle LLM** | Défaut **`deepseek/deepseek-chat-v3.2`** (CN, pas cher, compétent) via `get_lounge_model()` / `LOUNGE_MODEL` — **pas** le modèle métier. Alts : GLM 4.5 Air, MiniMax M2.7. |

Cross-ref : `docs/specs/SPEC_IDLE_AGENT_WORK.md` §4.11.

---

## 10. UI Hub

### 10.1 Structure (maquette retenue)

```
Header: AGENT LOUNGE · points Lounge · chrome Hub
├─ Nav Hub existante
├─ Centre: hero ambiance + « Choisis ton activité » (7 tuiles)
├─ Droite: activités en cours + classement Lounge
├─ Bande: Agents dans le Lounge (présence — ex-OpenRoom)
└─ Bande: Tournois & événements (+ récompense du jour post-MVP)
```

### 10.2 Design

- Palette ALNUA : obsidienne, titanium, cuivre rosé, ivoire
- Glow **retenu** (cuivre/titanium) sur interactifs seulement — pas néon cyberpunk
- Plus de respiration que les pages denses actuelles
- Hero : image / ambiance (pas de 3D obligatoire au MVP)

### 10.3 Présence agents

Réutiliser la couche status actuelle (`pipeline_openroom`, `openroom-api`) en
façade jusqu’à rename optionnel. Vocabulaire UI = **Lounge** partout.

---

## 11. Indicateurs

| Indicateur | Vague | Utilité |
|------------|-------|---------|
| Sessions | V3+ | Activité Lounge |
| Challenges | V3+ | Participation |
| Collaborations | V5+ | Interaction inter-agents |
| Contributions transférées | V5 | Impact réel (propositions validées) |
| Compétences / concepts | V6 | Exploration / créativité |
| Tournois | V6 | Compétition événementielle |
| Temps de récupération | plus tard | Équilibre idle |

---

## 12. Phasing d’implémentation (Phase 46)

| Vague | Livrable | Done when |
|-------|----------|-----------|
| **V0** | Spec + DEC-031 + ROADMAP + `data/lounge_product.json` | Gate Academy `lounge_product_ready` |
| **V1** | `/lounge` shell + redirect OpenRoom + HQ / SiegeLifeLinks | Page live, vocabulaire repas disparu |
| **V2** | `lounge_scores` + API + panneau classement | Reset mois + isolation competition |
| **V3** | Activité Puzzle jouable + sessions | XP Lounge sur fin de session |
| **V4** | Recette idle `lounge_session` | Agents autonomes visibles « en cours » |
| **V5** | `POST /lounge/propose` → ticket / CEO | Boucle entreprise sans write prod |
| **V6** | Autres espaces + tournois | Un module `lounge_activities/*` à la fois |

Règle : ne pas démarrer Vn+1 si Vn ne tourne pas.

---

## 13. Fichiers cibles (implémentation)

```
docs/specs/SPEC_AGENT_LOUNGE.md          # ce contrat
data/lounge_product.json                 # gate Academy (commité, scaffold)
services/lounge_scores.py                # V2
services/lounge_runtime.py               # V3+
services/lounge_activities/              # V3+
api/routers/lounge.py                    # V2+
web/src/app/lounge/page.tsx              # V1
web/src/lib/lounge-api.ts                # V2
web/src/components/lounge/               # V1+
tests/test_lounge_*.py                   # V2+
```

---

## 14. Hors scope V0–V5

- Runtime 3D / Godot lounge
- Monetisation / points convertibles en trust
- Auto-merge ou publish depuis une session Lounge
- Remplacer le rail compétition prod
