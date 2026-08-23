"""Phase 35 — design system + brand coherence (keep brand.py kit router lean)."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.input_sanitizer import sanitize_user_input

router = APIRouter(tags=["brand-system"])


class BrandReviewRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=8000)
    sector: str = ""
    department: str = ""


@router.get("/brand/design-system")
def brand_design_system() -> dict[str, Any]:
    from services.brand_design_system import get_design_system

    return get_design_system()


@router.post("/brand/review")
def brand_review(body: BrandReviewRequest) -> dict[str, Any]:
    from services.brand_design_system import review_brand_coherence

    return review_brand_coherence(
        sanitize_user_input(body.text, max_length=8000, redact_pii_enabled=False),
        sector=sanitize_user_input(body.sector, max_length=64),
        department=sanitize_user_input(body.department, max_length=64),
    )


class BrandDebateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=8000)
    sector: str = ""
    department: str = ""
    rounds: int = Field(default=1, ge=1, le=2)


@router.post("/brand/debate")
def brand_debate(body: BrandDebateRequest) -> dict[str, Any]:
    """Élise (brand) ↔ Anouk (content_company) — Phase 35 Depth+."""
    from services.brand_voice_debate import debate_brand_voice

    return debate_brand_voice(
        body.text,
        sector=body.sector,
        department=body.department,
        rounds=body.rounds,
    )
