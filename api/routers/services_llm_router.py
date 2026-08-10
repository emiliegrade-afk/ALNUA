"""Advanced services — LLM Router + Adversarial Spec (peeled from advanced_services.py)."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter(prefix="/services", tags=["advanced-services"])


class LLMRouterRequest(BaseModel):
    agent_id: str
    prompt: str
    method_name: str = ""
    force_tier: str | None = None


class LLMRouterReportRequest(BaseModel):
    agent_id: str
    prompt: str
    method_name: str = ""


@router.post("/llm-router/route")
def llm_router_route(body: LLMRouterRequest) -> dict[str, Any]:
    """Retourne le model slug optimal pour un appel donné."""
    from services.llm_router import route_to_model
    model = route_to_model(body.agent_id, body.prompt, body.method_name, body.force_tier)
    return {"agent_id": body.agent_id, "routed_model": model}


@router.post("/llm-router/report")
def llm_router_report(body: LLMRouterReportRequest) -> dict[str, Any]:
    """Rapport complet de décision de routage (debug / audit Rémi)."""
    from services.llm_router import routing_report
    return routing_report(body.agent_id, body.prompt, body.method_name)


@router.post("/llm-router/complexity")
def llm_router_complexity(body: LLMRouterReportRequest) -> dict[str, Any]:
    """Score de complexité seul (0-10)."""
    from services.llm_router import complexity_score
    score = complexity_score(body.prompt, body.method_name)
    return {
        "prompt_chars": len(body.prompt),
        "method": body.method_name,
        "complexity_score": score,
        "tier_suggestion": "premium" if score >= 7 else "standard" if score >= 4 else "fast",
    }


class AdversarialSpecRequest(BaseModel):
    spec_text: str
    context: str = ""
    rounds: int = Field(default=2, ge=1, le=3)
    stop_on_approve: bool = True


class QuickCheckRequest(BaseModel):
    spec_text: str
    context: str = ""


@router.post("/adversarial-spec/debate")
def adversarial_spec_debate(body: AdversarialSpecRequest) -> dict[str, Any]:
    """
    Fait débattre Léon (Spec) et Alex (QA) sur une spec jusqu'à consensus.
    Retourne la spec convergée + divergences + historique des rounds.
    """
    from services.adversarial_spec import debate_spec
    return debate_spec(body.spec_text, body.context, body.rounds, body.stop_on_approve)


@router.post("/adversarial-spec/quick-check")
def adversarial_spec_quick_check(body: QuickCheckRequest) -> dict[str, Any]:
    """Pre-check QA rapide sans itération. Identifie les problèmes critiques."""
    from services.adversarial_spec import quick_adversarial_check
    return quick_adversarial_check(body.spec_text, body.context)
