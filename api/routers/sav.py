"""SAV lite API — Nadia drafts, CEO validates."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

from typing import Any

from pydantic import BaseModel, Field

router = APIRouter(prefix="/sav", tags=["sav"])


class SavCaseCreateRequest(BaseModel):
    product_slug: str = Field(..., min_length=1, max_length=64)
    subject: str = Field(..., min_length=1, max_length=300)
    body: str = Field(..., min_length=1, max_length=8000)
    channel: str = "manual"
    customer_ref: str = ""


class SavApproveRequest(BaseModel):
    final_reply: str | None = None


@router.get("/kb")
def sav_list_kb() -> dict[str, Any]:
    from services.product_kb import list_kb

    items = list_kb()
    return {"items": [k.model_dump() for k in items]}


@router.post("/kb/sync")
def sav_sync_kb(*, only_prod_beta: bool = False) -> dict[str, Any]:
    from services.product_kb import sync_kb_from_registry

    return sync_kb_from_registry(only_prod_beta=only_prod_beta)


@router.get("/cases")
def sav_list_cases(
    product_slug: str | None = None,
    status: str | None = None,
    needs_ceo: bool | None = None,
    limit: int = 30,
) -> dict[str, Any]:
    from services.sav_lite import list_sav_cases

    return {
        "cases": list_sav_cases(
            product_slug=product_slug,
            status=status,
            needs_ceo=needs_ceo,
            limit=min(limit, 100),
        )
    }


@router.post("/cases")
def sav_create_case(body: SavCaseCreateRequest) -> dict[str, Any]:
    from services.sav_lite import SavCaseIn, process_sav_case

    return process_sav_case(SavCaseIn(**body.model_dump()))


@router.post("/cases/{case_id}/approve")
def sav_approve_case(case_id: str, body: SavApproveRequest) -> dict[str, Any]:
    from services.sav_lite import approve_and_close

    return approve_and_close(case_id, final_reply=body.final_reply)


@router.post("/workflow/run")
def sav_run_workflow() -> dict[str, Any]:
    """Run sav_lite recipe (KB sync + beta ingest + CEO pending summary)."""
    from services.workflow_engine import run_workflow

    return run_workflow("sav_lite", {})
