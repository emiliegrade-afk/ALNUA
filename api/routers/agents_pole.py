"""Auto-split from api/main.py — agents_pole routes."""

from __future__ import annotations

from api.route_common import *  # noqa: F403
from services.input_sanitizer import sanitize_user_input

router = APIRouter()


def _clean(text: str, *, max_length: int = 6000) -> str:
    """Bound + strip prompt-injection patterns from free text headed for an LLM.

    PII redaction stays off here: these endpoints routinely carry real business
    data (client emails, phone numbers in contracts) that must reach the agent
    intact — unlike the Telegram chat surface, which redacts by default.
    """
    return sanitize_user_input(text, max_length=max_length, redact_pii_enabled=False)


@router.post("/agents/secretary/draft-email")
def secretary_draft_email(body: SecretaryDraftEmailRequest) -> dict[str, Any]:
    return SecretaryAgent().draft_email(
        body.subject, _clean(body.context), body.recipient, body.tone, body.language
    )


@router.post("/agents/secretary/triage-emails")
def secretary_triage_emails(body: SecretaryTriageRequest) -> dict[str, Any]:
    emails = [
        {**e, "body": _clean(e.get("body", "")), "subject": _clean(e.get("subject", ""), max_length=500)}
        for e in body.emails
    ]
    return SecretaryAgent().triage_emails(emails)


@router.post("/agents/secretary/draft-contract")
def secretary_draft_contract(body: SecretaryDraftContractRequest) -> dict[str, Any]:
    return SecretaryAgent().draft_contract(
        body.contract_type, body.party_name, _clean(body.scope),
        body.duration, body.compensation, _clean(body.special_clauses),
    )


@router.post("/agents/secretary/plan-meeting")
def secretary_plan_meeting(body: SecretaryPlanMeetingRequest) -> dict[str, Any]:
    return SecretaryAgent().plan_meeting(
        body.participants, _clean(body.topic, max_length=500), body.duration_minutes, _clean(body.constraints)
    )


@router.post("/agents/secretary/meeting-notes")
def secretary_meeting_notes(body: SecretaryMeetingNotesRequest) -> dict[str, Any]:
    return SecretaryAgent().write_meeting_notes(
        body.meeting_title, _clean(body.raw_notes), body.participants
    )


@router.get("/agents/secretary/milestones")
def secretary_list_milestones(days_ahead: int = 120) -> dict[str, Any]:
    from services.milestones import list_upcoming_milestones

    return {"milestones": list_upcoming_milestones(days_ahead=days_ahead)}


@router.post("/agents/secretary/milestones")
def secretary_create_milestone(body: MilestoneCreateRequest) -> dict[str, Any]:
    from services.milestones import create_milestone

    return create_milestone(
        _clean(body.title, max_length=200),
        body.date_iso,
        pole=body.pole,
        description=_clean(body.description),
    )


@router.patch("/agents/secretary/milestones/{event_id}")
def secretary_update_milestone(event_id: str, body: MilestoneUpdateRequest) -> dict[str, Any]:
    from services.milestones import update_milestone

    return update_milestone(
        event_id,
        title=_clean(body.title, max_length=200) if body.title is not None else None,
        date_iso=body.date_iso,
        pole=body.pole,
        description=_clean(body.description) if body.description is not None else None,
    )


@router.post("/agents/secretary/milestones/{event_id}/validate")
def secretary_validate_milestone(event_id: str, body: MilestoneValidateRequest) -> dict[str, Any]:
    from services.milestones import set_milestone_validated

    return set_milestone_validated(event_id, body.validated)


@router.post("/agents/dev-backend/design-api")
def dev_backend_design_api(body: DevBackendDesignAPIRequest) -> dict[str, Any]:
    return DevBackendAgent().design_api(_clean(body.feature), body.project, _clean(body.constraints))


@router.post("/agents/dev-backend/implement")
def dev_backend_implement(body: DevBackendImplementRequest) -> dict[str, str]:
    result = DevBackendAgent().implement_feature(
        _clean(body.feature), body.project, _clean(body.api_spec, max_length=12000), body.tech_stack
    )
    return {"result": result}


@router.post("/agents/dev-backend/review")
def dev_backend_review(body: DevBackendReviewRequest) -> dict[str, Any]:
    return DevBackendAgent().review_code(_clean(body.code, max_length=12000), _clean(body.context))


