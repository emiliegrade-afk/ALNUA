"""Auto-split from api/main.py — agents_pole routes."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter()


@router.post("/agents/secretary/draft-email")
def secretary_draft_email(body: SecretaryDraftEmailRequest) -> dict[str, Any]:
    return SecretaryAgent().draft_email(
        body.subject, body.context, body.recipient, body.tone, body.language
    )


@router.post("/agents/secretary/triage-emails")
def secretary_triage_emails(body: SecretaryTriageRequest) -> dict[str, Any]:
    return SecretaryAgent().triage_emails(body.emails)


@router.post("/agents/secretary/draft-contract")
def secretary_draft_contract(body: SecretaryDraftContractRequest) -> dict[str, Any]:
    return SecretaryAgent().draft_contract(
        body.contract_type, body.party_name, body.scope,
        body.duration, body.compensation, body.special_clauses,
    )


@router.post("/agents/secretary/plan-meeting")
def secretary_plan_meeting(body: SecretaryPlanMeetingRequest) -> dict[str, Any]:
    return SecretaryAgent().plan_meeting(
        body.participants, body.topic, body.duration_minutes, body.constraints
    )


@router.post("/agents/secretary/meeting-notes")
def secretary_meeting_notes(body: SecretaryMeetingNotesRequest) -> dict[str, Any]:
    return SecretaryAgent().write_meeting_notes(
        body.meeting_title, body.raw_notes, body.participants
    )


@router.post("/agents/dev-backend/design-api")
def dev_backend_design_api(body: DevBackendDesignAPIRequest) -> dict[str, Any]:
    return DevBackendAgent().design_api(body.feature, body.project, body.constraints)


@router.post("/agents/dev-backend/implement")
def dev_backend_implement(body: DevBackendImplementRequest) -> dict[str, str]:
    result = DevBackendAgent().implement_feature(
        body.feature, body.project, body.api_spec, body.tech_stack
    )
    return {"result": result}


@router.post("/agents/dev-backend/review")
def dev_backend_review(body: DevBackendReviewRequest) -> dict[str, Any]:
    return DevBackendAgent().review_code(body.code, body.context)


@router.post("/agents/dev-backend/debug")
def dev_backend_debug(body: DevBackendDebugRequest) -> dict[str, Any]:
    return DevBackendAgent().debug(body.error, body.context, body.code_snippet)


@router.post("/agents/level-designer/quest")
def level_designer_quest(body: LevelDesignerQuestRequest) -> dict[str, Any]:
    return LevelDesignerAgent().design_quest(
        body.quest_name, body.game, body.lore_context,
        body.player_level_range, body.quest_type,
    )


@router.post("/agents/level-designer/level")
def level_designer_level(body: LevelDesignerLevelRequest) -> dict[str, Any]:
    return LevelDesignerAgent().design_level(
        body.level_name, body.game, body.biome,
        body.difficulty, body.special_mechanics,
    )


@router.post("/agents/level-designer/lore")
def level_designer_lore(body: LevelDesignerLoreRequest) -> dict[str, Any]:
    return LevelDesignerAgent().write_lore_entry(
        body.subject, body.game, body.lore_type, body.length
    )


@router.post("/agents/level-designer/balance")
def level_designer_balance(body: LevelDesignerBalanceRequest) -> dict[str, Any]:
    return LevelDesignerAgent().balance_review(
        body.system, body.current_values, body.player_feedback
    )


@router.post("/agents/dev-app/instruction")
def dev_app_instruction(body: AgentInstructionRequest) -> dict[str, str]:
    result = DevAppAgent().handle_instruction(body.instruction)
    return {"result": result}


@router.get("/agents/dev-app/issues")
def dev_app_list_issues() -> dict[str, Any]:
    from skills.skill_gh_issues import list_ready_issues

    issues = list_ready_issues()
    return {"issues": issues}


@router.post("/agents/dev-gaming/instruction")
def dev_gaming_instruction(body: AgentInstructionRequest) -> dict[str, str]:
    result = DevGamingAgent().handle_instruction(body.instruction)
    return {"result": result}


@router.post("/agents/marketing/instruction")
def marketing_instruction(body: AgentInstructionRequest) -> dict[str, str]:
    result = MarketingAgent().handle_instruction(body.instruction)
    return {"result": result}


@router.post("/agents/marketing/seo-audit")
def marketing_seo_audit(body: MarketingSeoRequest) -> dict[str, str]:
    from skills.skill_seo_audit import run_seo_audit

    return {"result": run_seo_audit(body.url)}


@router.post("/agents/marketing/content")
def marketing_create_content(body: MarketingContentRequest) -> dict[str, str]:
    instruction = (
        f"Génère du contenu {body.type} pour {body.project} sur le sujet : {body.topic}. "
        f"Ton : {body.tone}. Longueur : {body.length}."
    )
    result = MarketingAgent().handle_instruction(instruction)
    return {"result": result}


@router.post("/agents/hardware/instruction")
def hardware_instruction(body: AgentInstructionRequest) -> dict[str, str]:
    result = HardwareAgent().handle_instruction(body.instruction)
    return {"result": result}


@router.post("/agents/embedded/instruction")
def embedded_instruction(body: AgentInstructionRequest) -> dict[str, str]:
    result = EmbeddedDevAgent().handle_instruction(body.instruction)
    return {"result": result}


@router.post("/agents/embedded/pi-command")
def embedded_pi_command(body: EmbeddedPiCommandRequest) -> dict[str, Any]:
    from agents.embedded_dev_agent import execute_pi_ssh_with_retry

    result = execute_pi_ssh_with_retry(body.command)
    return result


@router.get("/bom/eve")
def bom_eve_list() -> dict[str, Any]:
    items = list_bom_items()
    return {"items": items, "totals": bom_totals(items), "categories": list(BOM_CATEGORIES)}


@router.post("/bom/eve")
def bom_eve_create(body: BomCreateRequest) -> dict[str, Any]:
    try:
        return create_bom_item(body.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/bom/eve/{item_id}")
def bom_eve_update(item_id: str, body: BomUpdateRequest) -> dict[str, Any]:
    try:
        return update_bom_item(item_id, body.model_dump(exclude_unset=True))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/bom/eve/{item_id}")
def bom_eve_delete(item_id: str) -> dict[str, Any]:
    return delete_bom_item(item_id)


@router.get("/looking-glass/status")
def looking_glass_status() -> dict[str, Any]:
    """Check HoloPlay / Looking Glass availability via Pi SSH or local host."""
    import os

    host = os.getenv("LOOKING_GLASS_HOST", "").strip()
    if host:
        try:
            import httpx

            with httpx.Client(timeout=5.0) as client:
                res = client.get(f"{host.rstrip('/')}/health")
                if res.is_success:
                    return {
                        "connected": True,
                        "holoplay_running": True,
                        "message": "Looking Glass host reachable",
                    }
        except Exception:
            pass

    from skills.skill_pi_ssh import pi_is_configured, run_pi_command

    if pi_is_configured():
        try:
            out = run_pi_command("pgrep -f holoplay || pgrep -f LookingGlass")
            running = out.get("success") and bool(out.get("output", "").strip())
            return {
                "connected": True,
                "holoplay_running": running,
                "message": "HoloPlay actif sur Pi" if running else "Pi online, HoloPlay inactif",
            }
        except Exception:
            return {
                "connected": False,
                "holoplay_running": False,
                "message": "Pi configuré mais injoignable",
            }

    return {
        "connected": False,
        "holoplay_running": False,
        "message": "Configurer LOOKING_GLASS_HOST ou PI_HOST dans .env",
    }


@router.post("/reviews/sync")
def reviews_sync(body: ReviewsSyncRequest) -> dict[str, Any]:
    bot = ReviewsBot()
    if body.project_id:
        ingested = bot.sync_project(body.project_id)
        return {"ingested": ingested}
    return bot.run_cycle()


@router.post("/bots/publisher/run")
def publisher_run_cycle() -> dict[str, Any]:
    return PublisherBot().run_cycle()


@router.post("/bots/analytics/run")
def analytics_run_cycle() -> dict[str, Any]:
    result = AnalyticsBot().run_cycle()
    return {"metrics_recorded": result.get("recorded", 0), **result}


@router.post("/agents/controller/costs")
def controller_costs(body: ControllerCostsRequest) -> dict[str, Any]:
    return ControllerAgent().analyze_costs(body.period, body.costs_data, body.budget)


@router.post("/agents/controller/forecast")
def controller_forecast(body: ControllerForecastRequest) -> dict[str, Any]:
    return ControllerAgent().build_forecast(
        body.project, body.horizon_months, body.assumptions, body.historical_data
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
        body.month, body.financial_summary, body.question
    )


@router.post("/agents/analyst-business/market")
def analyst_business_market(body: BusinessAnalystMarketRequest) -> dict[str, Any]:
    return BusinessAnalystAgent().market_analysis(body.product, body.market, body.competitors)


@router.post("/agents/analyst-business/kpis")
def analyst_business_kpis(body: BusinessAnalystKPIsRequest) -> dict[str, Any]:
    return BusinessAnalystAgent().define_kpis(body.project, body.stage, body.business_goal)


@router.post("/agents/analyst-business/user-research")
def analyst_business_user_research(body: BusinessAnalystUserResearchRequest) -> dict[str, Any]:
    return BusinessAnalystAgent().user_research(
        body.product, body.research_question, body.user_segment
    )


@router.post("/agents/analyst-business/brief")
def analyst_business_brief(body: BusinessAnalystBriefRequest) -> dict[str, Any]:
    return BusinessAnalystAgent().strategic_brief(
        body.topic, body.context, body.decision_needed
    )


@router.post("/agents/analyst-data/sql")
def analyst_data_sql(body: DataAnalystSQLRequest) -> dict[str, Any]:
    return DataAnalystAgent().sql_query(body.question, body.schema_context, body.db_type)


@router.post("/agents/analyst-data/funnel")
def analyst_data_funnel(body: DataAnalystFunnelRequest) -> dict[str, Any]:
    return DataAnalystAgent().funnel_analysis(body.funnel_name, body.steps, body.data)


@router.post("/agents/analyst-data/anomaly")
def analyst_data_anomaly(body: DataAnalystAnomalyRequest) -> dict[str, Any]:
    return DataAnalystAgent().anomaly_report(
        body.metric, body.recent_values, body.baseline, body.period
    )


@router.post("/agents/analyst-data/dashboard-spec")
def analyst_data_dashboard(body: DataAnalystDashboardRequest) -> dict[str, Any]:
    return DataAnalystAgent().dashboard_spec(
        body.dashboard_name, body.audience, body.kpis, body.data_sources
    )


