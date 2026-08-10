"""Auto-split from api/main.py — finances routes."""

from __future__ import annotations

from api.route_common import *  # noqa: F403
from api.routers.finances_planning import router as finances_planning_router

router = APIRouter()
router.include_router(finances_planning_router)


def _finance_tx_row(body: FinanceTransactionCreate) -> dict[str, Any]:
    return {
        "date": body.tx_date.isoformat(),
        "type": body.type,
        "amount": body.amount,
        "currency": body.currency,
        "category": body.category,
        "project_id": body.project_id,
        "campaign_id": body.campaign_id,
        "description": body.description,
        "is_recurring": body.is_recurring,
        "recurrence": body.recurrence if body.is_recurring else None,
    }


@router.get("/finances/transactions")
def list_finance_transactions(
    month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
    type: str | None = Query(default=None, pattern="^(income|expense)$"),
    category: str | None = None,
    project_id: str | None = None,
) -> list[dict[str, Any]]:
    db = get_supabase()
    rows = fetch_finance_transactions(
        db,
        month=month,
        tx_type=type,
        category=category,
        project_id=project_id,
    )
    return attach_project_names(db, rows)


@router.post("/finances/transactions")
def create_finance_transaction(body: FinanceTransactionCreate) -> dict[str, Any]:
    db = get_supabase()
    return db.insert("transactions", _finance_tx_row(body))


@router.patch("/finances/transactions/{transaction_id}")
def update_finance_transaction(
    transaction_id: str,
    body: FinanceTransactionUpdate,
) -> dict[str, Any]:
    db = get_supabase()
    rows = db.select("transactions", filters={"id": transaction_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Transaction introuvable")

    updates = body.model_dump(exclude_unset=True, by_alias=True)
    if "date" in updates and updates["date"] is not None:
        updates["date"] = updates["date"].isoformat()
    if updates.get("is_recurring") is False:
        updates["recurrence"] = None
    if not updates:
        return rows[0]
    return db.update("transactions", transaction_id, updates)


@router.delete("/finances/transactions/{transaction_id}")
def delete_finance_transaction(transaction_id: str) -> dict[str, bool]:
    db = get_supabase()
    rows = db.select("transactions", filters={"id": transaction_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Transaction introuvable")
    db.delete("transactions", transaction_id)
    return {"ok": True}


@router.get("/finances/saas-spend")
def finances_saas_spend(days: int = Query(default=30, ge=1, le=90)) -> dict[str, Any]:
    """Catalogue abonnements + coûts live (OpenRouter, manuel, Revolut si configuré)."""
    from services.saas_spend import build_saas_spend_report

    return build_saas_spend_report(days=days)


@router.get("/finances/invoices")
def list_finance_invoices(
    status: str | None = Query(default=None),
    vendor: str | None = Query(default=None),
) -> dict[str, Any]:
    from services.finance_invoices import invoice_summary, list_invoices

    return {"invoices": list_invoices(status=status, vendor=vendor), "summary": invoice_summary()}


@router.post("/finances/invoices")
def create_finance_invoice(body: FinanceInvoiceCreate) -> dict[str, Any]:
    from services.finance_invoices import create_invoice
    from services.input_sanitizer import sanitize_user_input

    try:
        return create_invoice(
            vendor=sanitize_user_input(body.vendor, max_length=120),
            amount=body.amount,
            currency=body.currency,
            description=sanitize_user_input(body.description or "", max_length=500),
            due_date=body.due_date.isoformat() if body.due_date else None,
            category=body.category,
            receipt_url=body.receipt_url or "",
            external_ref=sanitize_user_input(body.external_ref or "", max_length=120),
            status=body.status,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/finances/invoices/{invoice_id}")
def update_finance_invoice(invoice_id: str, body: FinanceInvoiceUpdate) -> dict[str, Any]:
    from services.finance_invoices import update_invoice
    from services.input_sanitizer import sanitize_user_input

    updates = body.model_dump(exclude_unset=True)
    if "vendor" in updates and updates["vendor"] is not None:
        updates["vendor"] = sanitize_user_input(updates["vendor"], max_length=120)
    if "description" in updates and updates["description"] is not None:
        updates["description"] = sanitize_user_input(updates["description"], max_length=500)
    if "due_date" in updates and updates["due_date"] is not None:
        updates["due_date"] = updates["due_date"].isoformat()
    try:
        return update_invoice(invoice_id, **updates)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Facture introuvable") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/finances/revolut/status")
def revolut_status(days: int = Query(default=30, ge=1, le=90)) -> dict[str, Any]:
    """Statut connecteur Revolut Business (lecture dépenses, jamais paiement)."""
    from services.revolut_business import fetch_expenses_summary, is_configured

    summary = fetch_expenses_summary(days=days)
    return {"configured": is_configured(), **summary}


@router.get("/finances/summary/{month}")
def get_finance_summary(month: str) -> dict[str, Any]:
    try:
        return get_or_generate_summary(month)
    except Exception as exc:
        logger.exception("Finance summary failed for %s", month)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/finances/summary/generate")
def regenerate_finance_summary(body: FinanceSummaryGenerate) -> dict[str, Any]:
    try:
        return generate_monthly_summary(body.month, force=True)
    except Exception as exc:
        logger.exception("Finance summary regeneration failed for %s", body.month)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/finances/dashboard")
def finance_dashboard(
    month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
) -> dict[str, Any]:
    db = get_supabase()
    data = build_dashboard(db, month=month)
    data["recurring_expenses"] = attach_project_names(
        db, data["recurring_expenses"]
    )
    return data
