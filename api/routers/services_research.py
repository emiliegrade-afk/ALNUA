"""Advanced services — Deep Research + Plan Executor (peeled from advanced_services.py)."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter(prefix="/services", tags=["advanced-services"])


class DeepResearchRequest(BaseModel):
    query: str
    context: str = ""
    rounds: int = Field(default=3, ge=1, le=3)
    agent_id: str = "brainstorm"


class QuickResearchRequest(BaseModel):
    query: str
    context: str = ""
    agent_id: str = "brainstorm"


@router.post("/deep-research/run")
def deep_research_run(body: DeepResearchRequest) -> dict[str, Any]:
    """
    Recherche multi-rounds : explore → approfondit → vérifie → synthétise.
    Idris (brainstorm), Alex (rnd_agent) ou Layla (analyst_business) selon agent_id.
    """
    from services.deep_research import run_deep_research
    return run_deep_research(
        query=body.query,
        context=body.context,
        rounds=body.rounds,
        agent_id=body.agent_id,
    )


@router.post("/deep-research/quick")
def deep_research_quick(body: QuickResearchRequest) -> dict[str, Any]:
    """Recherche rapide 1 round — pour réponses immédiates sans itération."""
    from services.deep_research import quick_research
    return quick_research(
        query=body.query,
        context=body.context,
        agent_id=body.agent_id,
    )


class PlanStepBody(BaseModel):
    step_id: str
    description: str
    agent_id: str
    method: str
    kwargs: dict[str, Any] = Field(default_factory=dict)
    depends_on: list[str] = Field(default_factory=list)


class PlanExecuteRequest(BaseModel):
    title: str
    steps: list[PlanStepBody]
    context: str = ""
    max_concurrent: int = Field(default=4, ge=1, le=5)
    stop_on_failure: bool = False


class CooRunRequest(BaseModel):
    objective: str
    context: str = ""
    max_concurrent: int = Field(default=4, ge=1, le=5)
    stop_on_failure: bool = False


@router.post("/plan/execute")
def plan_execute(body: PlanExecuteRequest) -> dict[str, Any]:
    """
    Exécute un plan structuré pré-construit.
    Steps indépendants tournent en parallèle, dépendances respectées.
    """
    from services.plan_executor import execute_plan, ExecutionPlan, ExecutionStep
    steps = [
        ExecutionStep(
            step_id=s.step_id,
            description=s.description,
            agent_id=s.agent_id,
            method=s.method,
            kwargs=s.kwargs,
            depends_on=s.depends_on,
        )
        for s in body.steps
    ]
    plan = ExecutionPlan(title=body.title, steps=steps, context=body.context)
    return execute_plan(plan, body.max_concurrent, body.stop_on_failure)


@router.post("/plan/coo-run")
def plan_coo_run(body: CooRunRequest) -> dict[str, Any]:
    """
    Pipeline complet : Aria (COO) génère le plan depuis l'objectif → executor le déroule.
    Les agents appropriés sont sélectionnés et exécutés automatiquement.
    """
    from services.plan_executor import run_coo_plan
    return run_coo_plan(
        objective=body.objective,
        context=body.context,
        max_concurrent=body.max_concurrent,
        stop_on_failure=body.stop_on_failure,
    )
