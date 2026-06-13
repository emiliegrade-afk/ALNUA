"""
services/parallel_runner.py — Exécution parallèle d'agents ALNUA.

Inspiré de oh-my-claude (ultrawork / max parallel execution) +
améliorations agent-orchestrator (retry + dependency mgmt) :
Lance plusieurs agents simultanément via asyncio.gather et retourne
les résultats agrégés. Compatible avec le système de scoring compétition.

Nouveautés v2 :
- Retry automatique jusqu'à 3 fois avec backoff exponentiel
- Support depends_on (tâche B attend tâche A)
- Progress tracking en temps réel via _TASK_PROGRESS
- run_with_dependencies() pour pipelines séquentiels/mixtes

Usage :
    from services.parallel_runner import run_agents_parallel, AgentTask

    results = await run_agents_parallel([
        AgentTask(agent_id="analyst_business", method="market_analysis",
                  kwargs={"product": "NomadApp", "market": "Vanlifers"}),
        AgentTask(agent_id="analyst_data", method="sql_query",
                  kwargs={"question": "Combien d'users actifs ?", "schema_context": "..."},
                  depends_on=["analyst_business.market_analysis"]),  # attend le résultat ci-dessus
        AgentTask(agent_id="content", method="write_content",
                  kwargs={"topic": "Lancement NomadApp", "format": "blog"},
                  max_retries=3),  # retry automatique
    ])

    # Synchrone (depuis code non-async) :
    from services.parallel_runner import run_agents_parallel_sync
    results = run_agents_parallel_sync([...])

    # Progress tracking :
    from services.parallel_runner import get_progress
    print(get_progress("my_run_id"))
"""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

# ---------------------------------------------------------------------------
# Progress Registry — accessible depuis les endpoints FastAPI
# ---------------------------------------------------------------------------

_TASK_PROGRESS: dict[str, dict[str, Any]] = {}


def get_progress(run_id: str) -> dict[str, Any]:
    """Retourne l'état de progression d'un run parallèle."""
    return _TASK_PROGRESS.get(run_id, {"error": "run_id not found"})


def list_runs(limit: int = 20) -> list[dict[str, Any]]:
    """Liste les derniers runs (les plus récents en premier)."""
    runs = sorted(
        _TASK_PROGRESS.values(),
        key=lambda r: r.get("started_at", 0),
        reverse=True,
    )
    return runs[:limit]

# ---------------------------------------------------------------------------
# Registry des agents et leurs méthodes
# ---------------------------------------------------------------------------

def _get_agent_method(agent_id: str, method_name: str) -> Callable:
    """Résout dynamiquement la méthode d'un agent par son ID."""
    AGENT_CLASSES = {
        "coo": ("agents.coo_agent", "COOAgent"),
        "spec": ("agents.spec_agent", "SpecAgent"),
        "qa": ("agents.qa_agent", "QAAgent"),
        "pm": ("agents.pm_agent", "PMAgent"),
        "dev_app": ("agents.dev_app_agent", "DevAppAgent"),
        "dev_backend": ("agents.dev_backend_agent", "DevBackendAgent"),
        "game_director": ("agents.game_director_agent", "GameDirectorAgent"),
        "dev_gaming": ("agents.dev_gaming_agent", "DevGamingAgent"),
        "brainstorm": ("agents.brainstorm_agent", "BrainstormAgent"),
        "rnd_agent": ("agents.rnd_agent", "RndAgent"),
        "marketing": ("agents.marketing_agent", "MarketingAgent"),
        "content": ("agents.content_agent", "ContentAgent"),
        "accounting": ("agents.accounting_agent", "AccountingAgent"),
        "hardware": ("agents.hardware_agent", "HardwareAgent"),
        "embedded_dev": ("agents.embedded_dev_agent", "EmbeddedDevAgent"),
        "secretary": ("agents.secretary_agent", "SecretaryAgent"),
        "dev_backend": ("agents.dev_backend_agent", "DevBackendAgent"),
        "level_designer": ("agents.level_designer_agent", "LevelDesignerAgent"),
        "controller": ("agents.controller_agent", "ControllerAgent"),
        "analyst_business": ("agents.analyst_business_agent", "BusinessAnalystAgent"),
        "analyst_data": ("agents.analyst_data_agent", "DataAnalystAgent"),
    }
    if agent_id not in AGENT_CLASSES:
        raise ValueError(f"Agent inconnu: {agent_id!r}. Agents disponibles: {list(AGENT_CLASSES)}")

    module_path, class_name = AGENT_CLASSES[agent_id]
    import importlib
    module = importlib.import_module(module_path)
    agent_class = getattr(module, class_name)
    instance = agent_class()
    method = getattr(instance, method_name, None)
    if method is None:
        raise AttributeError(f"L'agent {agent_id!r} n'a pas de méthode {method_name!r}")
    return method


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class AgentTask:
    """Définition d'une tâche agent pour l'exécution parallèle."""
    agent_id: str
    method: str
    kwargs: dict[str, Any] = field(default_factory=dict)
    task_label: str = ""            # Nom optionnel pour les logs (et clé depends_on)
    award_points: bool = True       # Attribuer des points compétition si succès
    max_retries: int = 2            # Nombre de retries automatiques (défaut 2, max 3)
    depends_on: list[str] = field(default_factory=list)  # labels des tâches bloquantes

    @property
    def label(self) -> str:
        return self.task_label or f"{self.agent_id}.{self.method}"


