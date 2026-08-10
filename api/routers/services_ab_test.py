"""Advanced services — A/B Tester (peeled from advanced_services.py)."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter(prefix="/services", tags=["advanced-services"])


class ABVariantBody(BaseModel):
    agent_id: str
    method: str
    kwargs: dict[str, Any] = Field(default_factory=dict)
    label: str = ""


class ABTestRequest(BaseModel):
    name: str
    variant_a: ABVariantBody
    variant_b: ABVariantBody
    judge_criteria: str = "Lequel est le plus utile, précis et bien structuré ?"
    runs_per_variant: int = Field(default=1, ge=1, le=3)
    judge_agent_id: str = "qa"


class QuickCompareRequest(BaseModel):
    agent_id: str
    method: str
    kwargs_a: dict[str, Any]
    kwargs_b: dict[str, Any]
    criteria: str = "Lequel est le meilleur résultat ?"


@router.post("/ab-test/run")
def ab_test_run(body: ABTestRequest) -> dict[str, Any]:
    """
    A/B test complet : exécute les deux variants en parallèle, LLM juge le gagnant.
    Alex (QA) est le juge par défaut.
    """
    from services.a_b_tester import run_ab_test, ABTestConfig
    config = ABTestConfig(
        name=body.name,
        variant_a=body.variant_a.model_dump(),
        variant_b=body.variant_b.model_dump(),
        judge_criteria=body.judge_criteria,
        runs_per_variant=body.runs_per_variant,
        judge_agent_id=body.judge_agent_id,
    )
    return run_ab_test(config)


@router.post("/ab-test/quick-compare")
def ab_test_quick_compare(body: QuickCompareRequest) -> dict[str, Any]:
    """Compare deux sets de kwargs sur le même agent — utile pour tester des paramètres."""
    from services.a_b_tester import quick_compare
    return quick_compare(
        agent_id=body.agent_id,
        method=body.method,
        kwargs_a=body.kwargs_a,
        kwargs_b=body.kwargs_b,
        criteria=body.criteria,
    )
