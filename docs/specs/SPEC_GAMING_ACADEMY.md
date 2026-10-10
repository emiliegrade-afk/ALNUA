# SPEC — Gaming Academy (formation autonome du studio)

> Contrat : ce que les agents du Gaming Studio peuvent produire **en autonomie
> encadrée**, miroir de l'Academy app (`dev_app`) — un curriculum d'exercices
> par rôle, avec progression trackée, QA systématique et gate avant production
> Wyrdheim.
>
> **Statut :** proposée 2026-09-08 — en attente validation CEO.
> **Décision :** DEC-034.
> **Parent :** `SPEC_IDLE_AGENT_WORK.md` (DEC-021) — la Gaming Academy se
> déclenche via la file idle, mêmes gates budget/trust. Miroir de
> `services/academy_curriculum.py` + `services/academy_gate.py` (Academy app).

---

## 1. Contexte & objectif

L'Academy app entraîne **un seul** agent (`dev_app`) via 52 exercices de code
(issues GitHub + pipeline). Rien d'équivalent n'existe pour le Gaming Studio :
les 10 agents gaming n'ont aucun mécanisme de travail autonome de fond, et le
repo gaming (`GITHUB_REPO_GAMING` / `UE_PROJECT_PATH`) n'est pas configuré.

Objectif : faire travailler le studio **tous les jours** sur un projet
éducatif commun — le **« Wyrdheim Paper Slice »**, une vertical slice
entièrement conçue sur papier (documents + données structurées), sans moteur —
pour que chaque agent monte en compétence sur son rôle réel avant la
production UE5.8.

**Constats fondateurs (2026-09-08) :**

- Les méthodes métier existent déjà : `LevelDesignerAgent.design_quest /
  design_level / write_lore_entry`, `NarrativeDesignerAgent.write_dialogue`,
  `run_studio_task(title, description)` sur les 5 agents créatifs
  (environment, technical, vfx, sound, ai_programmer),
  `QaGamingAgent.build_test_plan`,
  `GameDirectorAgent / DevGamingAgent.handle_instruction`.
- Le pattern livrables write-only existe : `services/rnd_workspace.py`
  (manifest + validation, Phase 9 dispatch).
- Le pattern progression + gate existe : `academy_progress.py` /
  `academy_gate.py`.

La V1 ne fait que **brancher ces briques entre elles** — aucun nouveau
pattern d'infrastructure.

---

## 2. Choix proposés (à valider par Emilie)

| Axe | Proposition |
|-----|-------------|
| Projet éducatif | **Wyrdheim Paper Slice** — zone tutoriel du vrai jeu, pas un projet jetable : les livrables validés deviennent le canon de pré-production |
| V1 | **Créative, sans UE** : documents + JSON/MD structurés, aucune dépendance repo gaming |
| V2 | **Code C++ Nova** via coding pipeline — seulement après configuration `GITHUB_REPO_GAMING` + `UE_PROJECT_PATH` |
| Déclencheur | File idle du jour (DEC-021) — items `gaming_academy` L1, jamais L3 |
| QA | Tomás (`qa_gaming`) relit chaque livrable contre un DoD par exercice |
| Compétition | Points existants (`task_completed` 10 / `task_validated` 25) |

---

## 3. Niveaux du curriculum

Miroir des niveaux Academy app (N1→N4), difficulté croissante :

| Niveau | Nom | Contenu |
|--------|-----|---------|
| **N1** | Fondations solo | Chaque agent produit ses livrables de base, isolés |
| **N2** | Interdépendances | Les livrables se référencent : la quête de Finn utilise le PNJ de Sable, posé dans le biome de Priya, avec le soundscape d'Ingrid |
| **N3** | Vertical slice papier | Assemblage complet de la zone tutoriel : GDD extract (Mira), quêtes, dialogues, map, VFX, behaviors IA, plan de test |
| **N4** | Pré-production | Package prêt pour UE : conventions de nommage (Otto), specs techniques C++/Blueprints (Nova), plan de build, critères d'acceptation |

Chaque exercice = 1 appel LLM + 1 livrable fichier + 1 relecture QA.
Volume cible MVP : **30 exercices** (3 par agent en moyenne) vs 52 pour l'app.

---

## 4. Curriculum par rôle (N1 indicatif)

