"""Advanced services — Parallel Runner (peeled from advanced_services.py)."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter(prefix="/services", tags=["advanced-services"])


class ParallelTask(BaseModel):
    agent_id: str
    method: str
    kwargs: dict[str, Any] = Field(default_factory=dict)
    task_label: str = ""
    award_points: bool = True


class ParallelRunRequest(BaseModel):
    tasks: list[ParallelTask]
    max_concurrent: int = Field(default=5, ge=1, le=10)
    fail_fast: bool = False


class AnalyticsRoomRequest(BaseModel):
    product: str
    business_question: str
    sql_question: str
    schema_context: str


class ContentSprintRequest(BaseModel):
    topic: str
    product: str
    target: str


@router.post("/parallel/run")
def parallel_run(body: ParallelRunRequest) -> dict[str, Any]:
    """Exécute plusieurs agents en parallèle simultanément."""
    from services.parallel_runner import run_agents_parallel_sync, AgentTask
    tasks = [
        AgentTask(
            agent_id=t.agent_id,
            method=t.method,
            kwargs=t.kwargs,
            task_label=t.task_label,
            award_points=t.award_points,
        )
        for t in body.tasks
    ]
    return run_agents_parallel_sync(tasks, body.max_concurrent, body.fail_fast)


@router.post("/parallel/analytics-room")
def parallel_analytics_room(body: AnalyticsRoomRequest) -> dict[str, Any]:
    """Lance Layla (Business) + Axel (Data) en parallèle sur la même question."""
    from services.parallel_runner import run_analytics_room
    return run_analytics_room(
        body.product, body.business_question, body.sql_question, body.schema_context
    )


@router.post("/parallel/content-sprint")
def parallel_content_sprint(body: ContentSprintRequest) -> dict[str, Any]:
    """Lance Camille (Marketing) + Sofia (Content) en parallèle sur le même sujet."""
    from services.parallel_runner import run_content_sprint
    return run_content_sprint(body.topic, body.product, body.target)


@router.post("/parallel/run-with-deps")
def parallel_run_with_deps(body: ParallelRunRequest) -> dict[str, Any]:
    """
    Exécute des tâches en respectant leurs dépendances (depends_on).
    Les tâches sans dépendances tournent en parallèle.
    """
    from services.parallel_runner import run_with_dependencies, AgentTask
    tasks = [
        AgentTask(
            agent_id=t.agent_id,
            method=t.method,
            kwargs=t.kwargs,
            task_label=t.task_label,
            award_points=t.award_points,
        )
        for t in body.tasks
    ]
    return run_with_dependencies(tasks, body.max_concurrent)


@router.get("/parallel/progress/{run_id}")
def parallel_progress(run_id: str) -> dict[str, Any]:
    """Suivi de progression en temps réel d'un run parallèle."""
    from services.parallel_runner import get_progress
    return get_progress(run_id)


@router.get("/parallel/runs")
def parallel_list_runs(limit: int = 20) -> list[dict[str, Any]]:
    """Liste les derniers runs parallèles."""
    from services.parallel_runner import list_runs
    return list_runs(limit)
