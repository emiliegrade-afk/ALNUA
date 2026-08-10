"""Advanced services — Content Pipeline + Trend Monitor (peeled from advanced_services.py)."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter(prefix="/services", tags=["advanced-services"])


class ContentPipelineRequest(BaseModel):
    topic: str
    product: str
    target_audience: str
    tone: str = "professionnel, direct"
    key_messages: list[str] = Field(default_factory=list)
    call_to_action: str = ""
    context: str = ""
    platforms: list[str] = Field(
        default_factory=lambda: ["twitter", "linkedin", "blog", "discord"]
    )


@router.post("/content-pipeline/run")
def content_pipeline_run(body: ContentPipelineRequest) -> dict[str, Any]:
    """
    Brief → contenus multi-plateformes en parallèle.
    Camille (Marketing) génère la stratégie, Sofia (Content) les textes.
    """
    from services.content_pipeline import run_pipeline, ContentBrief
    brief = ContentBrief(
        topic=body.topic,
        product=body.product,
        target_audience=body.target_audience,
        tone=body.tone,
        key_messages=body.key_messages,
        call_to_action=body.call_to_action,
        context=body.context,
    )
    return run_pipeline(brief, body.platforms)


@router.get("/content-pipeline/platforms")
def content_pipeline_platforms() -> list[dict[str, str]]:
    """Liste les plateformes supportées par le pipeline."""
    from services.content_pipeline import available_platforms
    return available_platforms()


class TrendBriefRequest(BaseModel):
    topics: list[str]
    sources: list[str] = ["hackernews", "reddit", "github"]
    agent_id: str = "marketing"
    limit: int = 20


@router.get("/trends/today")
def trends_today(
    sources: str = "hackernews,reddit,github",
    topics: str = "",
    limit: int = 30,
) -> dict[str, Any]:
    """
    Tendances brutes du jour depuis HackerNews, Reddit, GitHub.
    GET /services/trends/today?sources=hackernews,reddit&topics=ai,python
    """
    from services.trend_monitor import get_raw_trends
    sources_list = [s.strip() for s in sources.split(",") if s.strip()]
    topics_list = [t.strip() for t in topics.split(",") if t.strip()]
    return get_raw_trends(sources_list, topics_list, limit)


@router.post("/trends/brief")
def trends_brief(body: TrendBriefRequest) -> dict[str, Any]:
    """
    Brief tendances synthétisé par Camille (Marketing) via LLM.
    Agrège HN, Reddit, GitHub → brief structuré avec recommandations.
    """
    from services.trend_monitor import get_trend_brief
    return get_trend_brief(
        topics=body.topics,
        sources=body.sources,
        limit=body.limit,
        agent_id=body.agent_id,
    )
