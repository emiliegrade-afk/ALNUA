"""Advanced services — Cost Monitor (peeled from advanced_services.py)."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter(prefix="/services", tags=["advanced-services"])


class CostAlertRequest(BaseModel):
    daily_budget_usd: float = Field(default=5.0, gt=0)
    agent_id: str | None = None


@router.get("/costs/report")
def costs_report(
    agent_id: str | None = None,
    days: int = Query(default=7, ge=1, le=30),
    model: str | None = None,
) -> dict[str, Any]:
    """
    Rapport de coûts LLM par agent sur N jours.
    Rémi (controller) utilise ce rapport pour le suivi budgétaire.
    """
    from services.cost_monitor import get_cost_report
    return get_cost_report(agent_id=agent_id, days=days, model=model)


@router.get("/costs/monthly")
def costs_monthly(month: str | None = None) -> dict[str, Any]:
    """
    Résumé mensuel pour Jules (accounting). Format month: '2026-06'.
    """
    from services.cost_monitor import get_monthly_summary
    return get_monthly_summary(month=month)


@router.get("/costs/alert")
def costs_alert(
    daily_budget_usd: float = 5.0,
    agent_id: str | None = None,
) -> dict[str, Any]:
    """Vérifie si le budget journalier est dépassé. Severity: ok | warning | critical."""
    from services.cost_monitor import check_budget_alert
    return check_budget_alert(daily_budget_usd=daily_budget_usd, agent_id=agent_id)


@router.get("/costs/top")
def costs_top(limit: int = 10, days: int = 7) -> list[dict[str, Any]]:
    """Top N appels LLM les plus coûteux."""
    from services.cost_monitor import get_top_costs
    return get_top_costs(limit=limit, days=days)


@router.post("/costs/record")
def costs_record(
    agent_id: str = "",
    model: str = "",
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    method: str = "",
) -> dict[str, Any]:
    """Enregistre manuellement un appel LLM (normalement auto via LLMClient)."""
    from services.cost_monitor import record_call
    cost = record_call(agent_id, model, prompt_tokens, completion_tokens, method)
    return {"recorded": True, "cost_usd": cost}


class ManualCostRequest(BaseModel):
    source: str
    amount_usd: float = Field(gt=0)
    period: str | None = None
    note: str = ""


class ElevenLabsPlanCostRequest(BaseModel):
    usd_per_month: float = Field(gt=0)


@router.get("/costs/elevenlabs")
def costs_elevenlabs() -> dict[str, Any]:
    """Usage/quota ElevenLabs en temps réel (personnages utilisés, reset, coût estimé si le
    plan mensuel a été renseigné)."""
    from services.elevenlabs_monitor import get_elevenlabs_report
    return get_elevenlabs_report()


@router.post("/costs/elevenlabs/plan-cost")
def costs_elevenlabs_set_plan(body: ElevenLabsPlanCostRequest) -> dict[str, Any]:
    """Renseigne le prix mensuel du plan ElevenLabs — seul moyen d'obtenir une estimation
    en USD, l'API ElevenLabs n'expose pas de prix."""
    from services.elevenlabs_monitor import set_monthly_plan_cost
    set_monthly_plan_cost(body.usd_per_month)
    return {"success": True, "monthly_plan_cost_usd": body.usd_per_month}


@router.get("/costs/manual")
def costs_manual_report(months: int = 3) -> dict[str, Any]:
    """Coûts saisis manuellement (hébergeur, domaine...) sur N mois."""
    from services.manual_costs import get_manual_costs_report
    return get_manual_costs_report(months=months)


@router.post("/costs/manual")
def costs_manual_record(body: ManualCostRequest) -> dict[str, Any]:
    from services.manual_costs import record_manual_cost
    return record_manual_cost(body.source, body.amount_usd, period=body.period, note=body.note)


@router.delete("/costs/manual/{entry_id}")
def costs_manual_delete(entry_id: str) -> dict[str, Any]:
    from services.manual_costs import delete_manual_cost
    return {"deleted": delete_manual_cost(entry_id)}


@router.get("/costs/combined")
def costs_combined(days: int = 30) -> dict[str, Any]:
    """Vue Jules/Rémi : LLM (OpenRouter) + ElevenLabs + hébergeur/manuel réunis."""
    from services.cost_monitor import get_cost_report
    from services.elevenlabs_monitor import get_elevenlabs_report
    from services.manual_costs import get_manual_costs_report

    llm = get_cost_report(days=days)
    eleven = get_elevenlabs_report()
    manual = get_manual_costs_report(months=max(1, days // 30))

    total = llm.get("total_cost_usd", 0.0)
    if eleven.get("estimated_cost_this_period_usd"):
        total += eleven["estimated_cost_this_period_usd"]
    total += manual.get("total_usd", 0.0)

    return {
        "period_days": days,
        "llm": llm,
        "elevenlabs": eleven,
        "manual": manual,
        "total_usd_estimate": round(total, 2),
    }
