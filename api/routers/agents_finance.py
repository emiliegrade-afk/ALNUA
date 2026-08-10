"""Finance — controller and accounting agent routes."""

from __future__ import annotations

from api.route_common import *  # noqa: F403
from api.routers.agents_pole_helpers import clean_agent_text

router = APIRouter()


@router.post("/agents/controller/costs")
def controller_costs(body: ControllerCostsRequest) -> dict[str, Any]:
    return ControllerAgent().analyze_costs(body.period, body.costs_data, body.budget)


@router.post("/agents/controller/forecast")
def controller_forecast(body: ControllerForecastRequest) -> dict[str, Any]:
    return ControllerAgent().build_forecast(
        body.project, body.horizon_months, clean_agent_text(body.assumptions), body.historical_data
    )


@router.post("/agents/controller/llm-alert")
def controller_llm_alert(body: ControllerLLMAlertRequest) -> dict[str, Any]:
    return ControllerAgent().llm_cost_alert(body.daily_spend, body.monthly_budget)


@router.post("/agents/controller/monthly-report")
def controller_monthly_report(body: ControllerMonthlyReportRequest) -> dict[str, Any]:
    return ControllerAgent().monthly_report(body.month, body.all_data)


@router.post("/agents/accounting/advice")
def accounting_advice(body: AccountingAdviceRequest) -> dict[str, Any]:
    return AccountantAgent().financial_advice(
        body.month, body.financial_summary, clean_agent_text(body.question)
    )


@router.get("/agents/accounting/invoices")
def accounting_list_invoices(
    status: str | None = Query(default="to_pay"),
) -> dict[str, Any]:
    """Factures suivies par Jules — lecture seule (paiement hors Hub)."""
    return AccountantAgent().list_open_invoices(status=status or "to_pay")
