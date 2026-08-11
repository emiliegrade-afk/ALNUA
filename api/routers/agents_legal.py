"""Legal counsel — enterprise lawyer endpoints."""

from __future__ import annotations

from api.route_common import *  # noqa: F403
from services.input_sanitizer import sanitize_user_input

router = APIRouter(tags=["legal"])


class LegalAdviseRequest(BaseModel):
    question: str
    regions: list[str] = Field(default_factory=lambda: ["UE", "USA", "ASIE"])
    context: str = ""


class LegalReviewRequest(BaseModel):
    document_text: str
    doc_kind: str = "contrat"
    regions: list[str] = Field(default_factory=lambda: ["UE", "USA", "ASIE"])


@router.post("/agents/legal-counsel/advise")
def legal_advise(body: LegalAdviseRequest) -> dict[str, Any]:
    q = sanitize_user_input(body.question, max_length=4000, redact_pii_enabled=False)
    ctx = sanitize_user_input(body.context or "", max_length=3000, redact_pii_enabled=False)
    return LegalCounselAgent().advise(q, regions=body.regions, context=ctx)


@router.post("/agents/legal-counsel/review")
def legal_review(body: LegalReviewRequest) -> dict[str, Any]:
    doc = sanitize_user_input(body.document_text, max_length=12000, redact_pii_enabled=False)
    return LegalCounselAgent().review_document(
        doc, doc_kind=body.doc_kind or "contrat", regions=body.regions
    )


@router.post("/agents/legal-counsel/validate-before-sign")
def legal_validate(body: LegalReviewRequest) -> dict[str, Any]:
    doc = sanitize_user_input(body.document_text, max_length=12000, redact_pii_enabled=False)
    return LegalCounselAgent().validate_before_sign(doc, regions=body.regions)


@router.get("/agents/legal-counsel/templates")
def legal_list_templates() -> dict[str, Any]:
    from config.contract_templates_registry import list_contract_templates

    return {"templates": list_contract_templates()}
