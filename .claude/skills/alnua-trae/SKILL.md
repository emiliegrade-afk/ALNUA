# /alnua-trae — Skills techniques ALNUA (Best of TRAE-Skills)
> Adapté de TRAE-Skills (HighMark-31, 150+ skills) — sélection des patterns les plus pertinents pour la stack ALNUA.
> Invoque avec `/alnua-trae` pour charger les meilleures pratiques techniques de la stack.

## Stack couverte
FastAPI · Python 3.12+ · Next.js 14+ (App Router) · TypeScript · Supabase · OpenRouter · Pydantic v2 · asyncio

---

## 🐍 Python / FastAPI — Patterns ALNUA

### Pattern 1 — Endpoint FastAPI standard ALNUA
```python
from api.route_common import *  # toujours en premier

router = APIRouter()

@router.post("/agents/my-agent/action")
def my_action(body: MyRequest) -> dict[str, Any]:
    # 1. Instancier l'agent (db injecté automatiquement)
    agent = MyAgent()
    # 2. Appeler la méthode
    result = agent.my_method(body.param1, body.param2)
    # 3. Logger (via log_agent_action dans l'agent, pas ici)
    return result
```

### Pattern 2 — Méthode agent avec tous les décorateurs obligatoires
```python
@trace_agent("my_agent")  # Langfuse tracing
def my_method(self, param: str, context: str = "") -> dict[str, Any]:
    # Inject learning context from Mem0
    prompt = inject_learning_context(
        f"Ta tâche : {param}\nContexte : {context}",
        self.AGENT_NAME,
        param
    )
    # LLM call via OpenRouter
    raw = self.llm.complete(
        self.SYSTEM_PROMPT, prompt,
        agent_id=self.AGENT_NAME,
        temperature=0.4
    )
    # Parse JSON (gère les markdown fences automatiquement)
    result = parse_json_response(raw)
    # Log obligatoire
    log_agent_action(
        self.db, self.AGENT_NAME, "my_method",
        input_summary=param[:100],
        output_summary=str(result)[:100]
    )
    # Learning — dégradé silencieux
    try:
        record_task_learning(self.AGENT_NAME, "my_method", str(result)[:300], success=True)
    except Exception:
        pass
    return result
```

### Pattern 3 — Pydantic v2 models (api/schemas.py)
```python
class MyRequest(BaseModel):
    required_field: str
    optional_field: str = "default"
    numeric_field: int = Field(ge=0, le=100, description="0-100")
    list_field: list[str] = Field(default_factory=list)

class MyResponse(BaseModel):
    status: str
    data: dict[str, Any]
    agent: str = "my_agent"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

### Pattern 4 — Appel LLM avec routing dynamique
```python
from services.llm_router import route_to_model

# Laisser le router choisir le modèle optimal
model = route_to_model(
    agent_id=self.AGENT_NAME,
    prompt=prompt,
    method_name="my_method"  # influe sur le tier
)
raw = self.llm.complete(
    self.SYSTEM_PROMPT, prompt,
    agent_id=self.AGENT_NAME,
    model_override=model  # override optionnel
)
```

### Pattern 5 — Parallel runner (plusieurs agents simultanément)
```python
from services.parallel_runner import run_agents_parallel_sync, AgentTask

tasks = [
    AgentTask(
        agent_id="analyst_business",
        method="market_analysis",
        kwargs={"product": "ALNUA Hub", "market": "AI tools", "competitors": []},
        task_label="Analyse marché",
        award_points=True
    ),
    AgentTask(
        agent_id="analyst_data",
        method="dashboard_spec",
        kwargs={"dashboard_name": "KPIs Q2", "audience": "COO", "kpis": [], "data_sources": []},
        task_label="Dashboard spec",
        award_points=True
    ),
]
results = run_agents_parallel_sync(tasks, max_concurrent=5)
```

---

## ⚛️ Next.js / TypeScript — Patterns ALNUA

### Pattern 6 — Appel API Hub depuis un composant
```typescript
// hooks/useAgent.ts
export function useAgent<T>(endpoint: string) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const call = async (body: Record<string, unknown>) => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_HUB_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!res.ok) throw new Error(`Hub error: ${res.status}`)
      setData(await res.json())
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erreur inconnue')
    } finally {
      setLoading(false)
    }
  }
  return { data, loading, error, call }
}
```

### Pattern 7 — Composant agent standard
```typescript
// components/agents/MyAgentView.tsx
'use client'
import { useState } from 'react'
import { useAgent } from '@/hooks/useAgent'

