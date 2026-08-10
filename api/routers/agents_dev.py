"""Dev app / backend / gaming instruction routes."""

from __future__ import annotations

from api.route_common import *  # noqa: F403
from api.routers.agents_pole_helpers import clean_agent_text

router = APIRouter()


@router.post("/agents/dev-backend/design-api")
def dev_backend_design_api(body: DevBackendDesignAPIRequest) -> dict[str, Any]:
    return DevBackendAgent().design_api(
        clean_agent_text(body.feature), body.project, clean_agent_text(body.constraints)
    )


@router.post("/agents/dev-backend/implement")
def dev_backend_implement(body: DevBackendImplementRequest) -> dict[str, str]:
    result = DevBackendAgent().implement_feature(
        clean_agent_text(body.feature),
        body.project,
        clean_agent_text(body.api_spec, max_length=12000),
        body.tech_stack,
    )
    return {"result": result}


@router.post("/agents/dev-backend/review")
def dev_backend_review(body: DevBackendReviewRequest) -> dict[str, Any]:
    return DevBackendAgent().review_code(
        clean_agent_text(body.code, max_length=12000), clean_agent_text(body.context)
    )


@router.post("/agents/dev-backend/debug")
def dev_backend_debug(body: DevBackendDebugRequest) -> dict[str, Any]:
    return DevBackendAgent().debug(
        clean_agent_text(body.error),
        clean_agent_text(body.context),
        clean_agent_text(body.code_snippet, max_length=12000),
    )


@router.post("/agents/dev-app/instruction")
def dev_app_instruction(body: AgentInstructionRequest) -> dict[str, str]:
    result = DevAppAgent().handle_instruction(clean_agent_text(body.instruction))
    return {"result": result}


@router.get("/agents/dev-app/issues")
def dev_app_list_issues() -> dict[str, Any]:
    from skills.skill_gh_issues import list_ready_issues

    issues = list_ready_issues()
    return {"issues": issues}


@router.post("/agents/dev-gaming/instruction")
def dev_gaming_instruction(body: AgentInstructionRequest) -> dict[str, str]:
    result = DevGamingAgent().handle_instruction(clean_agent_text(body.instruction))
    return {"result": result}