| Agent | Exercice N1 | Méthode utilisée | Livrable |
|-------|-------------|------------------|----------|
| Mira (`game_director`) | Vision + pillars de la zone tutoriel | `handle_instruction` | `direction/vision-zone-tutoriel.md` |
| Sable (`narrative_designer`) | Fiche PNJ mentor + dialogue d'accueil | `write_dialogue` | `narrative/pnj-mentor.md` |
| Finn (`level_designer`) | Quête tutoriel « premier pas » | `design_quest` | `quests/quete-tutoriel-01.md` |
| Priya (`environment_artist`) | Concept biome de la zone | `run_studio_task` | `environnement/biome-tutoriel.md` |
| Otto (`technical_artist`) | Conventions assets + budgets perf cibles | `run_studio_task` | `tech-art/conventions-assets.md` |
| Diego (`vfx_artist`) | Concept VFX signature de la zone | `run_studio_task` | `vfx/vfx-signature.md` |
| Ingrid (`sound_designer`) | Soundscape d'ambiance de la zone | `design_soundscape` | `audio/soundscape-tutoriel.md` |
| Kenji (`ai_programmer`) | Behavior PNJ mentor (arbre pseudo/JSON) | `design_behavior` | `ai/behavior-pnj-mentor.md` |
| Nova (`dev_gaming`) | Spec architecture C++ du module quêtes | `handle_instruction` | `dev/spec-module-quetes.md` |
| Tomás (`qa_gaming`) | Plan de test de la zone + relectures | `build_test_plan` | `qa/test-plan-zone-tutoriel.md` |

N2–N4 réutilisent les mêmes méthodes avec des briefs croisés (payload
`context_refs` pointant les livrables validés des niveaux précédents).

---

## 5. Stockage & progression

```
ALNUA_WORKSPACE/gaming-academy/
  gaming-academy.manifest.json      ← état par exercice (pattern rnd_workspace)
  direction/ narrative/ quests/ …   ← livrables par pôle (write-only)
data/gaming_academy_progress.json   ← progression + gate (miroir academy_progress.json)
```

- **Write-only** : jamais de suppression/écrasement d'un livrable validé
  (même règle que Phase 9). Une reprise d'exercice écrit `-v2`.
- Manifest : `exercise_id → {agent_id, status, qa_verdict, path, run_id}`.
- Progression : `current_level`, `done/failed/in_progress` par niveau,
  `success_rate_pct`, timestamps — schéma aligné sur `academy_progress.json`.

---

## 6. Intégration file idle (DEC-021)

- Nouveau kind `gaming_academy_exercise` dans
  `services/idle_work_recipes.py::_execute_one` (handler dédié, mêmes gates
  budget/trust que les autres kinds).
- `services/idle_work_plan.py::build_day_plan` : 1–2 items
  `gaming_academy_exercise` par jour (niveau idle **L1** — livrables = brouillons
  créatifs sans side-effect irréversible, pas besoin de validation CEO).
- Le drain existant orchestre ; le runner exécute
  (`services/gaming_academy_runner.py`) : pick prochain exercice `pending` →
  appel agent → écriture livrable → relecture Tomás → MAJ manifest/progress.
- Famille budget dédiée `gaming_academy` : reportée si `warning`
  (comme `company`/`self_dev`), stoppée si `critical`.
- Points compétition : `task_completed` à l'écriture, `task_validated` si QA OK.

---

## 7. QA & Definition of Done

Chaque exercice embarque un DoD (checklist 3–5 points, ex. « la quête
référence un PNJ existant du canon », « le budget perf respecte les
conventions d'Otto »). Tomás (`qa_gaming.build_test_plan` + relecture LLM
dédiée) rend un verdict structuré :

```json
{"verdict": "validated|rejected", "dod_checks": [...], "feedback": "..."}
```

`rejected` → exercice repassé `pending` avec feedback injecté au prochain
essai (pattern retry-with-learning existant, cap 3 puis échec).

---

## 8. Budget & tiers

- Tiers métier inchangés (`config/agent_models.py`) : fast pour Finn, standard
  pour le gros du studio, premium réservé aux arbitrages de Mira.
- 1 exercice = 1 appel LLM + 1 relecture QA (tier de Tomás) → coût prévisible,
  ~2 appels/exercice, 1–2 exercices/jour en idle.
- Réutilise `cost_monitor` + gates budget idle — **pas** de budget séparé.

---

## 9. Gate « Academy → production Wyrdheim »

`services/gaming_academy_gate.py` (miroir `academy_gate.py`) — critères
pondérés, exposés au cockpit :