@dataclass
class AgentResult:
    """Résultat d'une tâche agent exécutée en parallèle."""
    agent_id: str
    method: str
    task_label: str
    success: bool
    result: Any = None
    error: str | None = None
    duration_ms: int = 0
    points_awarded: int = 0
    retries: int = 0


# ---------------------------------------------------------------------------
# Exécution
# ---------------------------------------------------------------------------

async def _run_single_task(
    task: AgentTask,
    run_id: str = "",
    progress: dict[str, Any] | None = None,
) -> AgentResult:
    """Exécute une seule tâche agent avec retry automatique (backoff exponentiel)."""
    start = time.monotonic()
    label = task.label
    max_retries = min(task.max_retries, 3)  # cap à 3
    retries = 0
    last_error = ""

    if progress is not None:
        progress[label] = {"status": "running", "retries": 0, "started_at": time.time()}

    while True:
        try:
            method = _get_agent_method(task.agent_id, task.method)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: method(**task.kwargs))
            duration_ms = int((time.monotonic() - start) * 1000)

            points = 0
            if task.award_points:
                try:
                    from services.competition import add_points
                    pts_result = add_points(task.agent_id, "task_completed", note=label[:80])
                    points = pts_result.get("points_added", 0)
                except Exception:
                    pass

            if progress is not None:
                progress[label] = {
                    "status": "done", "retries": retries,
                    "duration_ms": duration_ms,
                }

            return AgentResult(
                agent_id=task.agent_id, method=task.method,
                task_label=label, success=True, result=result,
                duration_ms=duration_ms, points_awarded=points, retries=retries,
            )

        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            retries += 1

            if retries > max_retries:
                break

            # Backoff exponentiel : 2s, 4s, 8s
            backoff = 2 ** retries
            if progress is not None:
                progress[label] = {
                    "status": f"retry_{retries}", "retries": retries,
                    "error": last_error, "backoff_s": backoff,
                }
            await asyncio.sleep(backoff)

    duration_ms = int((time.monotonic() - start) * 1000)
    if progress is not None:
        progress[label] = {
            "status": "failed", "retries": retries - 1,
            "error": last_error, "duration_ms": duration_ms,
        }
    return AgentResult(
        agent_id=task.agent_id, method=task.method,
        task_label=label, success=False, error=last_error,
        duration_ms=duration_ms, retries=retries - 1,
    )


async def run_agents_parallel(
    tasks: list[AgentTask],
    max_concurrent: int = 5,
    fail_fast: bool = False,
    run_id: str | None = None,
) -> dict[str, Any]:
    """
    Exécute plusieurs tâches agents simultanément.

    Args:
        tasks:          Liste de AgentTask à exécuter
        max_concurrent: Nombre max d'agents en parallèle (défaut: 5)
        fail_fast:      Arrêter dès le premier échec (défaut: False)

    Returns:
        {
            "results": [AgentResult, ...],
            "success_count": int,
            "failure_count": int,
            "total_duration_ms": int,
            "fastest_ms": int,
            "slowest_ms": int,
            "total_points_awarded": int,
        }
    """
    run_id = run_id or str(uuid.uuid4())[:8]
    semaphore = asyncio.Semaphore(max_concurrent)
    start_total = time.monotonic()

    # Progress tracking
    progress: dict[str, Any] = {}
    _TASK_PROGRESS[run_id] = {
        "run_id": run_id, "total": len(tasks),
        "started_at": time.time(), "tasks": progress,
    }

    async def run_with_semaphore(task: AgentTask) -> AgentResult:
        async with semaphore:
            return await _run_single_task(task, run_id=run_id, progress=progress)

    if fail_fast:
        results = []
        for task in tasks:
            r = await run_with_semaphore(task)
            results.append(r)
            if not r.success:
                break
    else:
        results = await asyncio.gather(*[run_with_semaphore(t) for t in tasks])

    total_ms = int((time.monotonic() - start_total) * 1000)
    successes = [r for r in results if r.success]
    failures = [r for r in results if not r.success]
    durations = [r.duration_ms for r in results]

    _TASK_PROGRESS[run_id]["completed_at"] = time.time()
    _TASK_PROGRESS[run_id]["total_duration_ms"] = total_ms

    return {
        "run_id": run_id,
        "results": [
            {
                "agent_id": r.agent_id,
                "method": r.method,
                "label": r.task_label,
                "success": r.success,
                "result": r.result,
                "error": r.error,
                "duration_ms": r.duration_ms,
                "points_awarded": r.points_awarded,
                "retries": r.retries,
            }
            for r in results
        ],
        "success_count": len(successes),
        "failure_count": len(failures),
        "total_duration_ms": total_ms,
        "fastest_ms": min(durations) if durations else 0,
        "slowest_ms": max(durations) if durations else 0,
        "total_points_awarded": sum(r.points_awarded for r in results),
        "failed_tasks": [
            {"agent_id": r.agent_id, "method": r.method, "error": r.error}
            for r in failures
        ],
    }


