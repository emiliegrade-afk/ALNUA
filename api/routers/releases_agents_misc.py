"""PM, QA, content, spec, and agent log routes."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter()

_SECTOR_AGENT_CLASSES: dict[str, tuple[str, str]] = {
    "app": ("agents.content_app_agent", "ContentAppAgent"),
    "gaming": ("agents.content_gaming_agent", "ContentGamingAgent"),
    "robo": ("agents.content_robo_agent", "ContentRoboAgent"),
    "company": ("agents.content_company_agent", "ContentCompanyAgent"),
}


def _resolve_content_agent(sector: str | None) -> ContentAgent:
    if not sector:
        return ContentAgent()
    import importlib

    module_path, class_name = _SECTOR_AGENT_CLASSES[sector]
    module = importlib.import_module(module_path)
    agent_class = getattr(module, class_name)
    return agent_class()


@router.post("/agents/pm/triage/{project_id}")
def pm_triage(project_id: str) -> dict[str, Any]:
    agent = PMAgent()
    return agent.triage_project(project_id)


@router.post("/agents/qa/analyze/{project_id}")
def qa_analyze(project_id: str) -> dict[str, Any]:
    agent = QAAgent()
    return agent.analyze_feedback_batch(project_id)


@router.post("/agents/content/generate")
def content_generate(body: ContentGenerateRequest) -> dict[str, Any]:
    agent = _resolve_content_agent(body.sector)
    try:
        posts = agent.generate_posts(
            body.project_id,
            body.dev_log,
            body.content_types,
            body.platforms,
            alnua_global=body.alnua_global,
        )
        return {"posts_created": len(posts), "posts": posts}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("content_generate failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/agents/content/generate/{project_id}")
def content_generate_legacy(project_id: str) -> dict[str, Any]:
    agent = ContentAgent()
    posts = agent.generate_from_dev_logs(project_id)
    return {"posts_created": len(posts), "posts": posts}


@router.post("/agents/spec/{ticket_id}")
def spec_generate(ticket_id: str) -> dict[str, Any]:
    agent = SpecAgent()
    return agent.generate_cursor_prompt(ticket_id)


@router.get("/agents/logs")
def agent_logs(limit: int = Query(default=50, le=200)) -> list[dict[str, Any]]:
    db = get_supabase()
    return db.select("agent_logs", order_by="created_at", ascending=False, limit=limit)
