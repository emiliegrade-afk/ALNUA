"""Advanced services router — LLM Router, Adversarial Spec, Parallel Runner, Content Pipeline."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter(prefix="/services", tags=["advanced-services"])


# ---------------------------------------------------------------------------
# LLM Router (NadirClaw-inspired)
# ---------------------------------------------------------------------------

class LLMRouterRequest(BaseModel):
    agent_id: str
    prompt: str
    method_name: str = ""
    force_tier: str | None = None


class LLMRouterReportRequest(BaseModel):
    agent_id: str
    prompt: str
    method_name: str = ""


@router.post("/llm-router/route")
def llm_router_route(body: LLMRouterRequest) -> dict[str, Any]:
    """Retourne le model slug optimal pour un appel donné."""
    from services.llm_router import route_to_model
    model = route_to_model(body.agent_id, body.prompt, body.method_name, body.force_tier)
    return {"agent_id": body.agent_id, "routed_model": model}


@router.post("/llm-router/report")
def llm_router_report(body: LLMRouterReportRequest) -> dict[str, Any]:
    """Rapport complet de décision de routage (debug / audit Rémi)."""
    from services.llm_router import routing_report
    return routing_report(body.agent_id, body.prompt, body.method_name)


@router.post("/llm-router/complexity")
def llm_router_complexity(body: LLMRouterReportRequest) -> dict[str, Any]:
    """Score de complexité seul (0-10)."""
    from services.llm_router import complexity_score
    score = complexity_score(body.prompt, body.method_name)
    return {
        "prompt_chars": len(body.prompt),
        "method": body.method_name,
        "complexity_score": score,
        "tier_suggestion": "premium" if score >= 7 else "standard" if score >= 4 else "fast",
    }


# ---------------------------------------------------------------------------
# Adversarial Spec (adversarial-spec-inspired)
# ---------------------------------------------------------------------------

class AdversarialSpecRequest(BaseModel):
    spec_text: str
    context: str = ""
    rounds: int = Field(default=2, ge=1, le=3)
    stop_on_approve: bool = True


class QuickCheckRequest(BaseModel):
    spec_text: str
    context: str = ""


@router.post("/adversarial-spec/debate")
def adversarial_spec_debate(body: AdversarialSpecRequest) -> dict[str, Any]:
    """
    Fait débattre Léon (Spec) et Alex (QA) sur une spec jusqu'à consensus.
    Retourne la spec convergée + divergences + historique des rounds.
    """
    from services.adversarial_spec import debate_spec
    return debate_spec(body.spec_text, body.context, body.rounds, body.stop_on_approve)


@router.post("/adversarial-spec/quick-check")
def adversarial_spec_quick_check(body: QuickCheckRequest) -> dict[str, Any]:
    """Pre-check QA rapide sans itération. Identifie les problèmes critiques."""
    from services.adversarial_spec import quick_adversarial_check
    return quick_adversarial_check(body.spec_text, body.context)


# ---------------------------------------------------------------------------
# Parallel Runner (oh-my-claude-inspired)
# ---------------------------------------------------------------------------

class ParallelTask(BaseModel):
    agent_id: str
    method: str
    kwargs: dict[str, Any] = Field(default_factory=dict)
    task_label: str = ""
    award_points: bool = True


class ParallelRunRequest(BaseModel):
    tasks: list[ParallelTask]
    max_concurrent: int = Field(default=5, ge=1, le=10)
    fail_fast: bool = False


class AnalyticsRoomRequest(BaseModel):
    product: str
    business_question: str
    sql_question: str
    schema_context: str


class ContentSprintRequest(BaseModel):
    topic: str
    product: str
    target: str


@router.post("/parallel/run")
def parallel_run(body: ParallelRunRequest) -> dict[str, Any]:
    """Exécute plusieurs agents en parallèle simultanément."""
    from services.parallel_runner import run_agents_parallel_sync, AgentTask
    tasks = [
        AgentTask(
            agent_id=t.agent_id,
            method=t.method,
            kwargs=t.kwargs,
            task_label=t.task_label,
            award_points=t.award_points,
        )
        for t in body.tasks
    ]
    return run_agents_parallel_sync(tasks, body.max_concurrent, body.fail_fast)


@router.post("/parallel/analytics-room")
def parallel_analytics_room(body: AnalyticsRoomRequest) -> dict[str, Any]:
    """Lance Layla (Business) + Axel (Data) en parallèle sur la même question."""
    from services.parallel_runner import run_analytics_room
    return run_analytics_room(
        body.product, body.business_question, body.sql_question, body.schema_context
    )


@router.post("/parallel/content-sprint")
def parallel_content_sprint(body: ContentSprintRequest) -> dict[str, Any]:
    """Lance Camille (Marketing) + Sofia (Content) en parallèle sur le même sujet."""
    from services.parallel_runner import run_content_sprint
    return run_content_sprint(body.topic, body.product, body.target)


@router.post("/parallel/run-with-deps")
def parallel_run_with_deps(body: ParallelRunRequest) -> dict[str, Any]:
    """
    Exécute des tâches en respectant leurs dépendances (depends_on).
    Les tâches sans dépendances tournent en parallèle.
    """
    from services.parallel_runner import run_with_dependencies, AgentTask
    tasks = [
        AgentTask(
            agent_id=t.agent_id,
            method=t.method,
            kwargs=t.kwargs,
            task_label=t.task_label,
            award_points=t.award_points,
        )
        for t in body.tasks
    ]
    return run_with_dependencies(tasks, body.max_concurrent)


@router.get("/parallel/progress/{run_id}")
def parallel_progress(run_id: str) -> dict[str, Any]:
    """Suivi de progression en temps réel d'un run parallèle."""
    from services.parallel_runner import get_progress
    return get_progress(run_id)


