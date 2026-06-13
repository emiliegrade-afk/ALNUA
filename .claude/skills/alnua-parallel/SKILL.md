# ALNUA Parallel — Exécution Multi-Agents Simultanée

Lance plusieurs agents en parallèle via `services/parallel_runner.py`. Inspiré de oh-my-claude (ultrawork).

---

## Import

```python
from services.parallel_runner import run_agents_parallel_sync, AgentTask
```

---

## Usage de base

```python
results = run_agents_parallel_sync([
    AgentTask(
        agent_id="analyst_business",
        method="strategic_brief",
        kwargs={"topic": "Lancement", "context": "...", "decision_needed": "Go/No-go ?"},
        task_label="Layla — brief",
    ),
    AgentTask(
        agent_id="analyst_data",
        method="sql_query",
        kwargs={"question": "KPIs semaine ?", "schema_context": "...", "db_type": "postgresql"},
        task_label="Axel — SQL",
    ),
    AgentTask(
        agent_id="content",
        method="handle_instruction",
        kwargs={"instruction": "Rédige le post LinkedIn pour le lancement"},
        task_label="Sofia — LinkedIn",
    ),
])

# Résultat
for r in results["results"]:
    if r["success"]:
        print(f"{r['label']}: {r['result']}")
    else:
        print(f"{r['label']} ERREUR: {r['error']}")
```

---

## Helpers pré-configurés

```python
# Analytics Room : Layla + Axel en parallèle
from services.parallel_runner import run_analytics_room
result = run_analytics_room(
    product="NomadApp",
    business_question="Devrait-on lancer le premium en Q3 ?",
    sql_question="Combien d'utilisateurs actifs ce mois ?",
    schema_context="Table users(id, created_at, last_active, plan)...",
)

# Content Sprint : Camille + Sofia en parallèle
from services.parallel_runner import run_content_sprint
result = run_content_sprint(
    topic="Nouveau système de scoring agents",
    product="ALNUA Hub",
    target="Développeurs indé / studio gaming solo",
)
```

---

## Endpoint API

```bash
# Lancement parallèle générique
POST /services/parallel/run
{
  "tasks": [
    {"agent_id": "analyst_business", "method": "market_analysis",
     "kwargs": {"product": "X", "market": "Y"}, "task_label": "Market"},
    {"agent_id": "marketing", "method": "handle_instruction",
     "kwargs": {"instruction": "Stratégie lancement X"}, "task_label": "Strategy"}
  ],
  "max_concurrent": 3
}

# Analytics Room
POST /services/parallel/analytics-room
{"product": "...", "business_question": "...", "sql_question": "...", "schema_context": "..."}

# Content Sprint
POST /services/parallel/content-sprint
{"topic": "...", "product": "...", "target": "..."}
```

---

## Points compétition

Chaque tâche réussie déclenche automatiquement `add_points(agent_id, "task_completed")`.
Le résultat inclut `total_points_awarded` — Rémi (Contrôleur) peut l'auditer.

```python
result["total_points_awarded"]  # Points totaux distribués en une session parallèle
result["success_count"]         # Agents ayant réussi
result["failure_count"]         # Agents ayant échoué
result["total_duration_ms"]     # Durée totale (pas la somme — c'est parallel !)
result["slowest_ms"]            # Goulot d'étranglement
```

---

## Contraintes et limites

- `max_concurrent` défaut = 5 — ne pas dépasser 10 (coûts OpenRouter + timeout Supabase)
- Les méthodes agents sont **synchrones** — elles tournent dans un thread executor
- `fail_fast=True` arrête à la première erreur (utile pour les pipelines critiques)
- Chaque agent instancie sa propre connexion DB — éviter >8 agents simultanés sur Supabase free tier
- Poids des tokens : une session parallèle de 5 agents = 5× le coût d'un appel séquentiel

---

## Pattern avancé : waterfall avec parallèle

```python
# Étape 1 : brief stratégique (séquentiel — décision bloquante)
coo = COOAgent()
brief = coo.brief("Lancement Q3", "Contexte...")

# Étape 2 : exécution en parallèle basée sur le brief
results = run_agents_parallel_sync([
    AgentTask("dev_app", "handle_instruction",
              {"instruction": brief["result"]["action_items"][0]}),
    AgentTask("marketing", "handle_instruction",
              {"instruction": brief["result"]["action_items"][1]}),
    AgentTask("content", "handle_instruction",
              {"instruction": brief["result"]["action_items"][2]}),
])
```
