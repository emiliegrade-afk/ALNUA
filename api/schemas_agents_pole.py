"""Pydantic models — split from schemas.py (debt paydown)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

class MarketingSeoRequest(BaseModel):
    url: str


class MarketingContentRequest(BaseModel):
    type: str = "discord"
    project: str = "wyrdheim"
    topic: str
    tone: str = "épique"
    length: str = "medium"


class AdsCreateCampaignRequest(BaseModel):
    brief: str
    project_id: str | None = None
    name: str | None = None
    platform: str = Field(default="meta", pattern="^(meta|google|tiktok)$")
    budget_usd: float = Field(default=50.0, gt=0)
    objective: str = Field(
        default="awareness",
        pattern="^(awareness|traffic|conversions|engagement|video_views)$",
    )
    audience: str = "lookalike"


class EmbeddedPiCommandRequest(BaseModel):
    command: str


class BomCreateRequest(BaseModel):
    component: str
    category: str = "autre"
    quantity: int = 1
    unit_price: float | None = None
    supplier: str | None = None
    url: str | None = None
    status: str = "a_commander"
    notes: str | None = None
    project_slug: str = "eve"


class BomUpdateRequest(BaseModel):
    component: str | None = None
    category: str | None = None
    quantity: int | None = None
    unit_price: float | None = None
    supplier: str | None = None
    url: str | None = None
    status: str | None = None
    notes: str | None = None


class EveAlternativesRequest(BaseModel):
    need: str = Field(min_length=3, max_length=400)
    category: str | None = None
    max_options: int = Field(default=4, ge=2, le=6)


class EveAssemblyPlanRequest(BaseModel):
    goal: str = Field(default="", max_length=500)


class EveInfraBlueprintRequest(BaseModel):
    focus: str = Field(default="full", max_length=80)


class ReviewsSyncRequest(BaseModel):
    project_id: str | None = None


class ControllerCostsRequest(BaseModel):
    period: str
    costs_data: dict[str, Any]
    budget: dict[str, float] | None = None


class ControllerForecastRequest(BaseModel):
    project: str
    horizon_months: int = 6
    assumptions: str
    historical_data: dict[str, Any] | None = None


class ControllerLLMAlertRequest(BaseModel):
    daily_spend: float
    monthly_budget: float


class ControllerMonthlyReportRequest(BaseModel):
    month: str
    all_data: dict[str, Any]


class AccountingAdviceRequest(BaseModel):
    month: str
    financial_summary: dict[str, Any]
    question: str = Field(min_length=3)


class BusinessAnalystMarketRequest(BaseModel):
    product: str
    market: str
    competitors: list[str] | None = None


class BusinessAnalystKPIsRequest(BaseModel):
    project: str
    stage: str
    business_goal: str


class BusinessAnalystUserResearchRequest(BaseModel):
    product: str
    research_question: str
    user_segment: str = ""


class BusinessAnalystBriefRequest(BaseModel):
    topic: str
    context: str
    decision_needed: str


class DataAnalystSQLRequest(BaseModel):
    question: str
    schema_context: str
    db_type: str = "postgresql"


class DataAnalystFunnelRequest(BaseModel):
    funnel_name: str
    steps: list[str]
    data: dict[str, Any]


class DataAnalystAnomalyRequest(BaseModel):
    metric: str
    recent_values: list[float]
    baseline: float
    period: str = "7 jours"


class DataAnalystDashboardRequest(BaseModel):
    dashboard_name: str
    audience: str
    kpis: list[str]
    data_sources: list[str]


