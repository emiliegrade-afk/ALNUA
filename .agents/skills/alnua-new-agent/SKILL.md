# ALNUA New Agent — Template & Checklist

Crée un nouvel agent ALNUA en 6 étapes. Chaque étape est obligatoire.

---

## Étape 1 — Définir l'agent

Avant de coder, réponds à ces questions :
- `AGENT_NAME` (snake_case) : ex. `my_agent`
- Prénom + Nom du persona : ex. `Elena Kovacs`
- Titre : ex. `Legal Analyst`
- Room (dans quelle pièce) : `direction` | `app_office` | `gaming_studio` | `rnd_lab` | `comms_hub` | `hardware_workshop` | `accounting_office` | `analytics_room`
- Team (si compétitive) : `app` | `innovation` | `finance` | `analytics` | `none`
- Tier modèle : `fast` | `standard` | `premium`
- 3-4 méthodes publiques avec leurs paramètres

---

## Étape 2 — Créer `agents/my_agent.py`

```python
"""[Role] Agent — [Prénom Nom], [Titre] ALNUA."""
from __future__ import annotations
from typing import Any
from agents.base import LLMClient, log_agent_action, parse_json_response
from database.supabase_client import SupabaseClient, get_supabase
from skills.skill_agent_learning import inject_learning_context, record_task_learning
from skills.skill_langfuse import trace_agent

class MyAgent:
    AGENT_NAME = "my_agent"

    SYSTEM_PROMPT = """Tu es [Prénom Nom], [Titre] d'ALNUA.
[Agent X] fait [tâche X], toi tu [tâche complémentaire]. [Relation pipeline explicite.]

Tes spécialités :
- Spécialité 1
- Spécialité 2
- Spécialité 3

Méthode de travail :
[Règle comportementale 1 — concrète et distinctive.]
[Règle comportementale 2 — comment tu traites les cas limites.]

Règles de format :
Réponds en JSON valide structuré.

Relation à la qualité :
[Phrase courte et mémorable sur ce qui compte pour toi.]"""

    def __init__(self, db: SupabaseClient | None = None, llm: LLMClient | None = None) -> None:
        self.db = db or get_supabase()
        self.llm = llm or LLMClient()

    @trace_agent("my_agent")
    def method_one(self, param1: str, param2: str = "") -> dict[str, Any]:
        """Description courte de la méthode."""
        prompt = inject_learning_context(
            f"""Instructions pour le LLM.
Paramètre 1 : {param1}
Paramètre 2 : {param2}

Réponds en JSON :
{{
  "field1": "string",
  "field2": ["item1", "item2"],
  "verdict": "string"
}}""",
            self.AGENT_NAME, param1,
        )
        raw = self.llm.complete(
            self.SYSTEM_PROMPT, prompt, agent_id=self.AGENT_NAME, temperature=0.4
        )
        result = parse_json_response(raw)
        log_agent_action(
            self.db, self.AGENT_NAME, "method_one",
            input_summary=param1[:100],
            output_summary=str(result)[:100],
        )
        try:
            record_task_learning(self.AGENT_NAME, "method_one", str(result)[:300], success=True)
        except Exception:
            pass
        return result
```

**Règles SYSTEM_PROMPT :**
- Toujours mentionner au moins un autre agent par nom (cross-référence)
- Section "Tes spécialités" : 3-5 items concrets
- Section "Méthode de travail" : 1-2 règles comportementales, pas génériques
- Section "Relation à la qualité" : une seule phrase, ton distinctif
- Format JSON obligatoire mentionné

**Règles méthodes :**
- `temperature` : 0.2 (SQL/analyse) | 0.3-0.4 (rédac/spec) | 0.5-0.7 (créatif/brainstorm)
- `max_tokens=4096` par défaut, 2000 pour les outputs courts structurés
- `log_agent_action()` obligatoire sur les méthodes principales
- `record_task_learning()` dans try/except (dégradé silencieux)

---

## Étape 3 — Ajouter à `config/agent_models.py`

```python
# Dans AGENT_TIERS :
"my_agent": "standard",  # fast | standard | premium

# Dans AGENT_ID_ALIASES (si l'agent peut être appelé avec plusieurs noms) :
"mya": "my_agent",
"my agent": "my_agent",
```

---

## Étape 4 — Ajouter à `config/agent_personas.py`

```python
# Dans AGENT_PERSONAS :
"my_agent": {
    "first_name": "Elena",
    "last_name": "Kovacs",
    "title": "Legal Analyst",
    "avatar": "👩‍⚖️",
    "room": "direction",
    "team": "none",           # ou "app" | "innovation" | "finance" | "analytics"
    "competitive": False,     # True si dans une équipe compétitive
    "tier": "standard",
    "work_style": "Méticuleuse et littérale — si ce n'est pas dans le contrat, ça n'existe pas.",
    "fear": "L'ambiguïté contractuelle qui devient un litige.",
},

# Dans ROOMS (ajouter dans la room concernée) :
"direction": {
    "label": "Direction",
    "agents": ["coo", "spec", "qa", "pm", "my_agent"],  # ← ajouter ici
},

# Dans TEAMS (si compétitive, ajouter dans la team) :
# Non applicable si competitive = False
```

---

## Étape 5 — Ajouter endpoints dans `api/main.py`

```python
# 1. Import en haut du fichier (bloc imports agents) :
from agents.my_agent import MyAgent

# 2. Modèles Pydantic (avant la section "Dev Logs") :
class MyAgentMethodOneRequest(BaseModel):
    param1: str
    param2: str = ""

# 3. Endpoints (après /agents/logs) :
@app.post("/agents/my-agent/method-one")
async def my_agent_method_one(req: MyAgentMethodOneRequest):
    agent = MyAgent()
    result = agent.method_one(req.param1, req.param2)
    return {"status": "ok", "result": result}
```

---

## Étape 6 — Mettre à jour le frontend (optionnel)

Si l'agent apparaît dans une Room du Hub frontend :

**`web/src/components/settings/model-settings-view.tsx`** — ajouter dans `AGENT_LABELS` :
```typescript
my_agent: "Elena Kovacs — Legal Analyst",
```

**Page Room concernée** (ex. `web/src/app/direction/page.tsx`) — ajouter la card agent.

---

## Checklist finale

- [ ] `agents/my_agent.py` créé avec SYSTEM_PROMPT structuré en 5 sections
- [ ] `@trace_agent()` sur chaque méthode publique
- [ ] `log_agent_action()` sur chaque méthode principale
- [ ] `record_task_learning()` dans try/except
- [ ] `config/agent_models.py` — tier ajouté
- [ ] `config/agent_personas.py` — persona + room + team mis à jour
- [ ] `api/main.py` — import + Pydantic models + endpoints ajoutés
- [ ] Test rapide : `curl -X POST http://localhost:8000/agents/my-agent/method-one -d '{"param1":"test"}' -H "Content-Type: application/json"`
