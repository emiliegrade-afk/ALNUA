"""R&D Dossier Hub — API request body Pydantic models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from services.rnd_schemas_literals import (
    CeoStatus,
    CouncilSessionKind,
    DossierStatus,
    IncubatorStage,
    SocialCalendarStatus,
)
from services.rnd_schemas_models import RndDossierOut, RndIdeaOut


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


class RndIncubatorStageBody(BaseModel):
    """Incubateur (Phase 24, ROADMAP.md) — glisser une carte Kanban vers une
    colonne intermédiaire. `departement` est refusé ici : ce passage a de
    vraies conséquences (dispatch), voir POST .../incubator/promote-to-department."""

    stage: IncubatorStage


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


class RndCouncilStartBody(BaseModel):
    kind: CouncilSessionKind = "strategic"
    topic: str = ""
    idea_id: str | None = None


class RndCouncilMessageBody(BaseModel):
    message: str


class RndCouncilStructuredInput(BaseModel):
    budget_eur: float | None = None
    team_size: int | None = None
    timeframe_weeks: int | None = None
    product_type: str = ""


class RndCouncilEvaluateBody(BaseModel):
    topic: str
    structured_input: RndCouncilStructuredInput
    idea_id: str | None = None