interface MyAgentViewProps {
  agentId: string
}

export function MyAgentView({ agentId }: MyAgentViewProps) {
  const [input, setInput] = useState('')
  const { data, loading, error, call } = useAgent<{ result: string }>(`/agents/${agentId}/action`)

  return (
    <div className="flex flex-col gap-4 p-4">
      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Instruction..."
        className="w-full rounded-md border p-2 text-sm"
        disabled={loading}
      />
      <button
        onClick={() => call({ instruction: input })}
        disabled={loading || !input.trim()}
        className="rounded-md bg-primary px-4 py-2 text-sm font-medium disabled:opacity-50"
      >
        {loading ? 'En cours...' : 'Envoyer'}
      </button>
      {error && <p className="text-sm text-red-500">{error}</p>}
      {data && <pre className="rounded-md bg-muted p-3 text-xs">{JSON.stringify(data, null, 2)}</pre>}
    </div>
  )
}
```

### Pattern 8 — Server Component avec fetch Hub
```typescript
// app/analytics/page.tsx
import { Suspense } from 'react'

async function getLeaderboard() {
  const res = await fetch(`${process.env.HUB_URL}/agents/leaderboard`, {
    next: { revalidate: 60 }  // Cache 60s
  })
  if (!res.ok) return []
  return res.json()
}

export default async function AnalyticsPage() {
  const leaderboard = await getLeaderboard()
  return (
    <Suspense fallback={<LeaderboardSkeleton />}>
      <LeaderboardTable data={leaderboard} />
    </Suspense>
  )
}
```

---

## 🗄️ Supabase — Patterns ALNUA

### Pattern 9 — Requête Supabase standard
```python
from database.supabase_client import get_supabase

def get_agent_data(agent_id: str) -> list[dict]:
    db = get_supabase()
    result = db.table("agent_logs") \
        .select("*") \
        .eq("agent_id", agent_id) \
        .order("created_at", desc=True) \
        .limit(50) \
        .execute()
    return result.data or []
```

### Pattern 10 — Insert avec gestion d'erreur
```python
def save_agent_output(agent_id: str, output: dict) -> bool:
    try:
        db = get_supabase()
        db.table("agent_outputs").insert({
            "agent_id": agent_id,
            "output": output,
            "created_at": datetime.utcnow().isoformat()
        }).execute()
        return True
    except Exception as e:
        logger.warning(f"Supabase insert failed: {e}")
        return False
```

---

## ⚡ asyncio — Patterns ALNUA

### Pattern 11 — Tâche async avec timeout
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def run_agent_async(agent_method, *args, timeout=30):
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        try:
            return await asyncio.wait_for(
                loop.run_in_executor(executor, lambda: agent_method(*args)),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.warning(f"Agent timeout after {timeout}s")
            return {"error": "timeout", "partial": True}
```

---

## 🚀 Checklist qualité code ALNUA

```
[ ] `parse_json_response()` sur TOUT output LLM
[ ] `log_agent_action()` sur chaque méthode principale
[ ] `@trace_agent("nom_agent")` sur chaque méthode publique
[ ] `inject_learning_context()` dans chaque prompt
[ ] `try/except pass` sur record_task_learning (dégradé silencieux)
[ ] `from api.route_common import *` en tête de chaque router
[ ] Types Pydantic définis pour chaque Request/Response
[ ] Pas de `any` en TypeScript sans commentaire justifié
[ ] Pas d'UE5 (règle invariante ALNUA)
```

---

## Anti-patterns à éviter

```python
# ❌ JAMAIS ça
result = json.loads(llm_output)  # cas markdown fence → plante

# ✅ Toujours ça
result = parse_json_response(llm_output)  # gère ```json ... ```

# ❌ JAMAIS ça  
from agents.coo_agent import COOAgent
from agents.pm_agent import PMAgent
# ... 20 imports dans le router

# ✅ Toujours ça
from api.route_common import *  # 1 ligne, tout inclus

# ❌ JAMAIS ça (TypeScript)
const data: any = await res.json()

# ✅ Toujours ça
const data: AgentResponse = await res.json()
```