@router.get("/parallel/runs")
def parallel_list_runs(limit: int = 20) -> list[dict[str, Any]]:
    """Liste les derniers runs parallèles."""
    from services.parallel_runner import list_runs
    return list_runs(limit)


# ---------------------------------------------------------------------------
# Content Pipeline (content-pipeline-inspired)
# ---------------------------------------------------------------------------

class ContentPipelineRequest(BaseModel):
    topic: str
    product: str
    target_audience: str
    tone: str = "professionnel, direct"
    key_messages:    list[str] = Field(default_factory=list)
    call_to_action: str = ""
    context: str = ""
    platforms: list[str] = Field(
        default_factory=lambda: ["twitter", "linkedin", "blog", "discord"]
    )


@router.post("/content-pipeline/run")
def content_pipeline_run(body: ContentPipelineRequest) -> dict[str, Any]:
    """
    Brief → contenus multi-plateformes en parallèle.
    Camille (Marketing) génère la stratégie, Sofia (Content) les textes.
    """
    from services.content_pipeline import run_pipeline, ContentBrief
    brief = ContentBrief(
        topic=body.topic,
        product=body.product,
        target_audience=body.target_audience,
        tone=body.tone,
        key_messages=body.key_messages,
        call_to_action=body.call_to_action,
        context=body.context,
    )
    return run_pipeline(brief, body.platforms)


@router.get("/content-pipeline/platforms")
def content_pipeline_platforms() -> list[dict[str, str]]:
    """Liste les plateformes supportées par le pipeline."""
    from services.content_pipeline import available_platforms
    return available_platforms()


# ---------------------------------------------------------------------------
# Trend Monitor (TrendRadar-inspired)
# ---------------------------------------------------------------------------

class TrendBriefRequest(BaseModel):
    topics: list[str]
    sources: list[str] = ["hackernews", "reddit", "github"]
    agent_id: str = "marketing"
    limit: int = 20


@router.get("/trends/today")
def trends_today(
    sources: str = "hackernews,reddit,github",
    topics: str = "",
    limit: int = 30,
) -> dict[str, Any]:
    """
    Tendances brutes du jour depuis HackerNews, Reddit, GitHub.
    GET /services/trends/today?sources=hackernews,reddit&topics=ai,python
    """
    from services.trend_monitor import get_raw_trends
    sources_list = [s.strip() for s in sources.split(",") if s.strip()]
    topics_list = [t.strip() for t in topics.split(",") if t.strip()]
    return get_raw_trends(sources_list, topics_list, limit)


@router.post("/trends/brief")
def trends_brief(body: TrendBriefRequest) -> dict[str, Any]:
    """
    Brief tendances synthétisé par Camille (Marketing) via LLM.
    Agrège HN, Reddit, GitHub → brief structuré avec recommandations.
    """
    from services.trend_monitor import get_trend_brief
    return get_trend_brief(
        topics=body.topics,
        sources=body.sources,
        limit=body.limit,
        agent_id=body.agent_id,
    )


# ---------------------------------------------------------------------------
# Deep Research (deep-research-inspired)
# ---------------------------------------------------------------------------

class DeepResearchRequest(BaseModel):
    query: str
    context: str = ""
    rounds: int = Field(default=3, ge=1, le=3)
    agent_id: str = "brainstorm"


class QuickResearchRequest(BaseModel):
    query: str
    context: str = ""
    agent_id: str = "brainstorm"


@router.post("/deep-research/run")
def deep_research_run(body: DeepResearchRequest) -> dict[str, Any]:
    """
    Recherche multi-rounds : explore → approfondit → vérifie → synthétise.
    Idris (brainstorm), Alex (rnd_agent) ou Layla (analyst_business) selon agent_id.
    """
    from services.deep_research import run_deep_research
    return run_deep_research(
        query=body.query,
        context=body.context,
        rounds=body.rounds,
        agent_id=body.agent_id,
    )


