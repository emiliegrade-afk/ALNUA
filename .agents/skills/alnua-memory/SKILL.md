# /alnua-memory — Mémoire Mem0 + Compression ALNUA

Guide complet pour lire, écrire, interroger et compresser la mémoire des 20 agents via Mem0.

---

## Architecture mémoire ALNUA

Chaque agent a sa propre mémoire isolée dans Mem0, identifiée par son `agent_id` canonique.

```
Mem0 (cloud)
├── coo        → leçons de Aria (délégation, priorisation)
├── dev_backend → leçons de Hao (patterns FastAPI, bugs récurrents)
├── marketing  → leçons de Camille (canaux, formats, audiences)
├── content    → leçons de Sofia (tons, formats performants)
├── analyst_data → leçons d'Axel (requêtes SQL efficaces)
└── ... (20 agents total)
```

Règle : **pas de cross-contamination** — Hao n'apprend pas à écrire du marketing.

---

## Lire la mémoire d'un agent

```python
from skills.skill_mem0 import recall

# Récupère les leçons pertinentes pour une tâche
memories = recall(query="patterns FastAPI performance", agent_id="dev_backend")
print(memories)

# Inject automatiquement dans le prompt (pattern recommandé)
from skills.skill_agent_learning import inject_learning_context
prompt_enrichi = inject_learning_context(
    prompt="Optimise cet endpoint FastAPI...",
    agent_id="dev_backend",
    task="optimisation performance"
)
```

---

## Écrire dans la mémoire

```python
from skills.skill_mem0 import remember

# Manuellement (rare — préférer learn_from_outcome)
remember("Le pattern background task FastAPI évite les timeouts sur les endpoints lourds",
         agent_id="dev_backend")

# Automatiquement après chaque tâche (pattern recommandé)
from skills.skill_agent_learning import record_task_learning
record_task_learning(
    agent_id="dev_backend",
    task="Optimiser endpoint /reports",
    outcome="Latence réduite de 2.1s à 0.3s avec BackgroundTasks",
    success=True,
)
```

---

## Comprimer la mémoire (Codex-mem-inspired)

Quand un agent accumule trop de leçons, on les compresse en un digest synthétique.

```python
from skills.skill_agent_learning import auto_compress_if_needed, compress_agent_memory

# Auto-compression si > 20 entrées
compressed = auto_compress_if_needed("dev_backend", threshold=20)

# Compression forcée avec mémoires brutes
digest = compress_agent_memory(
    agent_id="dev_backend",
    raw_memories=["leçon 1...", "leçon 2...", ...],
    blocking=True,
)
print(digest)
# → "→ Toujours utiliser BackgroundTasks pour les opérations > 500ms
#    → Valider avec Pydantic avant d'insérer en base
#    → Les endpoints de reporting doivent avoir un cache Redis"
```

**Via API :**
```
POST /services/memory/compress
{"agent_id": "dev_backend", "threshold": 20}
```

---

## IDs canoniques des agents

| Agent | ID mémoire |
|-------|-----------|
| Aria (COO) | `coo` |
| Léon (Spec) | `spec` |
| Alex (QA) | `qa` |
| Sam (PM) | `pm` |
| Théo (Dev App) | `dev_app` |
| Hao (Dev Backend) | `dev_backend` |
| Nova (Dev Gaming) | `dev_gaming` |
| Mira (Game Director) | `game_director` |
| Idris (Brainstorm) | `brainstorm` |
| Alex (R&D) | `rnd_agent` |
| Camille (Marketing) | `marketing` |
| Sofia (Content) | `content` |
| Jules (Accounting) | `accounting` |
| Rémi (Controller) | `controller` |
| Yuki (Hardware) | `hardware` |
| Zara (Embedded) | `embedded_dev` |
| Nadia (Secretary) | `secretary` |
| Finn (Level Designer) | `level_designer` |
| Layla (Analyst Business) | `analyst_business` |
| Axel (Analyst Data) | `analyst_data` |

---

## Endpoints mémoire

```
POST /services/memory/compress     → compression d'un agent
GET  /services/memory/compress     → (via POST body: agent_id, threshold)
```

---

## Patterns anti-mémoire

- ❌ `remember("faire attention")` — trop vague, inutile
- ✅ `remember("Quand l'API retourne 429, attendre 60s avant retry — OpenRouter throttle agressivement")` — actionnable
- ❌ Écrire la même leçon deux fois → compression s'en chargera
- ✅ `record_task_learning()` après chaque méthode principale — c'est automatique
