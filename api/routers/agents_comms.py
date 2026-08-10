"""Marketing and ads agent routes."""

from __future__ import annotations

from api.route_common import *  # noqa: F403
from api.routers.agents_pole_helpers import clean_agent_text

router = APIRouter()


@router.post("/agents/marketing/instruction")
def marketing_instruction(body: AgentInstructionRequest) -> dict[str, str]:
    result = MarketingAgent().handle_instruction(clean_agent_text(body.instruction))
    return {"result": result}


@router.post("/agents/marketing/seo-audit")
def marketing_seo_audit(body: MarketingSeoRequest) -> dict[str, str]:
    from skills.skill_seo_audit import run_seo_audit

    return {"result": run_seo_audit(body.url)}


@router.post("/agents/marketing/content")
def marketing_create_content(body: MarketingContentRequest) -> dict[str, str]:
    instruction = (
        f"Génère du contenu {body.type} pour {body.project} sur le sujet : "
        f"{clean_agent_text(body.topic, max_length=500)}. "
        f"Ton : {body.tone}. Longueur : {body.length}."
    )
    result = MarketingAgent().handle_instruction(instruction)
    return {"result": result}


@router.post("/agents/ads/create-campaign")
def ads_create_campaign(body: AdsCreateCampaignRequest) -> dict[str, Any]:
    return AdsAgent().create_campaign(
        clean_agent_text(body.brief, max_length=2000),
        platform=body.platform,
        budget_usd=body.budget_usd,
        objective=body.objective,
        audience=body.audience,
        project_id=body.project_id,
        name=body.name,
    )
