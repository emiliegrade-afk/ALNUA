"""Orchestration routes — chaînes agent→agent pour n8n."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter(prefix="/orchestration", tags=["orchestration"])


@router.get("/workflows")
def list_orchestration_workflows() -> list[dict[str, Any]]:
    """Catalogue des workflows disponibles (pour config n8n / debug)."""
    from services.orchestration import WORKFLOW_CATALOG

    return WORKFLOW_CATALOG


@router.post("/morning")
def orchestration_morning(body: OrchestrationMorningRequest | None = None) -> dict[str, Any]:
    """
    Briefing quotidien + plan COO.
    n8n cron : lun-ven 08:00. Passer weekly_plan=true le lundi.
    """
    from services.orchestration import run_morning_orchestration

    weekly = body.weekly_plan if body else False
    return run_morning_orchestration(weekly_plan=weekly)


@router.post("/spec-qa-chain")
def orchestration_spec_qa_chain(body: OrchestrationSpecQaRequest) -> dict[str, Any]:
    """Léon (Spec) ↔ Alex (QA) — spec adversariale jusqu'à consensus."""
    from services.orchestration import run_spec_qa_chain

    return run_spec_qa_chain(
        body.spec_text,
        context=body.context,
        rounds=body.rounds,
        stop_on_approve=body.stop_on_approve,
        create_qa_ticket=body.create_qa_ticket,
        project_id=body.project_id,
        project_slug=body.project_slug,
        ticket_title=body.ticket_title,
    )


@router.post("/github-pr-review")
def orchestration_github_pr_review(body: OrchestrationGithubPrRequest) -> dict[str, Any]:
    """Revue backend Hao Chen sur un PR GitHub (via webhook n8n)."""
    from services.orchestration import run_github_pr_review

    return run_github_pr_review(
        repo=body.repo,
        pr_number=body.pr_number,
        title=body.title,
        diff_summary=body.diff_summary,
        changed_files=body.changed_files,
    )


@router.post("/welcome-user")
def orchestration_welcome_user(body: OrchestrationWelcomeRequest) -> dict[str, Any]:
    """Email de bienvenue Nadia — nouvel inscrit waitlist/beta/auth."""
    from services.orchestration import run_welcome_sequence

    return run_welcome_sequence(
        recipient_name=body.recipient_name,
        recipient_email=body.recipient_email,
        project=body.project,
        language=body.language,
    )


@router.post("/content-sprint")
def orchestration_content_sprint(body: OrchestrationContentSprintRequest) -> dict[str, Any]:
    """Sprint contenu multi-plateforme Sofia + Camille."""
    from services.orchestration import run_content_sprint

    return run_content_sprint(
        brief=body.brief,
        platforms=body.platforms,
        project=body.project,
    )


@router.post("/academy-sprint")
def orchestration_academy_sprint(body: AcademySprintRequest) -> dict[str, Any]:
    """Sprint Académie ALNUA — seed issues + agent-ready (n8n workflow 08)."""
    from services.orchestration import run_academy_sprint_orchestration

    return run_academy_sprint_orchestration(
        level=body.level,
        seed_if_missing=body.seed_if_missing,
        mark_ready_count=body.mark_ready_count,
    )


@router.post("/academy-poll")
def orchestration_academy_poll(body: AcademyPollRequest | None = None) -> dict[str, Any]:
    """Sync Academy + fermer issues + queue agent-ready (n8n workflow 12)."""
    from services.orchestration import run_academy_poll_orchestration

    req = body or AcademyPollRequest()
    return run_academy_poll_orchestration(
        mark_ready_if_idle=req.mark_ready_if_idle,
        mark_ready_count=req.mark_ready_count,
        notify=req.notify,
    )


@router.get("/pipeline-status")
def orchestration_pipeline_status() -> dict[str, Any]:
    """État agents coding — working / idle / stuck (CEO cockpit)."""
    from services.agent_wake import get_pipeline_status

    return get_pipeline_status()


@router.post("/wake")
def orchestration_wake(body: WakeAgentsRequest | None = None) -> dict[str, Any]:
    """Réveille les agents : sync + retry échecs + alimente agent-ready."""
    from services.agent_wake import wake_agents

    req = body or WakeAgentsRequest()
    return wake_agents(
        retry_failed=req.retry_failed,
        mark_ready_count=req.mark_ready_count,
        sync=req.sync,
        notify=req.notify,
    )


@router.post("/team-enrich")
def orchestration_team_enrich(body: LibraryEnrichRequest | None = None) -> dict[str, Any]:
    """Phase 3 — diffuse la bibliothèque vers Mem0 (n8n / CEO)."""
    from services.team_enrichment import enrich_team_from_library

    req = body or LibraryEnrichRequest()
    timing = req.timing if req.timing in ("now", "later") else None
    return enrich_team_from_library(days=req.days, timing=timing, limit=req.limit)


@router.post("/prd-decompose")
def orchestration_prd_decompose(body: PrdDecomposeOrchestrationRequest) -> dict[str, Any]:
    """CEO approved → engineering spec → GitHub issues (n8n workflow 07)."""
    from services.orchestration import run_prd_decompose_orchestration

    return run_prd_decompose_orchestration(
        dossier_id=body.dossier_id,
        repo_slug=body.repo_slug,
        dry_run=body.dry_run,
        mark_ready_count=body.mark_ready_count,
        force_spec=body.force_spec,
    )


@router.post("/sentry-ingest")
def orchestration_sentry_ingest(body: dict[str, Any]) -> dict[str, Any]:
    """Relay Sentry alert payload (n8n workflow 09)."""
    from services.orchestration import run_sentry_ingest_orchestration

    return run_sentry_ingest_orchestration(body)


@router.post("/academy-gate")
def orchestration_academy_gate() -> dict[str, Any]:
    """Évalue gate Academy → Lounge + notification CEO (n8n workflow 10)."""
    from services.orchestration import run_academy_gate_orchestration

    return run_academy_gate_orchestration()
