"""Pydantic request/response models for the Hub API."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from fastapi import HTTPException, Header
from pydantic import BaseModel, Field

from services.beta_portal import decode_tester_token

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# New agent request models
# ---------------------------------------------------------------------------
class SecretaryDraftEmailRequest(BaseModel):
    subject: str
    context: str
    recipient: str
    tone: str = "professionnel"
    language: str = "fr"


class SecretaryTriageRequest(BaseModel):
    emails: list[dict[str, str]]


class SecretaryDraftContractRequest(BaseModel):
    contract_type: str
    party_name: str
    scope: str
    duration: str
    compensation: str = ""
    special_clauses: str = ""


class SecretaryPlanMeetingRequest(BaseModel):
    participants: list[str]
    topic: str
    duration_minutes: int = 60
    constraints: str = ""


class SecretaryMeetingNotesRequest(BaseModel):
    meeting_title: str
    raw_notes: str
    participants: list[str]


class ScoreAddRequest(BaseModel):
    agent_id: str
    action: str = Field(
        pattern="^(task_completed|task_validated|feature_shipped|bug_found_critical|bug_fixed|review_approved|document_produced|insight_actioned|custom)$"
    )
    points: int | None = Field(default=None, ge=1, le=500)
    note: str = ""


class DevBackendDesignAPIRequest(BaseModel):
    feature: str
    project: str
    constraints: str = ""


class DevBackendImplementRequest(BaseModel):
    feature: str
    project: str
    api_spec: str = ""
    tech_stack: str = "FastAPI + Supabase"


class DevBackendReviewRequest(BaseModel):
    code: str
    context: str = ""


class DevBackendDebugRequest(BaseModel):
    error: str
    context: str
    code_snippet: str = ""


class LevelDesignerQuestRequest(BaseModel):
    quest_name: str
    game: str
    lore_context: str = ""
    player_level_range: str = "1-10"
    quest_type: str = "main"


class LevelDesignerLevelRequest(BaseModel):
    level_name: str
    game: str
    biome: str = ""
    difficulty: str = "medium"
    special_mechanics: str = ""


class LevelDesignerLoreRequest(BaseModel):
    subject: str
    game: str
    lore_type: str = "history"
    length: str = "medium"


class LevelDesignerBalanceRequest(BaseModel):
    system: str
    current_values: dict[str, Any]
    player_feedback: str = ""


class AgentInstructionRequest(BaseModel):
    instruction: str


class MarketingSeoRequest(BaseModel):
    url: str


class MarketingContentRequest(BaseModel):
    type: str = "discord"
    project: str = "wyrdheim"
    topic: str
    tone: str = "épique"
    length: str = "medium"


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


class DevLogCreate(BaseModel):
    project_id: str
    content: str
    log_date: date | None = None


class TicketCreate(BaseModel):
    project_id: str
    type: str = Field(pattern="^(bug|feature|improvement|crash)$")
    priority: str = Field(default="medium", pattern="^(critical|high|medium|low)$")
    title: str = Field(min_length=1)
    description: str = ""
    source: str = Field(
        default="emilie",
        pattern="^(qa_agent|sav_bot|reviews_bot|emilie|quick_capture|beta_tester|partnerships_bot)$",
    )


class TicketUpdate(BaseModel):
    status: str | None = Field(
        default=None,
        pattern="^(open|in_progress|done|wont_fix)$",
    )
    title: str | None = None
    description: str | None = None
    priority: str | None = Field(
        default=None,
        pattern="^(critical|high|medium|low)$",
    )
    cursor_prompt: str | None = None


class FeedbackCreate(BaseModel):
    project_id: str
    source: str
    content: str
    author: str | None = None
    rating: int | None = Field(default=None, ge=1, le=5)
    sentiment: str = Field(default="neutral", pattern="^(positive|negative|neutral|mixed)$")


class RoadmapCreate(BaseModel):
    project_id: str
    title: str
    description: str = ""
    status: str = Field(
        default="planned",
        pattern="^(idea|planned|in_progress|done)$",
    )
    priority: str = Field(
        default="medium",
        pattern="^(critical|high|medium|low)$",
    )
    phase: str | None = None
    due_date: date | None = None


class RoadmapUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = Field(
        default=None,
        pattern="^(idea|planned|in_progress|done)$",
    )
    priority: str | None = Field(
        default=None,
        pattern="^(critical|high|medium|low)$",
    )


class ReleaseGenerateRequest(BaseModel):
    project_id: str
    version: str = Field(min_length=1, max_length=32)
    since_date: date | None = None
    dev_log_ids: list[str] | None = None


class ReleaseUpdate(BaseModel):
    app_store_notes: str | None = None
    google_play_notes: str | None = None
    changelog_md: str | None = None
    status: str | None = Field(default=None, pattern="^(draft|published)$")
    release_date: date | None = None


class QuickCaptureRequest(BaseModel):
    type: str = Field(pattern="^(ticket|idea|roadmap|note)$")
    content: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    priority: str | None = Field(
        default="medium",
        pattern="^(critical|high|medium|low)$",
    )
    phase: str | None = None
    due_date: date | None = None
    linked_ticket_id: str | None = None


class BrainstormRequest(BaseModel):
    project_id: str
    topic: str
    context_notes: str = ""


class BrainstormChatRequest(BaseModel):
    message: str
    project_id: str | None = None
    session_id: str | None = None


class SAVQuestion(BaseModel):
    project_id: str
    question: str
    author: str | None = None


class FAQCreate(BaseModel):
    project_id: str
    question: str
    answer: str
    tags: list[str] = []


class TransactionCreate(BaseModel):
    project_id: str | None = None
    type: str = Field(pattern="^(income|expense|revenue)$")
    amount: float
    currency: str = "EUR"
    category: str
    description: str | None = None
    transaction_date: date | None = None
    is_recurring: bool = False
    recurrence: str | None = None


class FinanceTransactionCreate(BaseModel):
    tx_date: date = Field(alias="date")
    type: str = Field(pattern="^(income|expense)$")
    amount: float = Field(gt=0)
    currency: str = "EUR"
    category: str
    project_id: str | None = None
    description: str | None = None
    is_recurring: bool = False
    recurrence: str | None = Field(default=None, pattern="^(monthly|annual|one_time)$")

    model_config = {"populate_by_name": True}


class FinanceTransactionUpdate(BaseModel):
    tx_date: date | None = Field(default=None, alias="date")
    type: str | None = Field(default=None, pattern="^(income|expense)$")
    amount: float | None = Field(default=None, gt=0)
    currency: str | None = None
    category: str | None = None
    project_id: str | None = None
    description: str | None = None
    is_recurring: bool | None = None
    recurrence: str | None = Field(default=None, pattern="^(monthly|annual|one_time)$")

    model_config = {"populate_by_name": True}


class FinanceSummaryGenerate(BaseModel):
    month: str = Field(pattern=r"^\d{4}-\d{2}$")


class AnalyticsCreate(BaseModel):
    model_config = {"populate_by_name": True}

    project_id: str
    metric_name: str = Field(
        pattern="^(downloads|active_users|subscriptions|mrr|churn|web_visitors)$"
    )
    value: float
    record_date: date | None = Field(default=None, alias="date")
    source: str = Field(
        default="stripe",
        pattern="^(app_store|google_play|stripe|revenuecat|plausible)$",
    )


class COOInstruction(BaseModel):
    instruction: str = Field(min_length=1)
    project: str | None = None


class COOInstructionResponse(BaseModel):
    response: str
    issue_created: bool = False
    issue_number: int | None = None
    issue_url: str | None = None
    repo: str | None = None


class ContentGenerateRequest(BaseModel):
    project_id: str
    dev_log: str
    content_types: list[str] = Field(min_length=1)
    platforms: list[str] = Field(min_length=1)
    alnua_global: bool = False


class PostUpdate(BaseModel):
    status: str | None = None
    text_content: str | None = None
    hashtags: list[str] | None = None
    scheduled_at: str | None = None
    image_prompt: str | None = None
    video_script: str | None = None


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    branch: str = Field(pattern="^(app|gaming|robotics|other)$")
    description: str = ""
    status: str = Field(default="dev", pattern="^(active|beta|dev|paused)$")


class RevealFileRequest(BaseModel):
    file_path: str


class BetaRegisterRequest(BaseModel):
    project_slug: str
    email: str = Field(min_length=3)
    first_name: str = Field(min_length=1)
    device: str | None = None
    os_version: str | None = None
    app_version: str | None = None


class BetaFeedbackRequest(BaseModel):
    project_slug: str
    type: str = Field(pattern="^(bug|suggestion|crash|ux|autre)$")
    title: str = Field(min_length=1)
    description: str = ""
    severity: str | None = Field(
        default=None,
        pattern="^(bloquant|majeur|mineur|cosmétique)$",
    )
    screenshot_base64: str | None = None


class BetaInviteRequest(BaseModel):
    project_id: str


class WaitlistJoinRequest(BaseModel):
    project_slug: str
    email: str = Field(min_length=3)
    first_name: str | None = None
    source: str | None = None
    message: str | None = None


class WaitlistNotifyRequest(BaseModel):
    project_id: str
    subject: str = Field(min_length=1)
    message_md: str = Field(min_length=1)
    status_filter: str | None = Field(
        default=None,
        pattern="^(waiting|notified|converted)$",
    )


class WaitlistStatusUpdate(BaseModel):
    status: str = Field(pattern="^(waiting|notified|converted)$")


class WaitlistGenerateEmailRequest(BaseModel):
    project_id: str


class PartnerCreate(BaseModel):
    type: str
    direction: str = Field(pattern="^(outbound|inbound)$")
    name: str = Field(min_length=1)
    status: str = "prospect"
    company: str | None = None
    email: str | None = None
    instagram_url: str | None = None
    tiktok_url: str | None = None
    youtube_url: str | None = None
    website: str | None = None
    audience_size: int | None = None
    audience_description: str | None = None
    project_ids: list[str] | None = None
    notes: str | None = None
    next_followup: date | None = None
    last_contact_date: date | None = None


class PartnerUpdate(BaseModel):
    type: str | None = None
    direction: str | None = Field(default=None, pattern="^(outbound|inbound)$")
    name: str | None = None
    status: str | None = None
    company: str | None = None
    email: str | None = None
    instagram_url: str | None = None
    tiktok_url: str | None = None
    youtube_url: str | None = None
    website: str | None = None
    audience_size: int | None = None
    audience_description: str | None = None
    project_ids: list[str] | None = None
    notes: str | None = None
    contract_path: str | None = None
    next_followup: date | None = None
    last_contact_date: date | None = None


class PartnerInteractionCreate(BaseModel):
    type: str | None = None
    note: str | None = None
    date: datetime | None = None


class AffiliateLinkCreate(BaseModel):
    partner_id: str
    project_id: str | None = None
    code: str | None = None
    redirect_url: str
    commission_type: str | None = Field(default=None, pattern="^(percent|fixed)$")
    commission_value: float | None = None
    active: bool = True


class AffiliateLinkUpdate(BaseModel):
    redirect_url: str | None = None
    commission_type: str | None = Field(default=None, pattern="^(percent|fixed)$")
    commission_value: float | None = None
    active: bool | None = None
    project_id: str | None = None


class AffiliateConversionBody(BaseModel):
    revenue: float = 0.0


class PartnershipRequestCreate(BaseModel):
    name: str = Field(min_length=1)
    email: str = Field(min_length=3)
    type: str | None = None
    message: str | None = None
    instagram_url: str | None = None
    tiktok_url: str | None = None
    website: str | None = None
    audience_size: str | None = None
    project_interest: str | None = None


class PartnershipRequestUpdate(BaseModel):
    status: str | None = Field(
        default=None,
        pattern="^(new|reviewed|converted|declined)$",
    )


# ---------------------------------------------------------------------------
# Orchestration (n8n workflows)
# ---------------------------------------------------------------------------
class OrchestrationMorningRequest(BaseModel):
    weekly_plan: bool = False


class OrchestrationSpecQaRequest(BaseModel):
    spec_text: str = Field(min_length=10)
    context: str = ""
    rounds: int = Field(default=2, ge=1, le=3)
    stop_on_approve: bool = True
    create_qa_ticket: bool = True
    project_id: str | None = None
    project_slug: str | None = None
    ticket_title: str | None = None


class OrchestrationGithubPrRequest(BaseModel):
    repo: str = Field(min_length=1)
    pr_number: int = Field(ge=1)
    title: str = ""
    diff_summary: str = ""
    changed_files: str = ""


class OrchestrationWelcomeRequest(BaseModel):
    recipient_name: str = Field(min_length=1)
    recipient_email: str = Field(min_length=3)
    project: str = "ALNUA"
    language: str = "fr"


class OrchestrationContentSprintRequest(BaseModel):
    brief: str = Field(min_length=5)
    platforms: list[str] | None = None
    project: str = "ALNUA"


class AcademySeedRequest(BaseModel):
    level: int = Field(ge=1, le=4, description="Niveau curriculum 1-4")
    dry_run: bool = False
    mark_first_ready: bool = False


class AcademySprintRequest(BaseModel):
    level: int | None = Field(default=None, ge=1, le=4)
    seed_if_missing: bool = True
    mark_ready_count: int = Field(default=3, ge=1, le=10)


class AcademyPollRequest(BaseModel):
    mark_ready_if_idle: bool = True
    mark_ready_count: int = Field(default=2, ge=0, le=10)
    notify: bool = False


class NuawayCeoGoRequest(BaseModel):
    approved: bool = True
    note: str = Field(default="", max_length=500)


class EngineeringSpecGenerateRequest(BaseModel):
    force: bool = False
    debate_rounds: int = Field(default=1, ge=0, le=3)
    refine_with_pm: bool = True


class PrdDecomposeRequest(BaseModel):
    repo_slug: str | None = Field(
        default=None,
        description="hub | nomad | naia — auto si omis",
    )
    dry_run: bool = False
    mark_ready_count: int = Field(default=3, ge=0, le=20)
    force_spec: bool = False
    debate_rounds: int = Field(default=1, ge=0, le=3)


class PrdDecomposeOrchestrationRequest(BaseModel):
    dossier_id: str = Field(min_length=8)
    repo_slug: str | None = None
    dry_run: bool = False
    mark_ready_count: int = Field(default=3, ge=0, le=20)
    force_spec: bool = False


class SentrySimulateRequest(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    message: str = ""
    project_slug: str = "nuaway"
    level: str = "error"
    dry_run: bool = False


# ---------------------------------------------------------------------------
# Tier 2 Services — Trend Monitor, Deep Research, Plan Executor, Code Graph
# ---------------------------------------------------------------------------

class TrendBriefRequest(BaseModel):
    topics: list[str] = Field(min_length=1, description="Thèmes à surveiller")
    sources: list[str] = Field(
        default_factory=lambda: ["hackernews", "reddit", "github"],
        description="Sources : hackernews | reddit | github",
    )
    agent_id: str = Field(default="marketing", description="Agent qui synthétise")
    limit: int = Field(default=20, ge=5, le=50)


class TrendRawRequest(BaseModel):
    sources: list[str] = Field(
        default_factory=lambda: ["hackernews", "reddit", "github"],
    )
    topics: list[str] = Field(default_factory=list)
    limit: int = Field(default=30, ge=5, le=100)


class DeepResearchRequest(BaseModel):
    query: str = Field(min_length=5, description="Question ou sujet à rechercher")
    context: str = Field(default="", description="Contexte supplémentaire")
    rounds: int = Field(default=3, ge=1, le=3, description="Nombre de rounds (1-3)")
    agent_id: str = Field(
        default="brainstorm",
        description="Agent : brainstorm | rnd_agent | analyst_business",
    )


class QuickResearchRequest(BaseModel):
    query: str = Field(min_length=5)
    context: str = ""
    agent_id: str = "brainstorm"


class PlanStepRequest(BaseModel):
    step_id: str
    description: str
    agent_id: str
    method: str
    kwargs: dict[str, Any] = Field(default_factory=dict)
    depends_on: list[str] = Field(default_factory=list)


class PlanExecuteRequest(BaseModel):
    title: str
    steps: list[PlanStepRequest]
    context: str = ""
    max_concurrent: int = Field(default=3, ge=1, le=5)
    stop_on_failure: bool = False


class CooRunRequest(BaseModel):
    objective: str = Field(min_length=5, description="Objectif à atteindre")
    context: str = Field(default="", description="Contexte supplémentaire")
    max_concurrent: int = Field(default=3, ge=1, le=5)
    stop_on_failure: bool = False


class CodeGraphQueryRequest(BaseModel):
    question: str = Field(min_length=5, description="Question sur le codebase")
    agent_id: str = Field(default="analyst_data")
    rebuild: bool = Field(default=False, description="Forcer le rebuild du graphe")


class MemoryCompressRequest(BaseModel):
    agent_id: str
    threshold: int = Field(default=20, ge=5)


# ---------------------------------------------------------------------------
# CreatorFlow (Sprint 0)
# ---------------------------------------------------------------------------

CfPlatform = Literal["youtube", "instagram"]
CfAssetType = Literal["video", "image", "text"]
CfAssetStatus = Literal["pending", "analyzed", "scheduled", "exported"]


class CfAssetCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str | None = None
    file_url: str = Field(min_length=1)
    file_type: CfAssetType
    file_size_bytes: int | None = Field(default=None, ge=0)
    duration_seconds: int | None = Field(default=None, ge=0)
    mime_type: str | None = None
    project_id: str | None = None


class CfAssetOut(CfAssetCreate):
    id: str
    user_id: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    ai_analysis: dict[str, Any] = Field(default_factory=dict)
    status: CfAssetStatus
    created_at: str
    updated_at: str
    storage_path: str | None = None


class CfProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None


class CfProjectOut(BaseModel):
    id: str
    user_id: str
    name: str
    slug: str
    description: str | None = None
    is_default: bool = False
    created_at: str
    updated_at: str


CfEntryStatus = Literal["draft", "scheduled", "exported", "failed"]


class CfCalendarEntryCreate(BaseModel):
    asset_id: str | None = None
    project_id: str | None = None
    platform: CfPlatform
    scheduled_at: datetime
    title: str = Field(min_length=1, max_length=500)
    caption: str | None = None
    hashtags: list[str] = Field(default_factory=list)
    ai_suggested: bool = False
    ai_timing_score: float | None = Field(default=None, ge=0.0, le=1.0)


class CfCalendarEntryOut(BaseModel):
    id: str
    user_id: str
    project_id: str | None = None
    asset_id: str | None = None
    platform: CfPlatform
    scheduled_at: str
    title: str
    caption: str | None = None
    hashtags: list[str] = Field(default_factory=list)
    ai_suggested: bool = False
    ai_timing_score: float | None = None
    status: CfEntryStatus
    created_at: str
    updated_at: str


class CfCalendarEntryUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    caption: str | None = None
    hashtags: list[str] | None = None
    scheduled_at: datetime | None = None


class CfTimingSuggestion(BaseModel):
    platform: CfPlatform
    suggested_at: str
    score: float = Field(ge=0.0, le=1.0)
    reason: str


CfExportStatus = Literal["pending", "processing", "success", "failed"]


class CfExportCreate(BaseModel):
    calendar_entry_id: str = Field(min_length=1)
    platform: CfPlatform


class CfExportOut(BaseModel):
    id: str
    user_id: str
    calendar_entry_id: str
    platform: CfPlatform
    status: CfExportStatus
    platform_post_id: str | None = None
    platform_post_url: str | None = None
    error_message: str | None = None
    adapted_metadata: dict[str, Any] = Field(default_factory=dict)
    started_at: str | None = None
    completed_at: str | None = None
    created_at: str


class CfPlatformConnectionOut(BaseModel):
    platform: CfPlatform
    is_active: bool
    platform_username: str | None = None
    connected_at: str | None = None


class CfPlatformConnectRequest(BaseModel):
    platform: CfPlatform
    redirect_url: str | None = None


class CfPlatformConnectOut(BaseModel):
    platform: CfPlatform
    oauth_url: str | None = None
    already_connected: bool = False
    message: str | None = None


class CfPlatformExportStats(BaseModel):
    platform: CfPlatform
    total: int = Field(ge=0)
    success: int = Field(ge=0)
    failed: int = Field(ge=0)


class CfExportStatsOut(BaseModel):
    total: int = Field(ge=0)
    success: int = Field(ge=0)
    failed: int = Field(ge=0)
    pending: int = Field(ge=0)
    success_rate_pct: float = Field(ge=0.0, le=100.0)
    real_exports: int = Field(ge=0)
    mock_exports: int = Field(ge=0)
    last_7_days: int = Field(ge=0)
    by_platform: list[CfPlatformExportStats] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# CreatorFlow V1 — Think (ideas, DNA, BYOK)
# ---------------------------------------------------------------------------

CfIdeaStatus = Literal["spark", "developing", "ready_to_shoot", "in_production", "published", "archived"]
CfDnaScope = Literal["global", "youtube", "instagram"]
CfPlatformTarget = Literal["youtube", "instagram", "both"]
CfArtifactType = Literal["script", "shot_list", "brainstorm_summary"]
CfMessageRole = Literal["user", "assistant"]


class CfIdeaCreate(BaseModel):
    content: str = Field(min_length=1, max_length=10000)
    title: str | None = Field(default=None, max_length=200)
    project_id: str | None = None
    tags: list[str] = Field(default_factory=list)
    platform_target: CfPlatformTarget | None = None
    source_url: str | None = None
    notes: str | None = None


class CfIdeaUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, min_length=1, max_length=10000)
    status: CfIdeaStatus | None = None
    tags: list[str] | None = None
    platform_target: CfPlatformTarget | None = None
    source_url: str | None = None
    notes: str | None = None
    project_id: str | None = None


class CfIdeaOut(BaseModel):
    id: str
    user_id: str
    project_id: str | None = None
    title: str | None = None
    content: str
    status: CfIdeaStatus
    tags: list[str] = Field(default_factory=list)
    platform_target: CfPlatformTarget | None = None
    source_url: str | None = None
    notes: str | None = None
    linked_asset_id: str | None = None
    linked_calendar_entry_id: str | None = None
    created_at: str
    updated_at: str


class CfCreatorDnaUpsert(BaseModel):
    scope: CfDnaScope = "global"
    project_id: str | None = None
    voice_tone: str | None = None
    audience: str | None = None
    brand_promise: str | None = None
    taboos: list[str] = Field(default_factory=list)
    style_refs: list[str] = Field(default_factory=list)
    extra: dict[str, Any] = Field(default_factory=dict)


class CfCreatorDnaOut(BaseModel):
    id: str
    user_id: str
    project_id: str | None = None
    scope: CfDnaScope
    voice_tone: str | None = None
    audience: str | None = None
    brand_promise: str | None = None
    taboos: list[str] = Field(default_factory=list)
    style_refs: list[str] = Field(default_factory=list)
    extra: dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str


class CfIdeaMessageOut(BaseModel):
    id: str
    idea_id: str
    user_id: str
    role: CfMessageRole
    content: str
    created_at: str


class CfIdeaBrainstormRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)


class CfIdeaBrainstormResponse(BaseModel):
    message: CfIdeaMessageOut
    source: str = "llm"


class CfIdeaScheduleRequest(BaseModel):
    platform: CfPlatform | None = None
    scheduled_at: datetime | None = None
    title: str | None = Field(default=None, max_length=500)
    caption: str | None = None


class CfIdeaLinkAssetRequest(BaseModel):
    asset_id: str = Field(min_length=1)


class CfIdeaPipelineOut(BaseModel):
    idea: CfIdeaOut
    asset: CfAssetOut | None = None
    calendar_entry: CfCalendarEntryOut | None = None
    steps: dict[str, bool]


class CfIdeaArtifactOut(BaseModel):
    id: str
    idea_id: str
    user_id: str
    artifact_type: CfArtifactType
    version: int
    content: dict[str, Any] = Field(default_factory=dict)
    created_at: str


class CfArtifactGenerateResponse(BaseModel):
    artifact: CfIdeaArtifactOut
    source: str = "llm"


class CfUserAiSettingsUpdate(BaseModel):
    api_key: str | None = None
    use_own_key: bool | None = None
    default_model: str | None = None


class CfUserAiSettingsOut(BaseModel):
    user_id: str
    provider: str = "openrouter"
    use_own_key: bool = False
    default_model: str | None = None
    api_key_masked: str | None = None
    has_key: bool = False


class CfStudioCreateJobRequest(BaseModel):
    tool_id: str = Field(min_length=1)
    prompt: str | None = None
    params: dict[str, Any] = Field(default_factory=dict)


class CfStudioLinkAssetRequest(BaseModel):
    file_url: str = Field(min_length=1)
    title: str | None = None


class CfStudioJobOut(BaseModel):
    id: str
    idea_id: str
    user_id: str
    project_id: str | None = None
    tool_id: str
    capability: str
    provider: str
    model_slug: str
    status: str
    prompt: str
    params: dict[str, Any] = Field(default_factory=dict)
    artifact_url: str | None = None
    asset_id: str | None = None
    error_message: str | None = None
    provider_job_id: str | None = None
    created_at: str
    updated_at: str | None = None


class CfStudioToolOut(BaseModel):
    id: str
    label: str
    description: str
    capability: str
    provider: str
    model_slug: str
    default_aspect: str
    platforms: list[str]
    provider_ready: bool


class CfStudioCatalogOut(BaseModel):
    tools: list[CfStudioToolOut]
    providers: dict[str, dict[str, Any]]


class CfStudioPromptPreviewOut(BaseModel):
    prompt_kind: str
    prompt: str
    negative_prompt: str = ""
    style_tags: list[str] = Field(default_factory=list)
    default_params: dict[str, Any] = Field(default_factory=dict)


class CfStudioTemplateOut(BaseModel):
    id: str
    label: str
    description: str
    tool_ids: list[str] = Field(default_factory=list)
    platforms: list[str] = Field(default_factory=list)
    prompt_suffix: str = ""
    prompt_prefix: str = ""
    negative_prompt: str = ""
    params: dict[str, Any] = Field(default_factory=dict)


class CfStudioFlowNodeData(BaseModel):
    tool_id: str = Field(min_length=1)
    label: str = ""
    prompt: str = ""
    params: dict[str, Any] = Field(default_factory=dict)


class CfStudioFlowNode(BaseModel):
    id: str = Field(min_length=1)
    type: str = "studioTool"
    position: dict[str, float]
    data: CfStudioFlowNodeData


class CfStudioFlowEdge(BaseModel):
    id: str = Field(min_length=1)
    source: str = Field(min_length=1)
    target: str = Field(min_length=1)


class CfStudioFlowCreateRequest(BaseModel):
    name: str | None = None
    nodes: list[CfStudioFlowNode] | None = None
    edges: list[CfStudioFlowEdge] | None = None


class CfStudioFlowUpdateRequest(BaseModel):
    name: str | None = None
    nodes: list[CfStudioFlowNode] | None = None
    edges: list[CfStudioFlowEdge] | None = None


class CfStudioFlowOut(BaseModel):
    id: str
    user_id: str
    idea_id: str
    project_id: str | None = None
    name: str
    nodes: list[dict[str, Any]] = Field(default_factory=list)
    edges: list[dict[str, Any]] = Field(default_factory=list)
    last_run: dict[str, Any] | None = None
    created_at: str
    updated_at: str | None = None


class CfStudioFlowRunOut(BaseModel):
    status: str
    started_at: str | None = None
    finished_at: str | None = None
    node_jobs: dict[str, str] = Field(default_factory=dict)
    error: str | None = None


def beta_tester_auth(authorization: str | None = Header(default=None)) -> dict[str, str]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token requis")
    token = authorization.removeprefix("Bearer ").strip()
    return decode_tester_token(token)