@router.post("/deep-research/quick")
def deep_research_quick(body: QuickResearchRequest) -> dict[str, Any]:
    """Recherche rapide 1 round — pour réponses immédiates sans itération."""
    from services.deep_research import quick_research
    return quick_research(
        query=body.query,
        context=body.context,
        agent_id=body.agent_id,
    )


# ---------------------------------------------------------------------------
# Plan Executor (ralphex-inspired)
# ---------------------------------------------------------------------------

class PlanStepBody(BaseModel):
    step_id: str
    description: str
    agent_id: str
    method: str
    kwargs: dict[str, Any] = Field(default_factory=dict)
    depends_on: list[str] = Field(default_factory=list)


class PlanExecuteRequest(BaseModel):
    title: str
    steps: list[PlanStepBody]
    context: str = ""
    max_concurrent: int = Field(default=3, ge=1, le=5)
    stop_on_failure: bool = False


class CooRunRequest(BaseModel):
    objective: str
    context: str = ""
    max_concurrent: int = Field(default=3, ge=1, le=5)
    stop_on_failure: bool = False


@router.post("/plan/execute")
def plan_execute(body: PlanExecuteRequest) -> dict[str, Any]:
    """
    Exécute un plan structuré pré-construit.
    Steps indépendants tournent en parallèle, dépendances respectées.
    """
    from services.plan_executor import execute_plan, ExecutionPlan, ExecutionStep
    steps = [
        ExecutionStep(
            step_id=s.step_id,
            description=s.description,
            agent_id=s.agent_id,
            method=s.method,
            kwargs=s.kwargs,
            depends_on=s.depends_on,
        )
        for s in body.steps
    ]
    plan = ExecutionPlan(title=body.title, steps=steps, context=body.context)
    return execute_plan(plan, body.max_concurrent, body.stop_on_failure)


@router.post("/plan/coo-run")
def plan_coo_run(body: CooRunRequest) -> dict[str, Any]:
    """
    Pipeline complet : Aria (COO) génère le plan depuis l'objectif → executor le déroule.
    Les agents appropriés sont sélectionnés et exécutés automatiquement.
    """
    from services.plan_executor import run_coo_plan
    return run_coo_plan(
        objective=body.objective,
        context=body.context,
        max_concurrent=body.max_concurrent,
        stop_on_failure=body.stop_on_failure,
    )


# ---------------------------------------------------------------------------
# Code Graph (graphify-inspired)
# ---------------------------------------------------------------------------

class CodeGraphQueryRequest(BaseModel):
    question: str
    agent_id: str = "analyst_data"
    rebuild: bool = False


@router.post("/code-graph/query")
def code_graph_query(body: CodeGraphQueryRequest) -> dict[str, Any]:
    """
    Répond à une question sur l'architecture du codebase en langage naturel.
    Axel (analyst_data) analyse le graphe et répond avec les nœuds pertinents.
    """
    from services.code_graph import query_graph
    return query_graph(body.question, body.agent_id, body.rebuild)


@router.get("/code-graph/summary")
def code_graph_summary(rebuild: bool = False) -> dict[str, Any]:
    """
    Vue d'ensemble du codebase : agents, endpoints, tables, fichiers les plus importés.
    """
    from services.code_graph import get_codebase_summary
    return get_codebase_summary(rebuild)


@router.get("/code-graph/agent/{agent_id}")
def code_graph_agent(agent_id: str) -> dict[str, Any]:
    """
    Contexte complet d'un agent dans le graphe :
    imports, méthodes définies, endpoints associés, tables utilisées.
    """
    from services.code_graph import get_agent_context
    return get_agent_context(agent_id)


@router.post("/code-graph/invalidate")
def code_graph_invalidate() -> dict[str, str]:
    """Force le rebuild du graphe au prochain appel (cache invalidé)."""
    from services.code_graph import invalidate_cache
    return invalidate_cache()


# ---------------------------------------------------------------------------
# Memory Compression (claude-mem-inspired)
# ---------------------------------------------------------------------------

class MemoryCompressRequest(BaseModel):
    agent_id: str
    threshold: int = 20


@router.post("/memory/compress")
def memory_compress(body: MemoryCompressRequest) -> dict[str, Any]:
    """
    Compresse les mémoires d'un agent si elles dépassent le seuil.
    Distille N leçons brutes → 3-5 règles comportementales durables.
    """
    from skills.skill_agent_learning import auto_compress_if_needed
    compressed = auto_compress_if_needed(body.agent_id, body.threshold, blocking=True)
    return {
        "agent_id": body.agent_id,
        "compressed": compressed,
        "message": "Compression lancée" if compressed else "Pas de compression nécessaire",
    }