@router.post("/agents/dev-backend/debug")
def dev_backend_debug(body: DevBackendDebugRequest) -> dict[str, Any]:
    return DevBackendAgent().debug(
        _clean(body.error), _clean(body.context), _clean(body.code_snippet, max_length=12000)
    )


@router.post("/agents/level-designer/quest")
def level_designer_quest(body: LevelDesignerQuestRequest) -> dict[str, Any]:
    return LevelDesignerAgent().design_quest(
        body.quest_name, body.game, _clean(body.lore_context),
        body.player_level_range, body.quest_type,
    )


@router.post("/agents/level-designer/level")
def level_designer_level(body: LevelDesignerLevelRequest) -> dict[str, Any]:
    return LevelDesignerAgent().design_level(
        body.level_name, body.game, body.biome,
        body.difficulty, _clean(body.special_mechanics),
    )


@router.post("/agents/level-designer/lore")
def level_designer_lore(body: LevelDesignerLoreRequest) -> dict[str, Any]:
    return LevelDesignerAgent().write_lore_entry(
        _clean(body.subject, max_length=500), body.game, body.lore_type, body.length
    )


@router.post("/agents/level-designer/balance")
def level_designer_balance(body: LevelDesignerBalanceRequest) -> dict[str, Any]:
    return LevelDesignerAgent().balance_review(
        body.system, body.current_values, _clean(body.player_feedback)
    )


@router.post("/agents/ai-programmer/behavior")
def ai_programmer_behavior(body: AiProgrammerBehaviorRequest) -> dict[str, Any]:
    return AiProgrammerAgent().design_behavior(
        body.entity_name, body.game, body.behavior_type, body.difficulty
    )


@router.post("/agents/ai-programmer/nwiro-probe")
def ai_programmer_nwiro_probe() -> dict[str, Any]:
    """Phase 21 — Kenji probes Nwiro BT tools (explicit offline if UE5 down)."""
    return AiProgrammerAgent().probe_nwiro_tools()


@router.post("/agents/environment-artist/environment")
def environment_artist_environment(body: EnvironmentArtistRequest) -> dict[str, Any]:
    return EnvironmentArtistAgent().design_environment(
        body.zone_name, body.game, body.biome, _clean(body.mood, max_length=500)
    )


@router.post("/agents/technical-artist/render-budget")
def technical_artist_render_budget(body: TechnicalArtistRenderRequest) -> dict[str, Any]:
    return TechnicalArtistAgent().optimize_render_budget(
        body.scene_name, body.game, body.target_fps, _clean(body.current_issues)
    )


@router.post("/agents/narrative-designer/dialogue")
def narrative_designer_dialogue(body: NarrativeDesignerDialogueRequest) -> dict[str, Any]:
    return NarrativeDesignerAgent().write_dialogue(
        body.npc_name, body.game, _clean(body.context), body.tone
    )


@router.post("/agents/vfx-artist/vfx")
def vfx_artist_vfx(body: VfxArtistRequest) -> dict[str, Any]:
    return VfxArtistAgent().design_vfx(
        body.effect_name, body.game, body.trigger, body.style
    )


@router.post("/agents/sound-designer/soundscape")
def sound_designer_soundscape(body: SoundDesignerRequest) -> dict[str, Any]:
    return SoundDesignerAgent().design_soundscape(
        body.scene_name, body.game, body.mood, _clean(body.key_sfx, max_length=500)
    )


@router.post("/agents/qa-gaming/test-plan")
def qa_gaming_test_plan(body: QaGamingTestPlanRequest) -> dict[str, Any]:
    return QaGamingAgent().build_test_plan(
        body.feature_name, body.game, body.build_version, _clean(body.risk_areas)
    )


@router.post("/agents/vision-ai/detection-pipeline")
def vision_ai_detection_pipeline(body: VisionAiDetectionRequest) -> dict[str, Any]:
    return VisionAiAgent().design_detection_pipeline(
        body.task_name, body.target_objects, _clean(body.constraints)
    )


@router.post("/agents/electronics/circuit")
def electronics_circuit(body: ElectronicsCircuitRequest) -> dict[str, Any]:
    return ElectronicsAgent().design_circuit(
        body.circuit_name, body.function, _clean(body.constraints)
    )


