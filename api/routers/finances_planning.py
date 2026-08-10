"""Finances router — budgets, fiscal obligations, forecast."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter()


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
