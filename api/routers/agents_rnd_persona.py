"""Alex Mercer (rnd_agent) — dedicated HTTP surface."""

from __future__ import annotations

from api.route_common import *  # noqa: F403
from api.routers.agents_pole_helpers import clean_agent_text

router = APIRouter()


@router.post("/agents/rnd-agent/research")
def rnd_agent_research(body: RndAgentResearchRequest) -> dict[str, Any]:
    return RndAgent().research_topic(
        clean_agent_text(body.query),
        clean_agent_text(body.context),
    )


@router.post("/agents/rnd-agent/prototype")
def rnd_agent_prototype(body: RndAgentPrototypeRequest) -> dict[str, Any]:
    return RndAgent().prototype_spec(
        clean_agent_text(body.idea),
        clean_agent_text(body.context),
    )


@router.post("/agents/rnd-agent/instruction")
def rnd_agent_instruction(body: AgentInstructionRequest) -> dict[str, Any]:
    """Default: research_topic on the instruction text."""
    return RndAgent().research_topic(clean_agent_text(body.instruction))