@router.post("/agents/electronics/bom-context")
def electronics_bom_context(body: ElectronicsBomContextRequest) -> dict[str, Any]:
    """Phase 21 — Marco reads Eve BOM via skill_bom (no fabricated lines)."""
    return ElectronicsAgent().bom_context(category=body.category, limit=body.limit)


@router.post("/agents/electronics/alternatives")
def electronics_alternatives(body: EveAlternativesRequest) -> dict[str, Any]:
    """Sourcing expert — pro vs budget options (estimates, no auto-buy)."""
    from services.input_sanitizer import sanitize_user_input

    try:
        return ElectronicsAgent().suggest_alternatives(
            sanitize_user_input(body.need, max_length=400),
            category=sanitize_user_input(body.category or "", max_length=40) or None,
            max_options=body.max_options,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/agents/firmware/driver")
def firmware_driver(body: FirmwareDriverRequest) -> dict[str, Any]:
    return FirmwareAgent().design_driver(
        body.component_name, body.timing_requirement, _clean(body.constraints)
    )


@router.post("/agents/firmware/pi-probe")
def firmware_pi_probe(body: FirmwarePiProbeRequest) -> dict[str, Any]:
    """Phase 21 — Petra probes Eve Pi via SSH (denylist + PI_NOT_CONFIGURED)."""
    from services.input_sanitizer import sanitize_user_input

    cmd = sanitize_user_input(body.command or "uname -a", max_length=200)
    return FirmwareAgent().probe_pi(cmd)


@router.post("/agents/mechanical/part")
def mechanical_part(body: MechanicalPartRequest) -> dict[str, Any]:
    return MechanicalAgent().design_part(
        body.part_name, body.function, _clean(body.load_requirements)
    )


@router.post("/agents/mechanical/assembly-plan")
def mechanical_assembly_plan(body: EveAssemblyPlanRequest) -> dict[str, Any]:
    """Plan de montage Eve — basé sur le BOM courant."""
    from services.input_sanitizer import sanitize_user_input

    return MechanicalAgent().assembly_plan(
        sanitize_user_input(body.goal or "", max_length=500)
    )


@router.post("/agents/industrial-design/form-factor")
def industrial_design_form_factor(body: IndustrialDesignRequest) -> dict[str, Any]:
    return IndustrialDesignAgent().design_form_factor(
        body.product_name, _clean(body.constraints), _clean(body.brand_notes)
    )


@router.post("/agents/qa-robot/protocol")
def qa_robot_protocol(body: QaRobotProtocolRequest) -> dict[str, Any]:
    return QaRobotAgent().build_test_protocol(
        body.subsystem_name, body.risk_level, _clean(body.prior_issues)
    )


@router.post("/agents/safety/risk-assessment")
def safety_risk_assessment(body: SafetyRiskRequest) -> dict[str, Any]:
    return SafetyAgent().assess_risk(
        body.subsystem_name, body.hazard_type, _clean(body.context)
    )


@router.post("/agents/simulation/plan")
def simulation_plan(body: SimulationPlanRequest) -> dict[str, Any]:
    return SimulationAgent().run_simulation_plan(
        body.subsystem_name, body.scenario, _clean(body.constraints)
    )


@router.post("/agents/dev-app/instruction")
def dev_app_instruction(body: AgentInstructionRequest) -> dict[str, str]:
    result = DevAppAgent().handle_instruction(_clean(body.instruction))
    return {"result": result}


@router.get("/agents/dev-app/issues")
def dev_app_list_issues() -> dict[str, Any]:
    from skills.skill_gh_issues import list_ready_issues

    issues = list_ready_issues()
    return {"issues": issues}


@router.post("/agents/dev-gaming/instruction")
def dev_gaming_instruction(body: AgentInstructionRequest) -> dict[str, str]:
    result = DevGamingAgent().handle_instruction(_clean(body.instruction))
    return {"result": result}


@router.post("/agents/marketing/instruction")
def marketing_instruction(body: AgentInstructionRequest) -> dict[str, str]:
    result = MarketingAgent().handle_instruction(_clean(body.instruction))
    return {"result": result}


@router.post("/agents/marketing/seo-audit")
def marketing_seo_audit(body: MarketingSeoRequest) -> dict[str, str]:
    from skills.skill_seo_audit import run_seo_audit

    return {"result": run_seo_audit(body.url)}


@router.post("/agents/marketing/content")
def marketing_create_content(body: MarketingContentRequest) -> dict[str, str]:
    instruction = (
        f"Génère du contenu {body.type} pour {body.project} sur le sujet : {_clean(body.topic, max_length=500)}. "
        f"Ton : {body.tone}. Longueur : {body.length}."
    )
    result = MarketingAgent().handle_instruction(instruction)
    return {"result": result}


@router.post("/agents/ads/create-campaign")
def ads_create_campaign(body: AdsCreateCampaignRequest) -> dict[str, Any]:
    return AdsAgent().create_campaign(
        _clean(body.brief, max_length=2000),
        platform=body.platform,
        budget_usd=body.budget_usd,
        objective=body.objective,
        audience=body.audience,
        project_id=body.project_id,
        name=body.name,
    )


@router.post("/agents/hardware/instruction")
def hardware_instruction(body: AgentInstructionRequest) -> dict[str, str]:
    result = HardwareAgent().handle_instruction(_clean(body.instruction))
    return {"result": result}


@router.post("/agents/hardware/infra-blueprint")
def hardware_infra_blueprint(body: EveInfraBlueprintRequest) -> dict[str, Any]:
    """Qui build le robot vs l'app compagnon (comme Naïa) — Yuki."""
    from services.input_sanitizer import sanitize_user_input

    return HardwareAgent().infra_blueprint(
        sanitize_user_input(body.focus or "full", max_length=80)
    )


@router.get("/robo/pi-bridge")
def robo_pi_bridge_status() -> dict[str, Any]:
    """SSH bridge status — Hub replaces WinSCP for agent commands when PI_HOST set."""
    import os

    from skills.skill_pi_ssh import PI_NOT_CONFIGURED, pi_is_configured

    configured = pi_is_configured()
    return {
        "configured": configured,
        "host": (os.getenv("PI_HOST") or "").strip() or None,
        "tooling": {
            "agents": "POST /agents/embedded/pi-command (denylist + SSH)",
            "human_files": "WinSCP optional for manual file copy; not used by agents",
        },
        "message": (
            "Pi prêt pour commandes agents via Hub."
            if configured
            else PI_NOT_CONFIGURED
        ),
        "pi_deferred_ok": True,
    }


@router.post("/agents/embedded/instruction")
def embedded_instruction(body: AgentInstructionRequest) -> dict[str, str]:
    result = EmbeddedDevAgent().handle_instruction(_clean(body.instruction))
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
        body.project, body.horizon_months, _clean(body.assumptions), body.historical_data
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
        body.month, body.financial_summary, _clean(body.question)
    )


