"""Pydantic models — split from schemas.py (debt paydown)."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

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