def run_agents_parallel_sync(
    tasks: list[AgentTask],
    max_concurrent: int = 5,
    fail_fast: bool = False,
    run_id: str | None = None,
) -> dict[str, Any]:
    """
    Version synchrone de run_agents_parallel.
    Utilisable depuis du code non-async (endpoints FastAPI sync, scripts, etc.).
    """
    coro = run_agents_parallel(tasks, max_concurrent, fail_fast, run_id)
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


def run_with_dependencies(
    tasks: list[AgentTask],
    max_concurrent: int = 3,
) -> dict[str, Any]:
    """
    Exécute des tâches en respectant les dépendances (depends_on).
    Les tâches sans dépendances tournent en parallèle.
    Passe les résultats des tâches précédentes via kwargs["_deps"] si souhaité.

    Endpoint: POST /services/parallel/run-with-deps
    """
    completed: dict[str, AgentResult] = {}
    pending = list(tasks)
    all_results: list[dict] = []
    start = time.monotonic()
    run_id = str(uuid.uuid4())[:8]

    _TASK_PROGRESS[run_id] = {
        "run_id": run_id, "total": len(tasks),
        "mode": "with_dependencies", "started_at": time.time(), "tasks": {},
    }

    while pending:
        ready = [t for t in pending if all(dep in completed for dep in t.depends_on)]
        if not ready:
            # Blocage : dépendances impossibles
            for t in pending:
                all_results.append({
                    "label": t.label, "success": False,
                    "error": "Blocked by dependency failure or cycle",
                    "agent_id": t.agent_id, "retries": 0,
                })
            break

        batch = ready[:max_concurrent]
        for t in batch:
            pending.remove(t)

        batch_result = run_agents_parallel_sync(batch, max_concurrent, run_id=run_id)
        for r in batch_result.get("results", []):
            completed[r["label"]] = r
            all_results.append(r)

    total_ms = int((time.monotonic() - start) * 1000)
    _TASK_PROGRESS[run_id]["completed_at"] = time.time()

    success_count = sum(1 for r in all_results if r.get("success"))
    return {
        "run_id": run_id,
        "results": all_results,
        "success_count": success_count,
        "failure_count": len(all_results) - success_count,
        "total_duration_ms": total_ms,
    }


# ---------------------------------------------------------------------------
# Helpers pré-configurés pour cas d'usage courants ALNUA
# ---------------------------------------------------------------------------

def run_analytics_room(
    product: str,
    business_question: str,
    sql_question: str,
    schema_context: str,
) -> dict[str, Any]:
    """
    Lance Layla (Business Analyst) et Axel (Data Analyst) en parallèle.
    Pattern le plus courant pour l'analytics_room.
    """
    tasks = [
        AgentTask(
            agent_id="analyst_business",
            method="strategic_brief",
            kwargs={
                "topic": product,
                "context": business_question,
                "decision_needed": "Quelle action prendre ?",
            },
            task_label="Layla — brief stratégique",
        ),
        AgentTask(
            agent_id="analyst_data",
            method="sql_query",
            kwargs={
                "question": sql_question,
                "schema_context": schema_context,
            },
            task_label="Axel — requête SQL",
        ),
    ]
    return run_agents_parallel_sync(tasks)


def run_content_sprint(
    topic: str,
    product: str,
    target: str,
) -> dict[str, Any]:
    """
    Lance Camille (Marketing) et Sofia (Content) en parallèle sur le même sujet.
    """
    tasks = [
        AgentTask(
            agent_id="marketing",
            method="handle_instruction",
            kwargs={"instruction": f"Stratégie de lancement pour {product} sur le sujet : {topic}. Cible : {target}"},
            task_label="Camille — stratégie marketing",
        ),
        AgentTask(
            agent_id="content",
            method="handle_instruction",
            kwargs={"instruction": f"Rédige du contenu blog pour {product} sur : {topic}. Ton : engageant, cible : {target}"},
            task_label="Sofia — contenu blog",
        ),
    ]
    return run_agents_parallel_sync(tasks)