# ---------------------------------------------------------------------------
# Cost Monitor (llm-cost-tracker-inspired) — Tier 3
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Coûts non-LLM — ElevenLabs (auto) + hébergeur (saisie manuelle)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# A/B Tester (prompt-optimizer-inspired) — Tier 3
# ---------------------------------------------------------------------------

class ABVariantBody(BaseModel):
    agent_id: str
    method: str
    kwargs: dict[str, Any] = Field(default_factory=dict)
    label: str = ""


class ABTestRequest(BaseModel):
    name: str
    variant_a: ABVariantBody
    variant_b: ABVariantBody
    judge_criteria: str = "Lequel est le plus utile, précis et bien structuré ?"
    runs_per_variant: int = Field(default=1, ge=1, le=3)
    judge_agent_id: str = "qa"


class QuickCompareRequest(BaseModel):
    agent_id: str
    method: str
    kwargs_a: dict[str, Any]
    kwargs_b: dict[str, Any]
    criteria: str = "Lequel est le meilleur résultat ?"


@router.post("/ab-test/run")
def ab_test_run(body: ABTestRequest) -> dict[str, Any]:
    """
    A/B test complet : exécute les deux variants en parallèle, LLM juge le gagnant.
    Alex (QA) est le juge par défaut.
    """
    from services.a_b_tester import run_ab_test, ABTestConfig
    config = ABTestConfig(
        name=body.name,
        variant_a=body.variant_a.model_dump(),
        variant_b=body.variant_b.model_dump(),
        judge_criteria=body.judge_criteria,
        runs_per_variant=body.runs_per_variant,
        judge_agent_id=body.judge_agent_id,
    )
    return run_ab_test(config)


@router.post("/ab-test/quick-compare")
def ab_test_quick_compare(body: QuickCompareRequest) -> dict[str, Any]:
    """Compare deux sets de kwargs sur le même agent — utile pour tester des paramètres."""
    from services.a_b_tester import quick_compare
    return quick_compare(
        agent_id=body.agent_id,
        method=body.method,
        kwargs_a=body.kwargs_a,
        kwargs_b=body.kwargs_b,
        criteria=body.criteria,
    )


# ---------------------------------------------------------------------------
# Event Bus (agent-memory-stream-inspired) — Tier 3
# ---------------------------------------------------------------------------

class EmitEventRequest(BaseModel):
    event_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    source_agent: str = ""


@router.post("/events/emit")
def events_emit(body: EmitEventRequest) -> dict[str, Any]:
    """Émet un événement sur le bus — déclenche les handlers abonnés."""
    from services.event_bus import emit
    event = emit(body.event_type, body.payload, body.source_agent)
    return event.to_dict()


@router.get("/events/recent")
def events_recent(
    event_type: str | None = None,
    source_agent: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Events récents du bus (en mémoire)."""
    from services.event_bus import get_recent_events
    return get_recent_events(event_type=event_type, source_agent=source_agent, limit=limit)


@router.get("/events/stats")
def events_stats() -> dict[str, Any]:
    """Stats du bus : counts par type, agents les plus actifs, handlers enregistrés."""
    from services.event_bus import get_event_stats
    return get_event_stats()


@router.get("/events/types")
def events_types() -> dict[str, str]:
    """Liste tous les types d'événements ALNUA disponibles."""
    from services.event_bus import EVENT_TYPES
    return EVENT_TYPES


@router.post("/events/clear")
def events_clear() -> dict[str, str]:
    """Vide le store en mémoire (logs disque conservés)."""
    from services.event_bus import clear_store
    return clear_store()


# ---------------------------------------------------------------------------
# Daily Briefing (morning-digest-inspired) — Tier 3
# ---------------------------------------------------------------------------

class BriefingRequest(BaseModel):
    context: str = ""
    include_trends: bool = True
    include_costs: bool = True
    include_events: bool = True


@router.post("/briefing/daily")
def briefing_daily(body: BriefingRequest) -> dict[str, Any]:
    """
    Briefing quotidien complet : leaderboard + trends + coûts + events → Aria synthétise.
    Déclenché chaque matin par n8n — donne les priorités du jour à Emilie.
    """
    from services.daily_briefing import run_daily_briefing
    return run_daily_briefing(
        context=body.context,
        include_trends=body.include_trends,
        include_costs=body.include_costs,
        include_events=body.include_events,
    )


@router.post("/briefing/quick")
def briefing_quick(context: str = "") -> dict[str, Any]:
    """Version rapide du briefing — leaderboard + coûts uniquement, sans trends."""
    from services.daily_briefing import run_quick_briefing
    return run_quick_briefing(context=context)
