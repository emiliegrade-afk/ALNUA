"""Business and data analyst agent routes."""

from __future__ import annotations

from api.route_common import *  # noqa: F403
from api.routers.agents_pole_helpers import clean_agent_text

router = APIRouter()


@router.post("/agents/analyst-business/market")
def analyst_business_market(body: BusinessAnalystMarketRequest) -> dict[str, Any]:
    return BusinessAnalystAgent().market_analysis(body.product, body.market, body.competitors)


@router.post("/agents/analyst-business/kpis")
def analyst_business_kpis(body: BusinessAnalystKPIsRequest) -> dict[str, Any]:
    return BusinessAnalystAgent().define_kpis(
        body.project, body.stage, clean_agent_text(body.business_goal)
    )


@router.post("/agents/analyst-business/user-research")
def analyst_business_user_research(body: BusinessAnalystUserResearchRequest) -> dict[str, Any]:
    return BusinessAnalystAgent().user_research(
        body.product, clean_agent_text(body.research_question), body.user_segment
    )


@router.post("/agents/analyst-business/brief")
def analyst_business_brief(body: BusinessAnalystBriefRequest) -> dict[str, Any]:
    return BusinessAnalystAgent().strategic_brief(
        clean_agent_text(body.topic, max_length=500),
        clean_agent_text(body.context),
        clean_agent_text(body.decision_needed),
    )


@router.post("/agents/analyst-data/sql")
def analyst_data_sql(body: DataAnalystSQLRequest) -> dict[str, Any]:
    return DataAnalystAgent().sql_query(
        clean_agent_text(body.question),
        clean_agent_text(body.schema_context, max_length=8000),
        body.db_type,
    )


@router.post("/agents/analyst-data/funnel")
def analyst_data_funnel(body: DataAnalystFunnelRequest) -> dict[str, Any]:
    return DataAnalystAgent().funnel_analysis(body.funnel_name, body.steps, body.data)


@router.post("/agents/analyst-data/anomaly")
def analyst_data_anomaly(body: DataAnalystAnomalyRequest) -> dict[str, Any]:
    return DataAnalystAgent().anomaly_report(
        body.metric, body.recent_values, body.baseline, body.period
    )


@router.post("/agents/analyst-data/dashboard-spec")
def analyst_data_dashboard(body: DataAnalystDashboardRequest) -> dict[str, Any]:
    return DataAnalystAgent().dashboard_spec(
        body.dashboard_name, body.audience, body.kpis, body.data_sources
    )
