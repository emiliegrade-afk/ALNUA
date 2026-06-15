"""Pydantic schemas for R&D Dossier Hub."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Enums (string literals for API validation)
# ---------------------------------------------------------------------------

LifecycleStatus = Literal[
    "raw", "dossier_draft", "in_committee", "sections_review",
    "ceo_review", "approved", "rejected", "in_conception", "shipped", "archived",
]

DossierStatus = Literal[
    "draft", "committee_active", "partial_validated", "ready_for_ceo",
    "ceo_approved", "ceo_rejected", "in_conception", "published", "archived",
]

CeoStatus = Literal["pending", "approved", "rejected", "pivot_requested"]

SectionStatus = Literal["draft", "under_review", "validated", "needs_revision", "skipped"]

SectionKey = Literal[
    "problem", "solution", "market", "mvp", "feasibility", "business_case",
    "manufacturing", "lore", "visual_identity", "social_strategy", "risks", "decision",
]

Branch = Literal["app", "gaming", "robotics", "other"]

# ---------------------------------------------------------------------------
# Section definitions
# ---------------------------------------------------------------------------

SECTION_DEFINITIONS: dict[str, dict[str, Any]] = {
    "problem": {"title": "Problème & opportunité", "sort_order": 10},
    "solution": {"title": "Solution produit", "sort_order": 20},
    "market": {"title": "Marché & concurrence", "sort_order": 30},
    "mvp": {"title": "MVP & roadmap", "sort_order": 40},
    "feasibility": {"title": "Faisabilité technique", "sort_order": 50},
    "business_case": {"title": "Business case & coûts", "sort_order": 60},
    "manufacturing": {"title": "Fabrication & BOM", "sort_order": 70},
    "lore": {"title": "Univers & narration", "sort_order": 75},
    "visual_identity": {"title": "Identité visuelle", "sort_order": 80},
    "social_strategy": {"title": "Stratégie réseaux sociaux", "sort_order": 90},
    "risks": {"title": "Risques & mitigations", "sort_order": 100},
    "decision": {"title": "Recommandation & décision", "sort_order": 110},
}

DOMAIN_TO_BRANCH: dict[str, str] = {
    "app": "app",
    "saas": "app",
    "ia": "app",
    "jeu": "gaming",
    "game": "gaming",
    "gaming": "gaming",
    "hardware": "robotics",
    "robotique": "robotics",
    "robotics": "robotics",
}

# ---------------------------------------------------------------------------
# API models
# ---------------------------------------------------------------------------


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
    status: DossierStatus
    ceo_status: CeoStatus
    idea_legacy_id: str | None = None
    sections_validated_count: int = 0
    sections_total_count: int = 0
    created_at: str | None = None
    updated_at: str | None = None


class RndDossierCreateBody(BaseModel):
    idea_id: str = Field(description="legacy_id or UUID")
    title: str | None = None
    domain: str | None = None


class RndUserSubmitBody(BaseModel):
    """Structured proposal from Emilie — creates idea + dossier in one step."""

    title: str = Field(min_length=3, max_length=200)
    tagline: str | None = Field(default=None, max_length=500)
    domain: str = Field(default="autre", max_length=80)
    why_now: str | None = Field(default=None, max_length=4000)
    sections: dict[str, str] = Field(
        default_factory=dict,
        description="Optional section keys: problem, solution, market, mvp, feasibility, risks",
    )
    enrich: bool = Field(
        default=False,
        description="If true, agents enrich empty sections after creation (user text preserved)",
    )
    source: str = "Emilie"


class RndSectionUpdateBody(BaseModel):
    content_md: str = Field(min_length=1, max_length=50000)


class RndDossierPatchBody(BaseModel):
    title: str | None = None
    tagline: str | None = None
    status: DossierStatus | None = None
    ceo_status: CeoStatus | None = None
    ceo_note: str | None = None


class RndPromoteResponse(BaseModel):
    dossier: RndDossierOut
    idea: RndIdeaOut
    message: str


class RndSectionActionBody(BaseModel):
    section_key: str
    note: str | None = None


class RndSectionRevisionBody(BaseModel):
    section_key: str
    revision_note: str = Field(min_length=1)


class RndFinanceReviseBody(BaseModel):
    constraint: str | None = None


class RndCommitteeStartBody(BaseModel):
    mode: str = "free"
    active_section: str | None = None
    force_new: bool = False


class RndCommitteeMessageBody(BaseModel):
    message: str = Field(min_length=1)
    target_speaker: str | None = None


class RndCommitteeCloseBody(BaseModel):
    apply_sections: bool = True
    generate_ceo_package: bool = False


class RndAssetsGenerateBody(BaseModel):
    force: bool = False


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


class RndProductGenerateBody(BaseModel):
    force: bool = False
    waitlist_enabled: bool | None = None


class RndProductPatchBody(BaseModel):
    tagline: str | None = None
    description_html: str | None = None
    features: list[dict[str, Any]] | None = None
    faq: list[dict[str, str]] | None = None
    pricing_model: str | None = None
    seo_title: str | None = None
    seo_description: str | None = None
    waitlist_enabled: bool | None = None


class RndCeoGenerateBody(BaseModel):
    force: bool = False


class RndCeoDecisionBody(BaseModel):
    ceo_status: CeoStatus = Field(
        description="approved | rejected | pivot_requested",
    )
    ceo_note: str | None = None


SocialPhase = Literal[
    "internal", "behind_scenes", "teaser", "pre_launch", "launch", "post_launch",
]

SocialCalendarStatus = Literal[
    "planned", "generated", "approved", "published", "cancelled",
]


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
    # Enriched from posts_queue when loaded
    post: dict[str, Any] | None = None
    platforms: list[str] = Field(default_factory=list)
    content_type: str | None = None


class RndSocialCalendarGenerateBody(BaseModel):
    force: bool = False
    launch_date: str | None = Field(
        default=None,
        description="ISO date for launch phase anchor (default: +21 days)",
    )


class RndSocialGeneratePostBody(BaseModel):
    platforms: list[str] | None = None


class RndSocialPatchCalendarBody(BaseModel):
    milestone: str | None = None
    planned_at: str | None = None
    status: SocialCalendarStatus | None = None
    notes: str | None = None
