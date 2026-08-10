"""R&D Dossier Hub — core output / entity Pydantic models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from services.rnd_schemas_literals import (
    CeoStatus,
    DossierStatus,
    SectionStatus,
    SocialCalendarStatus,
    SocialPhase,
)


class RndIdeaOut(BaseModel):
    """Idea returned to API clients (JSON + Supabase merged)."""

    id: str
    db_id: str | None = None
    title: str
    description: str = ""
    source: str = "rnd_agent"
    status: str | None = None
    score: int | None = None
    market_score: int | None = None
    feasibility_score: int | None = None
    vision_score: int | None = None
    verdict: str | None = None
    verdict_reason: str | None = None
    reasoning: str | None = None
    next_step: str | None = None
    why_now: str | None = None
    effort: str | None = None
    domain: str | None = None
    spec_file: str | None = None
    lifecycle_status: str = "raw"
    dossier_id: str | None = None
    incubator_stage: str = "idee"
    created_at: str | None = None
    evaluated_at: str | None = None


class RndDossierSectionOut(BaseModel):
    id: str
    dossier_id: str
    section_key: str
    title: str
    content_md: str = ""
    status: SectionStatus = "draft"
    sort_order: int = 0
    validated_by: str | None = None
    validated_at: str | None = None
    revision_note: str | None = None


class RndDossierEventOut(BaseModel):
    id: str
    dossier_id: str
    event_type: str
    actor: str
    payload: dict[str, Any] | None = None
    created_at: str


class FinanceJson(BaseModel):
    capex_eur: float = 0
    capex_dev_eur: float = 0
    capex_marketing_eur: float = 0
    opex_monthly_eur: float = 0
    llm_monthly_eur: float = 0
    dev_weeks: int = 0
    dev_hours: int = 0
    break_even_months: int | None = None
    runway_impact_months: float = 0
    treasury_ytd_eur: float = 0
    verdict_finance: str = "tight"
    assumptions: list[str] = Field(default_factory=list)
    funding_options: list[str] = Field(default_factory=list)
    reasoning: str = ""
    revenue_hypothesis: dict[str, Any] = Field(default_factory=dict)


class RndDossierOut(BaseModel):
    id: str
    idea_id: str
    idea_legacy_id: str | None = None
    slug: str
    title: str
    tagline: str | None = None
    domain: str
    branch: str | None = None
    status: DossierStatus = "draft"
    ceo_status: CeoStatus = "pending"
    ceo_note: str | None = None
    committee_team: list[dict[str, Any]] = Field(default_factory=list)
    vision_snapshot: str | None = None
    competitive_context: str | None = None
    finance_json: dict[str, Any] | None = None
    deck_html_path: str | None = None
    deck_pdf_path: str | None = None
    one_pager_md: str | None = None
    ceo_package_json: dict[str, Any] | None = None
    committee_report_md: str | None = None
    dispatch_json: dict[str, Any] | None = None
    dispatch_status: str = "pending"
    project_id: str | None = None
    local_path: str | None = None
    sections: list[RndDossierSectionOut] = Field(default_factory=list)
    sections_validated_count: int = 0
    sections_total_count: int = 0
    created_at: str | None = None
    updated_at: str | None = None


class RndDossierAssetOut(BaseModel):
    id: str
    dossier_id: str
    section_key: str | None = None
    asset_type: str
    file_path: str
    public_url: str | None = None
    image_prompt: str | None = None
    generation_model: str | None = None
    width: int | None = None
    height: int | None = None
    metadata: dict[str, Any] | None = None
    created_at: str | None = None


class RndDeckGenerateResult(BaseModel):
    html_path: str | None = None
    pdf_path: str | None = None
    html_url: str | None = None
    pdf_url: str | None = None
    slide_count: int = 0
    pdf_error: str | None = None
    message: str = "Deck généré"


class RndDossierListItem(BaseModel):
    id: str
    slug: str
    title: str
    domain: str
    branch: str | None = None
    status: DossierStatus
    ceo_status: CeoStatus
    idea_legacy_id: str | None = None
    sections_validated_count: int = 0
    sections_total_count: int = 0
    created_at: str | None = None
    updated_at: str | None = None


class RndProductPageOut(BaseModel):
    id: str
    dossier_id: str
    project_id: str | None = None
    slug: str
    title: str
    tagline: str | None = None
    description_html: str | None = None
    hero_asset_id: str | None = None
    features: list[dict[str, Any]] = Field(default_factory=list)
    pricing_model: str | None = None
    faq: list[dict[str, str]] = Field(default_factory=list)
    seo_title: str | None = None
    seo_description: str | None = None
    waitlist_enabled: bool = False
    published: bool = False
    published_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class RndSocialCalendarItemOut(BaseModel):
    id: str
    dossier_id: str
    phase: SocialPhase
    milestone: str | None = None
    planned_at: str | None = None
    post_id: str | None = None
    status: SocialCalendarStatus = "planned"
    notes: str | None = None
    created_at: str | None = None
    post: dict[str, Any] | None = None
    platforms: list[str] = Field(default_factory=list)
    content_type: str | None = None
