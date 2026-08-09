# ALNUA Workflow Engine — Company OS

> Moteur de recettes Hermes-lite : un chef d'orchestre, étapes séquentielles, statuts unifiés, blocage sur `ECART`.

## Contrat d'autonomie (Emilie = CEO)

| **Emilie décide** | **Hub exécute seul** |
|-------------------|----------------------|
| Quel produit / idée développer | Fix bugs, pipeline coding, PR |
| Brainstorming & exploration (arbres R&D) | Ops multi-repo (`run_ops`) |
| Validation CEO dossiers (`ready_for_ceo`) | Auto-issues GitHub si erreurs ouvertes |
| Pivot / rejet / priorités stratégiques | Dispatch post-approbation → issues Hub |
| SAV sensible (plus tard) | Brief hebdo ops + rappel queue CEO |

**100 % autonome** = tout sauf le *quoi* stratégique et la validation CEO.

## Objectif

Unifier les pipelines dispersés (`orchestration`, `plan_executor`, dossiers R&D, `app_factory`, `fix_pipeline`) sous **un même contrat** :

| Statut | Signification |
|--------|---------------|
| `PENDING` | Pas encore exécuté |
| `IN_PROGRESS` | En cours (une seule étape à la fois) |
| `OK` | Terminé, critères satisfaits |
| `A_VERIFIER` | Terminé mais points à valider par Emilie |
| `ECART` | **Blocage** — le workflow s'arrête, action humaine requise |

Règles :
- Seul l'agent **head** (COO, rnd_ceo, qa…) délègue ; les étapes appellent des services existants.
- Persistance : `data/workflow_runs/{run_id}.json`
- Audit : chaque étape garde `started_at`, `finished_at`, `detail`, `gaps[]`

## Recettes (catalogue)

| ID | Nom | Head | Priorité | Statut |
|----|-----|------|----------|--------|
| `explore` | Arbres R&D (hypothèse) | rnd_agent | — | ✅ via `rnd_hypothesis_tree` |
| `dossier_ceo` | Dossier → package CEO | rnd_ceo_agent | **P0** | ✅ MVP |
| `ship_app` | Release app (registry) | qa + coo | **P0** | ✅ MVP |
| `ship_hub` | Release Hub (registry) | qa + coo | **P0** | ✅ MVP |
| `run_ops` | Surveillance multi-repo | coo | **P0** | ✅ MVP |
| `sav_lite` | SAV Nadia + fiche produit | secretary | P1 | ✅ Implémenté (`services/sav_lite.py` + handlers) |
| `ship_game` | Release jeu | game_director | P2 | ✅ MVP (handlers `ship_game` dans `workflow_engine`) |
| `ship_robo` | Release robotique | hardware | P2 | ✅ MVP (handlers `ship_robo` dans `workflow_engine`) |
| `fiscal` | Déclarations agentiques | accounting | Later | Hors scope |
| `semaine` | Brief hebdo ops + queue CEO | coo | **P0** | ✅ MVP |

> Aligné code le 2026-08-09 (Phase A / Audit 002) — le catalogue ci-dessus était
> resté sur « À faire » pour `sav_lite` / `ship_*` alors que les `WorkflowRecipe`
> existent déjà dans `services/workflow_engine.py::RECIPE_CATALOG`.


## Recette `dossier_ceo`

**Contexte** : `{ "dossier_id": "uuid", "force": false }`

| Étape | Handler | ECART si |
|-------|---------|----------|
| `validate_sections` | Contrôle sections obligatoires validées | < 4 sections core validées |
| `validate_committee` | CR comité présent | CR < 40 caractères |
| `generate_package` | `RndCeoAgent.generate_package` | `CeoPackageNotReadyError` |
| `control_gaps` | Audit package (recommandation, risques, finance) | gaps critiques |
| `mark_ready` | `status → ready_for_ceo` si OK | — |

## Recette `ship_app`

**Contexte** : `{ "slug": "nomad", "target_status": "beta"|"prod" }`

| Étape | Handler | ECART si |
|-------|---------|----------|
| `validate_registry` | App dans registry + path local | slug inconnu ou path absent |
| `qa_readiness` | Erreurs coding ouvertes pour ce repo | > 3 erreurs open |
| `update_lifecycle` | `lifecycle_status` dans registry | — |
| `notify_shipped` | `event_bus.feature_shipped` | — |

## Recette `run_ops`

**Contexte** : `{ "branch": "app"|"gaming"|"robotics"|null }` (filtre optionnel)

| Étape | Handler | ECART si |
|-------|---------|----------|
| `scan_registry` | Liste apps enabled | aucune app |
| `scan_errors` | `coding_errors.json` par `repo_slug` | — |
| `watchdog_status` | Résumé + repos sans mapping watchdog | — |

## Mapping services existants

```
workflow_engine.run_workflow("dossier_ceo", ctx)
  → rnd_repository, rnd_ceo_agent, rnd_pipeline

workflow_engine.run_workflow("ship_app", ctx)
  → app_registry, coding_error_journal, event_bus

workflow_engine.run_workflow("run_ops", ctx)
  → app_registry, coding_error_journal, bug_watchdog paths

orchestration.WORKFLOW_CATALOG  — chaînes n8n (complémentaire, pas remplacé)
plan_executor                   — dispatch multi-agents post-CEO (inchangé)
rnd_hypothesis_tree             — EXPLORE (arbor-lite)
```

## API

```
GET  /workflows/recipes          — catalogue
GET  /workflows/runs             — historique récent
GET  /workflows/runs/{run_id}    — détail run
POST /workflows/run              — { recipe_id, context }
```

## Portfolio registry (extension)

Champ `lifecycle_status` : `idea` | `build` | `beta` | `prod`

Branch : `app` | `gaming` | `robotics` | `hub` | `other`

## Phases suivantes

1. ~~**P1** — `sav_lite`~~ ✅ fait
2. ~~**P1** — `semaine`~~ ✅ fait
3. ~~**P2** — `ship_game` / `ship_robo`~~ ✅ MVP fait
4. **UI** — panneau workflows dans Hub CEO / Ops
5. **IA** — DiffusionGemma local (2e SSD) branché sur benchmark existant
6. **Phase 30 ROADMAP** — recettes de **validation** :
   - ~~`content_validation`~~ ✅ MVP (2026-08-09)
   - ~~`campaign_validation`~~ ✅ MVP (2026-08-09)
   - `budget_transfer` (lié Phase 34)
   (+ niveaux d'autonomie 0–3 MVP — voir `ROADMAP.md` Phase 30, DEC-012)
   Extension via `services/workflow_validation_recipes.py` (ne pas grossir
   `workflow_engine.py` — BUG-004).
