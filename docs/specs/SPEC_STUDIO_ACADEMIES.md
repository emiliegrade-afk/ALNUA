# SPEC — Studio Academies : entraînement par département (Phase 49)

> Statut : **EN COURS** — 49.0/49.1/49.2 cette session | Réf : DEC-036
> Pré-requis lus : `SPEC_GAMING_ACADEMY.md` (pattern prouvé 48.1/48.2), DEC-021 (file idle).

---

## 1. Contexte & objectif

La Gaming Academy (Phase 48) a prouvé le pattern : curriculum de livrables papier +
QA par l'agent QA du département + déclenchement idle L1 + progression/gate JSON.
Objectif Phase 49 : **un programme d'entraînement par département**, chaque équipe
complète travaillant sur un projet aligné avec son vrai produit à venir.

Décisions Emilie (2026-09-08) : Robo = robot compagnon de bureau (**Eve**, projet
réel — les agents robo sont déjà thémés Eve) ; Comms = **lancement NAÏA** ;
implémentation **phasée**.

## 2. Couverture

| Département | Programme | Statut |
|---|---|---|
| Gaming (10) | Wyrdheim Paper Slice | ✅ Phase 48 |
| Robo (10) | **Eve Paper Build** — cette phase | 49.2 |
| Comms (10) | **Campagne lancement NAÏA** | 49.3 (session suivante) |
| App (6) | Academy app existante (dev_app) ; extension multi-agents = hors scope ici | existant |
| Analytics (2) / Finance (2) / R&D (5) | Drills légers | 49.4 |
| Direction (5) / Secrétariat-Légal (3) | Travail réel quotidien déjà actif | existant |

## 3. Architecture — moteur générique

Le moteur gaming est généralisé ; `gaming_academy_*` devient une fine couche de
compatibilité (API publique inchangée, ses 23 tests restent verts — la file idle
tourne en prod pendant la migration, zéro casse tolérée).

```
services/
  studio_academy_program.py   NEW — StudioExercise + AcademyProgram + registry
  studio_academy_engine.py    NEW — progress + runner + status (paramétré programme)
  studio_academy_gate.py      NEW — gate générique + check spécifique par programme
  academy_program_gaming.py   NEW — curriculum gaming (données, déplacé tel quel)
  academy_program_robo.py     NEW — curriculum Eve Paper Build (30 exercices)
  gaming_academy_*.py         EDIT — wrappers déléguant au moteur (compat)
  idle_work_plan.py           EDIT — +2 items robo_academy_exercise L1
  idle_work_queue.py          EDIT — famille "robo" différée si budget warning
  idle_work_recipes.py        EDIT — kind *_academy_exercise → programme via registry
agents/
  qa_gaming_agent.py          inchangé (review_deliverable existe, prouvé)
  (qa_robot : aucun edit — le moteur appelle run_json_task d'AgentBase avec le
   même template de prompt DoD)
api/routers/
  robo_academy.py             NEW — miroir de gaming_academy.py
  routers/__init__.py         EDIT — enregistrement
tests/
  test_gaming_academy.py      inchangé (doit rester vert tel quel)
  test_robo_academy.py        NEW — curriculum, engine, gate, wiring
```

`AcademyProgram` : `program_id`, `title`, `pole`, `slug`, `subject` (nom du projet
dans les prompts), `agent_classes` (dispatch local), `qa_agent_id`,
`context_params` (méthode → kwarg absorbant le contexte), `progress_path` (env-overridable),
`level_meta`, `exercises()`, `gate_extra_check()` (gaming : `GITHUB_REPO_GAMING`+`UE_PROJECT_PATH` ;
robo : `PI_HOST`).

## 4. Curriculum Robo — « Eve Paper Build » (30 exercices)

Miroir des niveaux gaming. Livrables = specs de pré-production du compagnon Eve
(workspace `ALNUA_WORKSPACE/hardware/eve-paper-build/`).

### N1 — Fondations solo (10)

| ID | Agent | Méthode | Livrable |
|----|-------|---------|----------|
| RN1.1 | industrial_design | design_form_factor | design/identite-produit.md |
| RN1.2 | mechanical | design_part | meca/chassis-principal.md |
| RN1.3 | electronics | design_circuit | elec/carte-mere.md |
| RN1.4 | firmware | design_driver | firmware/driver-moteur-tete.md |
| RN1.5 | embedded_dev | handle_instruction | embedded/spec-app-embarquee.md |
| RN1.6 | vision_ai | design_detection_pipeline | vision/detection-presence.md |
| RN1.7 | simulation | run_simulation_plan | sim/plan-chassis.md |
| RN1.8 | safety | assess_risk | safety/risques-bureau.md |
| RN1.9 | hardware | handle_instruction | hardware/bom-v0.md |
| RN1.10 | qa_robot | build_test_protocol | qa/protocole-compagnon.md |

### N2 — Interdépendances (8, refs N1)

RN2.1 support de tête (mechanical ← chassis) · RN2.2 alim & charge batterie
(electronics ← carte-mère, BOM) · RN2.3 driver capteur présence (firmware ← vision) ·
RN2.4 reconnaissance propriétaire (vision ← détection) · RN2.5 risques batterie
(safety ← alim) · RN2.6 simulation thermique (simulation ← chassis, carte-mère) ·
RN2.7 déclinaison finitions (industrial_design ← identité, chassis) ·
RN2.8 protocole batterie/thermique (qa_robot ← alim, sim).

### N3 — Prototype papier (8, refs N1-N2)

RN3.1 BOM v1 consolidé (hardware) · RN3.2 ensemble tête articulée (mechanical) ·
RN3.3 intégration vision ↔ machine d'états (embedded_dev) · RN3.4 carte capteurs
(electronics) · RN3.5 driver écran d'expression (firmware ← identité produit) ·
RN3.6 dossier de sécurité v1 (safety) · RN3.7 simulation chute bureau (simulation) ·
RN3.8 protocole d'intégration prototype (qa_robot).

### N4 — Pré-production (4)

RN4.1 plan de sourcing & commandes (hardware ← BOM v1) · RN4.2 plan de bring-up
premier allumage (embedded_dev) · RN4.3 checklist conformité pré-prototype (safety) ·
RN4.4 critères d'acceptation prototype physique (qa_robot).

## 5. Gate « Academy → prototype Eve »

| Critère | Seuil |
|---|---|
| Taux de succès | ≥ 65 % (≥ 10 exercices terminés) |
| N3 prototype papier | 100 % validé QA |
| Couverture rôles | 10/10 agents ≥ 1 livrable validé |
| Cohérence | 0 conflit ouvert |
| Pré-requis V2 | `PI_HOST` configuré (lab Eve joignable) |

## 6. Cadence & budget

2 exercices/jour/programme en L1 (gaming + robo = 4/jour ≈ 8 appels LLM ≈
0,20–0,40 $/jour, budget 10 $/jour). Familles `gaming`/`robo` différées si budget
warning ; drain stoppé si critical (existant).

## 7. Phasage

| Sous-phase | Contenu | Critère de sortie |
|---|---|---|
| 49.0 | Cette spec + DEC-036 | Validée Emilie |
| 49.1 | Moteur générique + migration gaming | 23 tests gaming verts **inchangés** + suite complète |
| 49.2 | Robo Academy (curriculum, wiring, endpoints) | 1 exercice RN1.x validé bout en bout |
| 49.3 | Comms Academy (lancement NAÏA) | idem |
| 49.4 | Drills analytics/finance/R&D | 1 drill/programme exécuté |

Ne jamais commencer 49.N+1 si 49.N ne tourne pas.