| Critère | Seuil indicatif |
|---------|-----------------|
| Taux de succès exercices | ≥ 65 % |
| N3 vertical slice complète | 100 % validée QA |
| Couverture rôles | 10/10 agents ≥ 1 livrable validé |
| Cohérence canon | 0 conflit canon ouvert (relecture Sable) |
| Pré-requis V2 Nova | `GITHUB_REPO_GAMING` + `UE_PROJECT_PATH` configurés |

Gate ouverte = le studio est déclaré prêt pour la production UE5.8 réelle.

---

## 10. Surfaces API / UI (cible)

| Surface | Rôle |
|---------|------|
| `GET /academy/gaming/status` | Progression, exercice en cours, gate % |
| `POST /academy/gaming/wake` | Forcer le prochain exercice (CEO) |
| `GET /academy/gaming/deliverables` | Liste livrables + verdicts QA |
| Carte cockpit `/academy` | Miroir `academy-cockpit.tsx` (lecture seule V1) |

---

## 11. Fichiers impactés (implémentation)

| Fichier | Action |
|---------|--------|
| `services/gaming_academy_curriculum.py` | **NEW** — 30 exercices, `StudioExercise` dataclass (≤ 250 lignes) |
| `services/gaming_academy_runner.py` | **NEW** — exécution 1 exercice + relecture QA (≤ 200) |
| `services/gaming_academy_progress.py` | **NEW** — progression + manifest (≤ 150) |
| `services/gaming_academy_gate.py` | **NEW** — critères gate (≤ 120) |
| `services/idle_work_recipes.py` | EDIT — handler kind `gaming_academy_exercise` |
| `services/idle_work_plan.py` | EDIT — 1–2 items gaming dans `build_day_plan` |
| `api/routers/academy.py` | EDIT — endpoints §10 (section dédiée) |
| `tests/test_gaming_academy.py` | **NEW** — curriculum cohérent, runner mocké, gate, gates budget |

Règle ≤ 300 lignes appliquée dès la création. V2 (Nova C++) : config
`GITHUB_REPO_GAMING`/`UE_PROJECT_PATH` + émission d'issues `[GACADEMY Nx.y]`
sur le repo gaming via le coding pipeline existant — **aucun** nouveau
pipeline. Génération 3D d'assets (props/items) en V2 : **Meshy** retenu
(DEC-035) — `skills/skill_meshy.py`, briefs issus des livrables validés.

---

## 12. Phases

| Phase | Scope | Critère de sortie |
|-------|-------|-------------------|
| 48.0 | Cette spec + DEC-034 | Validée Emilie |
| 48.1 | Curriculum N1–N4 + progress + runner + QA | 1 exercice N1 exécuté bout en bout |
| 48.2 | Intégration idle + endpoints status | Item `gaming_academy` drainé en idle réel |
| 48.3 | Gate + carte cockpit | Gate évaluée et visible |
| 48.4 (V2) | Repo gaming configuré → exercices C++ Nova via pipeline | 1 PR `[GACADEMY]` mergée QA OK |

Ne jamais commencer 48.N+1 si 48.N ne tourne pas.

---

## 13. Hors scope

- Exécution UE5.8 réelle (serveur éditeur, agency) — DEC-017/DEC-020 inchangées
- Génération d'assets binaires (meshes, textures, audio) — concepts textuels
  uniquement
- Publication/store — L3, toujours Emilie (SPEC_IDLE_AGENT_WORK §3)
- Modification des personas ou tiers modèles

---

## 14. Critères d'acceptation

1. Spec + DEC-034 présentes ; ROADMAP Phase 48 référencée.
2. `build_day_plan` produit ≥ 1 item `gaming_academy_exercise` éligible L1.
3. Un exercice N1 exécuté produit : livrable sur disque + verdict QA + manifest
   + progression MAJ (test d'intégration).
4. Budget `warning` → items gaming reportés (test unitaire).
5. Verdict `rejected` ×3 → exercice `failed`, feedback conservé (test).
6. Aucune écriture hors `ALNUA_WORKSPACE/gaming-academy/` et
   `data/gaming_academy_*` (test).

---

## 15. Liens

- `docs/specs/SPEC_IDLE_AGENT_WORK.md` — gates idle (DEC-021)
- `services/academy_curriculum.py`, `services/academy_gate.py` — miroirs app
- `services/rnd_workspace.py` — pattern livrables write-only
- `CLAUDE.md` — roster Gaming Studio
- `DECISIONS.md` — DEC-017, DEC-020, DEC-021, **DEC-034**
- `ROADMAP.md` — Phase 48
