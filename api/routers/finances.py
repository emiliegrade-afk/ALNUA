"""Auto-split from api/main.py — finances routes."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter()


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


@router.get("/finances/budgets")
def list_finance_budgets(
    department: str | None = Query(default=None),
    period: str | None = Query(default=None),
) -> dict[str, Any]:
    from services.finance_budgets import budget_summary, list_budgets

    return {
        "budgets": list_budgets(department=department, period=period),
        "summary": budget_summary(),
    }


@router.post("/finances/budgets")
def create_finance_budget(body: FinanceBudgetCreate) -> dict[str, Any]:
    from services.finance_budgets import create_budget
    from services.input_sanitizer import sanitize_user_input

    try:
        return create_budget(
            department=sanitize_user_input(body.department, max_length=40),
            period=sanitize_user_input(body.period, max_length=20),
            amount=body.amount,
            currency=body.currency,
            label=sanitize_user_input(body.label or "", max_length=120),
            notes=sanitize_user_input(body.notes or "", max_length=500),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/finances/budgets/{budget_id}")
def update_finance_budget(budget_id: str, body: FinanceBudgetUpdate) -> dict[str, Any]:
    from services.finance_budgets import update_budget
    from services.input_sanitizer import sanitize_user_input

    updates = body.model_dump(exclude_unset=True)
    for key in ("department", "period", "label", "notes"):
        if key in updates and updates[key] is not None:
            updates[key] = sanitize_user_input(str(updates[key]), max_length=200)
    try:
        return update_budget(budget_id, **updates)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Budget introuvable") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/finances/fiscal-obligations")
def list_fiscal_obligations(
    status: str | None = Query(default=None),
    kind: str | None = Query(default=None),
) -> dict[str, Any]:
    from services.finance_fiscal import fiscal_summary, list_obligations

    return {
        "obligations": list_obligations(status=status, kind=kind),
        "summary": fiscal_summary(),
    }


@router.post("/finances/fiscal-obligations")
def create_fiscal_obligation(body: FinanceFiscalCreate) -> dict[str, Any]:
    from services.finance_fiscal import create_obligation
    from services.input_sanitizer import sanitize_user_input

    try:
        return create_obligation(
            title=sanitize_user_input(body.title, max_length=200),
            amount=body.amount,
            due_date=body.due_date.isoformat() if body.due_date else None,
            kind=sanitize_user_input(body.kind, max_length=40),
            currency=body.currency,
            notes=sanitize_user_input(body.notes or "", max_length=500),
            status=body.status,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/finances/fiscal-obligations/{obligation_id}")
def update_fiscal_obligation(
    obligation_id: str,
    body: FinanceFiscalUpdate,
) -> dict[str, Any]:
    from services.finance_fiscal import update_obligation
    from services.input_sanitizer import sanitize_user_input

    updates = body.model_dump(exclude_unset=True)
    if "due_date" in updates and updates["due_date"] is not None:
        updates["due_date"] = updates["due_date"].isoformat()
    for key in ("title", "kind", "notes"):
        if key in updates and updates[key] is not None:
            updates[key] = sanitize_user_input(str(updates[key]), max_length=200)
    try:
        return update_obligation(obligation_id, **updates)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Obligation introuvable") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/finances/cockpit-forecast")
def finances_cockpit_forecast(
    period: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
    horizon_months: int = Query(default=6, ge=1, le=24),
) -> dict[str, Any]:
    """Vague C — deterministic forecast from budgets + fiscal + SaaS (no auto-pay)."""
    from services.finance_cockpit_forecast import build_cockpit_forecast

    return build_cockpit_forecast(period=period, horizon_months=horizon_months)


@router.post("/finances/forecast/llm")
def finances_forecast_llm(body: dict[str, Any]) -> dict[str, Any]:
    """Vague C — Rémi LLM forecast, prefilled from cockpit ledgers when possible."""
    from agents.controller_agent import ControllerAgent
    from services.finance_cockpit_forecast import build_cockpit_forecast
    from services.input_sanitizer import sanitize_user_input

    period = sanitize_user_input(str(body.get("period") or ""), max_length=10) or None
    horizon = int(body.get("horizon_months") or 6)
    cockpit = build_cockpit_forecast(period=period, horizon_months=horizon)
    project = sanitize_user_input(str(body.get("project") or "ALNUA global"), max_length=120)
    assumptions = sanitize_user_input(
        str(body.get("assumptions") or cockpit.get("assumptions_for_llm") or ""),
        max_length=4000,
    )
    historical = body.get("historical_data")
    if not isinstance(historical, dict):
        historical = {
            "cockpit": cockpit,
            "period_remaining": cockpit["budgets"]["period_remaining"],
            "monthly_burn_estimate": cockpit["projection"]["monthly_burn_estimate"],
        }
    result = ControllerAgent().build_forecast(
        project=project,
        horizon_months=horizon,
        assumptions=assumptions,
        historical_data=historical,
    )
    return {"ok": True, "cockpit": cockpit, "llm_forecast": result}
