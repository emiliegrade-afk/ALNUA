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


@router.post("/agents/dev-frontend/implement-ui")
def dev_frontend_implement_ui(body: DevFrontendImplementRequest) -> dict[str, str]:
    result = DevFrontendAgent().implement_ui(
        clean_agent_text(body.feature),
        body.project,
        clean_agent_text(body.context),
        clean_agent_text(body.design_notes),
    )
    return {"result": result}


@router.post("/agents/dev-frontend/fix-layout")
def dev_frontend_fix_layout(body: DevFrontendFixLayoutRequest) -> dict[str, Any]:
    return DevFrontendAgent().fix_layout(
        clean_agent_text(body.issue),
        clean_agent_text(body.context),
        clean_agent_text(body.code_snippet, max_length=12000),
    )


@router.post("/agents/dev-frontend/review")
def dev_frontend_review(body: DevFrontendReviewRequest) -> dict[str, Any]:
    return DevFrontendAgent().review_component(
        clean_agent_text(body.code, max_length=12000),
        clean_agent_text(body.context),
    )


@router.post("/agents/dev-frontend/instruction")
def dev_frontend_instruction(body: AgentInstructionRequest) -> dict[str, str]:
    result = DevFrontendAgent().handle_instruction(clean_agent_text(body.instruction))
    return {"result": result}


@router.post("/agents/dev-integrator/integrate")
def dev_integrator_integrate(body: DevIntegratorIntegrateRequest) -> dict[str, Any]:
    return DevIntegratorAgent().integrate_worktrees(
        body.repo_path,
        body.branch,
        body.worktrees,
        body.base_branch,
    )


@router.post("/agents/dev-integrator/open-pr")
def dev_integrator_open_pr(body: DevIntegratorOpenPrRequest) -> dict[str, Any]:
    return DevIntegratorAgent().open_integration_pr(
        body.repo_path,
        body.branch,
        clean_agent_text(body.title, max_length=200),
        clean_agent_text(body.body, max_length=4000),
        body.qa_verdict,
    )


@router.post("/agents/dev-integrator/review-diff")
def dev_integrator_review_diff(body: DevIntegratorReviewDiffRequest) -> dict[str, Any]:
    return DevIntegratorAgent().review_diff(
        clean_agent_text(body.diff_summary, max_length=12000),
        clean_agent_text(body.context),
    )