@router.get("/agents/accounting/invoices")
def accounting_list_invoices(
    status: str | None = Query(default="to_pay"),
) -> dict[str, Any]:
    """Factures suivies par Jules — lecture seule (paiement hors Hub)."""
    return AccountantAgent().list_open_invoices(status=status or "to_pay")


@router.post("/agents/analyst-business/market")
def analyst_business_market(body: BusinessAnalystMarketRequest) -> dict[str, Any]:
    return BusinessAnalystAgent().market_analysis(body.product, body.market, body.competitors)


@router.post("/agents/analyst-business/kpis")
def analyst_business_kpis(body: BusinessAnalystKPIsRequest) -> dict[str, Any]:
    return BusinessAnalystAgent().define_kpis(body.project, body.stage, _clean(body.business_goal))


@router.post("/agents/analyst-business/user-research")
def analyst_business_user_research(body: BusinessAnalystUserResearchRequest) -> dict[str, Any]:
    return BusinessAnalystAgent().user_research(
        body.product, _clean(body.research_question), body.user_segment
    )


@router.post("/agents/analyst-business/brief")
def analyst_business_brief(body: BusinessAnalystBriefRequest) -> dict[str, Any]:
    return BusinessAnalystAgent().strategic_brief(
        _clean(body.topic, max_length=500), _clean(body.context), _clean(body.decision_needed)
    )


@router.post("/agents/analyst-data/sql")
def analyst_data_sql(body: DataAnalystSQLRequest) -> dict[str, Any]:
    return DataAnalystAgent().sql_query(_clean(body.question), _clean(body.schema_context, max_length=8000), body.db_type)


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


