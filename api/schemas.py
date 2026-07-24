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


class MilestoneCreateRequest(BaseModel):
    title: str
    date_iso: str
    pole: str = ""
    description: str = ""


class MilestoneUpdateRequest(BaseModel):
    title: str | None = None
    date_iso: str
    pole: str | None = None
    description: str | None = None


class MilestoneValidateRequest(BaseModel):
    validated: bool = True


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


class AssistantChatRequest(BaseModel):
    message: str = Field(min_length=1)
    agent: Literal["auto", "coo", "secretary"] = "auto"
    project: str | None = None
    session_id: str | None = Field(
        default=None,
        description="Isolates pending email drafts (hub default, or tg:<chat_id>)",
    )


class AssistantChatResponse(BaseModel):
    agent_id: str
    agent_name: str
    response: str
    response_id: str | None = None
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


class WakeAgentsRequest(BaseModel):
    """CEO kick — retry failed + queue next Academy issues."""

    retry_failed: bool = True
    mark_ready_count: int | None = Field(default=None, ge=1, le=10)
    sync: bool = True
    notify: bool = False


class AcademyHumanLessonRequest(BaseModel):
    """CEO manual fix → agents learn via journal + Mem0."""

    cause: str = Field(min_length=5, max_length=2000)
    fix: str = Field(min_length=5, max_length=2000)
    files: list[str] = Field(default_factory=list)
    issue_number: int | None = Field(default=None, ge=1)
    repo_slug: str = Field(default="academy", max_length=64)
    agent_id: str = Field(default="dev_app", max_length=64)


class EngineeringSpecGenerateRequest(BaseModel):
    force: bool = False
    debate_rounds: int = Field(default=1, ge=0, le=3)
    refine_with_pm: bool = True


class PrdDecomposeRequest(BaseModel):
    repo_slug: str | None = Field(
        default=None,
        description="hub | registry slug — auto si omis",
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
    project_slug: str = "hub"
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


class LibraryResearchRequest(BaseModel):
    """CEO research — archive everything in bureau library."""

    query: str = Field(min_length=3, max_length=500)
    bureaus: list[str] | None = Field(
        default=None,
        description="Optional bureau ids to prioritize (hub, app, rd, …)",
    )
    requested_by: str = Field(default="ceo", max_length=64)
    wait: bool = Field(
        default=False,
        description="Block until research completes (UI sync mode)",
    )


class LibraryReportRequest(BaseModel):
    days: int = Field(default=7, ge=1, le=90)


class LibraryEnrichRequest(BaseModel):
    """Push library entries into Mem0 for all bureau agents (Phase 3)."""

    days: int = Field(default=30, ge=1, le=180)
    timing: str | None = Field(
        default=None,
        description="Optional filter: now | later",
    )
    limit: int = Field(default=25, ge=1, le=100)


class LibraryDistributeAllRequest(BaseModel):
    """Distribute every library entry to bureau agents (background job)."""

    skip_distributed: bool = Field(
        default=True,
        description="Skip entry×agent pairs already in the distribution ledger",
    )
    timing: str | None = Field(
        default=None,
        description="Optional filter: now | later",
    )
    run_learning: bool = Field(
        default=False,
        description="Chain learn job after distribute (heavy — off by default)",
    )


class LibraryRetentionApplyRequest(BaseModel):
    compress: bool = True
    purge: bool = True
    dry_run: bool = False


class NomenclatureNextRequest(BaseModel):
    kind: str = Field(description="APP | GDD | LORE | ASSET | BUG | COLLAB | RND")
    slug: str | None = None
    scope: str | None = Field(default=None, description="WYR | NWA for lore/gdd/asset")
    subtype: str | None = Field(default=None, description="ENV | CHAR | VFX | MAT | SFX for assets")
    feature: bool = Field(default=False, description="APP feature ref (F00n)")
    create_note: bool = Field(default=False, description="Create Obsidian stub in vault")
    title: str | None = None


class NomenclatureValidateRequest(BaseModel):
    ref: str


def beta_tester_auth(authorization: str | None = Header(default=None)) -> dict[str, str]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token requis")
    token = authorization.removeprefix("Bearer ").strip()
    return decode_tester_token(token)

