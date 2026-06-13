# ALNUA Hub — Architecture & Dev Reference

Tu travailles dans **ALNUA Hub** (`C:\Dev\ALUNA_HUB`), le backend central d'une société virtuelle de 20 agents IA.

---

## Stack

| Couche | Technologie |
|--------|------------|
| API REST | FastAPI — `api/main.py` |
| Agents LLM | OpenRouter via `agents/base.py::LLMClient` |
| Orchestration | CrewAI (tâches complexes multi-agents) |
| Base de données | Supabase (PostgreSQL) — `database/supabase_client.py` |
| Mémoire | Mem0 — `skills/skill_mem0.py` |
| Observabilité | Langfuse — `skills/skill_langfuse.py` |
| Automatisation | n8n (workflows externes) |
| Scores | `services/competition.py` + `data/agent_scores.json` |
| Config modèles | `config/agent_models.py` |
| Config personas | `config/agent_personas.py` |

---

## Structure fichiers

```
agents/
  base.py                    ← LLMClient, run_with_learning, log_agent_action
  coo_agent.py               ← Aria Stern, COO
  spec_agent.py              ← Marcus Webb, Spec Rédacteur
  qa_agent.py                ← Sven Lindqvist, QA
  pm_agent.py                ← Léa Moreau, PM
  dev_app_agent.py           ← Théo Laurent, Dev App
  game_director_agent.py     ← Mira Chen, Game Director
  dev_gaming_agent.py        ← Nova Fischer, Dev Gaming
  brainstorm_agent.py        ← Idris Okonkwo, Brainstorm
  rnd_agent.py               ← Alex Mercer, R&D
  marketing_agent.py         ← Camille Rousseau, Marketing
  content_agent.py           ← Sofia Reyes, Content
  accounting_agent.py        ← Jules Bernard, Comptabilité
  hardware_agent.py          ← Yuki Tanaka, Hardware
  embedded_dev_agent.py      ← Zara Singh, Embedded Dev
  secretary_agent.py         ← Nadia Faure, Secrétaire
  dev_backend_agent.py       ← Hao Chen, Dev Backend
  level_designer_agent.py    ← Finn Larsen, Level Designer
  controller_agent.py        ← Rémi Chassagne, Contrôleur
  analyst_business_agent.py  ← Layla Hassan, Business Analyst
  analyst_data_agent.py      ← Axel Roux, Data Analyst BI

config/
  agent_models.py    ← modèles LLM par agent (fast/standard/premium)
  agent_personas.py  ← AGENT_PERSONAS, ROOMS, TEAMS, get_competitive_context()
  settings.py        ← Settings Pydantic (OPENROUTER_API_KEY, SUPABASE_URL...)

services/
  competition.py     ← get_scores(), add_points(), get_leaderboard()

skills/
  skill_langfuse.py       ← @trace_agent() decorator
  skill_agent_learning.py ← inject_learning_context(), record_task_learning()
  skill_mem0.py           ← mémoire persistante Mem0

api/main.py     ← tous les endpoints FastAPI
web/            ← frontend Next.js/React
```

---

## Pattern agent (à répliquer exactement)

```python
"""[Role] Agent — [Prénom Nom], [Titre] ALNUA."""
from __future__ import annotations
from typing import Any
from agents.base import LLMClient, log_agent_action, parse_json_response
from database.supabase_client import SupabaseClient, get_supabase
from skills.skill_agent_learning import inject_learning_context, record_task_learning
from skills.skill_langfuse import trace_agent

class MyAgent:
    AGENT_NAME = "my_agent"  # doit matcher la clé AGENT_PERSONAS

    SYSTEM_PROMPT = """Tu es [Prénom Nom], [Titre] d'ALNUA.
[Relation avec un autre agent — cross-référence explicite]

Tes spécialités :
- Spécialité 1
- Spécialité 2

Méthode de travail :
[1-2 règles comportement concrètes]

Règles de format :
Réponds en JSON valide structuré.

Relation à la qualité :
[Phrase manifeste courte]"""

    def __init__(self, db: SupabaseClient | None = None, llm: LLMClient | None = None) -> None:
        self.db = db or get_supabase()
        self.llm = llm or LLMClient()

    @trace_agent("my_agent")
    def my_method(self, param: str) -> dict[str, Any]:
        prompt = inject_learning_context(f"...", self.AGENT_NAME, param)
        raw = self.llm.complete(self.SYSTEM_PROMPT, prompt, agent_id=self.AGENT_NAME, temperature=0.4)
        result = parse_json_response(raw)
        log_agent_action(self.db, self.AGENT_NAME, "my_method",
            input_summary=param[:100], output_summary=str(result)[:100])
        try:
            record_task_learning(self.AGENT_NAME, "my_method", str(result)[:300], success=True)
        except Exception:
            pass
        return result
```

---

## LLMClient — paramètres

```python
self.llm.complete(
    system=self.SYSTEM_PROMPT,
    user=prompt,
    agent_id=self.AGENT_NAME,  # résout le modèle via agent_models.py
    temperature=0.3,           # 0.2 SQL/analyse | 0.4 rédac | 0.7 créatif
    max_tokens=4096,           # défaut ; 2000 pour outputs courts
)
```

`LLMClient.chat()` injecte `get_competitive_context()` automatiquement si `persona["competitive"] == True`.

---

## run_with_learning — wrapper universel

```python
from agents.base import run_with_learning
result = run_with_learning("my_agent", "Description tâche", self.my_method, param)
# → exécute la méthode + apprentissage Mem0 + add_points("task_completed", 10pts)
```

---

## Scoring compétition

```python
from services.competition import add_points, get_scores, get_leaderboard

add_points("dev_app", "feature_shipped", note="Landing v2")
# POINT_VALUES:
#   task_completed=10, task_validated=25, feature_shipped=50
#   bug_found_critical=30, bug_fixed=20, review_approved=15
#   document_produced=10, insight_actioned=35

scores = get_scores()      # dict agent_id → int
board  = get_leaderboard() # liste triée + rank + milestone_status
```

Milestones : 100=coffee_break | 200=tier_upgrade_7d | 500=tier_upgrade_30d

---

## Pattern endpoint FastAPI

```python
class MyRequest(BaseModel):
    param: str
    optional: str = ""

@app.post("/agents/my-agent/my-action")
async def my_action(req: MyRequest):
    return {"status": "ok", "result": MyAgent().my_method(req.param)}
```

---

## Rooms & Teams

```
direction         → coo, spec, qa, pm
app_office        → dev_app, dev_backend
gaming_studio     → game_director, dev_gaming
rnd_lab           → brainstorm, rnd_agent
comms_hub         → marketing, content
hardware_workshop → hardware, embedded_dev
accounting_office → accounting, controller
analytics_room    → analyst_business, analyst_data
```

Équipes compétitives (intra-team) : `app` | `innovation` | `finance` | `analytics`

---

## Règles invariantes

- **Pas d'UE5** — aucune intégration Unreal Engine
- `parse_json_response()` obligatoire sur tout output LLM (gère markdown fences)
- `log_agent_action()` obligatoire pour chaque action Supabase
- `@trace_agent("agent_name")` sur chaque méthode publique
- Dégradé silencieux (`try/except pass`) partout sauf l'appel LLM principal
- `data/agent_scores.json` créé automatiquement au premier `add_points()`
