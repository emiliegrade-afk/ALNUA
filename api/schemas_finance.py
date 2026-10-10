"""Pydantic models — split from schemas.py (debt paydown)."""

from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field

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


class FinanceInvoiceCreate(BaseModel):
    vendor: str = Field(min_length=1, max_length=120)
    amount: float = Field(gt=0)
    currency: str = "EUR"
    description: str = ""
    due_date: date | None = None
    category: str = "saas_tools"
    receipt_url: str = ""
    external_ref: str = ""
    status: str = Field(default="received", pattern="^(draft|received|to_pay|paid_externally|cancelled)$")


class FinanceInvoiceUpdate(BaseModel):
    vendor: str | None = None
    amount: float | None = Field(default=None, gt=0)
    description: str | None = None
    due_date: date | None = None
    category: str | None = None
    receipt_url: str | None = None
    external_ref: str | None = None
    status: str | None = Field(
        default=None, pattern="^(draft|received|to_pay|paid_externally|cancelled)$"
    )
    notes: str | None = None


class FinanceBudgetCreate(BaseModel):
    department: str = Field(min_length=1, max_length=40)
    period: str = Field(min_length=4, max_length=20)
    amount: float = Field(ge=0)
    currency: str = "EUR"
    label: str = ""
    notes: str = ""


class FinanceBudgetUpdate(BaseModel):
    department: str | None = None
    period: str | None = None
    amount: float | None = Field(default=None, ge=0)
    spent: float | None = Field(default=None, ge=0)
    currency: str | None = None
    label: str | None = None
    notes: str | None = None


class FinanceFiscalCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    amount: float = Field(ge=0)
    due_date: date | None = None
    kind: str = "autre"
    currency: str = "EUR"
    notes: str = ""
    status: str = Field(default="upcoming", pattern="^(upcoming|due|paid_externally|cancelled)$")


class FinanceFiscalUpdate(BaseModel):
    title: str | None = None
    amount: float | None = Field(default=None, ge=0)
    due_date: date | None = None
    kind: str | None = None
    currency: str | None = None
    notes: str | None = None
    status: str | None = Field(
        default=None, pattern="^(upcoming|due|paid_externally|cancelled)$"
    )


class ElectronicsBomContextRequest(BaseModel):
    category: str | None = None
    limit: int = Field(default=20, ge=1, le=100)


class FirmwarePiProbeRequest(BaseModel):
    command: str = Field(default="uname -a", max_length=200)


class FinanceTransactionCreate(BaseModel):
    tx_date: date = Field(alias="date")
    type: str = Field(pattern="^(income|expense)$")
    amount: float = Field(gt=0)
    currency: str = "EUR"
    category: str
    project_id: str | None = None
    # Rattache une dépense à une campagne (Phase 33, ROADMAP.md) — permet de
    # calculer un "dépensé réel" par campagne sans dupliquer la donnée.
    campaign_id: str | None = None
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
    campaign_id: str | None = None
    description: str | None = None
    is_recurring: bool | None = None
    recurrence: str | None = Field(default=None, pattern="^(monthly|annual|one_time)$")

    model_config = {"populate_by_name": True}


class FinanceSummaryGenerate(BaseModel):
    month: str = Field(pattern=r"^\d{4}-\d{2}$")


class CampaignCreate(BaseModel):
    name: str
    objective: str = Field(
        pattern="^(awareness|traffic|conversions|engagement|video_views)$"
    )
    platform: str = Field(pattern="^(meta|google|tiktok)$")
    status: str = Field(default="draft", pattern="^(draft|active|paused|completed)$")
    budget_allocated_usd: float = Field(default=0, ge=0)
    project_id: str | None = None
    audience: str | None = None
    brief: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class CampaignUpdate(BaseModel):
    name: str | None = None
    objective: str | None = Field(
        default=None, pattern="^(awareness|traffic|conversions|engagement|video_views)$"
    )
    platform: str | None = Field(default=None, pattern="^(meta|google|tiktok)$")
    status: str | None = Field(default=None, pattern="^(draft|active|paused|completed)$")
    budget_allocated_usd: float | None = Field(default=None, ge=0)
    project_id: str | None = None
    audience: str | None = None
    brief: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    # Stats de performance réelle (Phase 37) — saisie manuelle, jamais
    # calculée/estimée. None = "pas encore saisi", jamais 0 par défaut.
    reach: int | None = Field(default=None, ge=0)
    engagements: int | None = Field(default=None, ge=0)
    conversions: int | None = Field(default=None, ge=0)
    revenue_generated_usd: float | None = Field(default=None, ge=0)


class FunnelSnapshotUpsert(BaseModel):
    project_id: str
    period_month: date
    visitors: int = Field(default=0, ge=0)
    interested: int = Field(default=0, ge=0)
    engaged: int = Field(default=0, ge=0)
    subscribers: int = Field(default=0, ge=0)
    customers: int = Field(default=0, ge=0)
    source_note: str | None = None
    entered_by_agent_id: str | None = None


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
    message: str = Field(default="", max_length=4000)
    agent: Literal["auto", "coo", "secretary"] = "auto"
    project: str | None = None
    session_id: str | None = Field(
        default=None,
        description="Isolates pending email drafts (hub default, or tg:<chat_id>)",
    )
    file_ids: list[str] = Field(default_factory=list, max_length=5)


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
    sector: str | None = Field(
        default=None,
        pattern="^(app|gaming|robo|company)$",
        description="Route vers l'agent secteur (Esmée/Kael/Mira/Anouk) au lieu du content générique",
    )


class PostCreate(BaseModel):
    project_id: str = Field(min_length=1)
    platform: str = Field(min_length=1)
    content_type: str = Field(min_length=1)
    text_content: str = Field(min_length=1)
    sector: str | None = Field(default=None, pattern="^(app|gaming|robo|company)$")
    author_agent_id: str | None = None
    hashtags: list[str] = Field(default_factory=list)
    layout: dict[str, Any] | None = None
    media_urls: list[str] = Field(default_factory=list)
    channel: str | None = None
    scheduled_at: str
    status: str = Field(default="pending_approval", pattern="^(draft|pending_approval|approved)$")


class PostUpdate(BaseModel):
    status: str | None = None
    text_content: str | None = None
    hashtags: list[str] | None = None
    scheduled_at: str | None = None
    image_prompt: str | None = None
    video_script: str | None = None
    layout: dict[str, Any] | None = None
    media_urls: list[str] | None = None
    channel: str | None = None
    sector: str | None = None
    author_agent_id: str | None = None
    # Stats de performance réelle (Phase 37) — saisies manuellement une fois
    # le post publié, copiées depuis les insights natifs de la plateforme.
    reach: int | None = Field(default=None, ge=0)
    engagement_count: int | None = Field(default=None, ge=0)


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    branch: str = Field(pattern="^(app|gaming|robotics|other)$")
    description: str = ""
    status: str = Field(default="dev", pattern="^(active|beta|dev|paused)$")


class RevealFileRequest(BaseModel):
    file_path: str


