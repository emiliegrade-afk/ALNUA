"""Bureau library API — research archives per department."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter(prefix="/library", tags=["library"])


@router.get("/bureaus")
def library_bureaus() -> dict[str, Any]:
    from services.bureau_library import get_bureaus_meta

    return {"bureaus": get_bureaus_meta()}


@router.get("/entries")
def library_entries(
    bureau: str | None = None,
    timing: str | None = None,
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    from services.bureau_library import list_entries

    t: str | None = timing if timing in ("now", "later") else None
    return list_entries(bureau=bureau, timing=t, limit=limit, offset=offset)


@router.post("/research")
def library_research(body: LibraryResearchRequest) -> dict[str, Any]:
    """Launch web research — all findings archived (nothing discarded)."""
    from services.bureau_library import run_bureau_research

    return run_bureau_research(
        body.query.strip(),
        bureaus=body.bureaus,
        requested_by=body.requested_by,
        blocking=body.wait,
    )


@router.post("/report")
def library_ceo_report(body: LibraryReportRequest | None = None) -> dict[str, Any]:
    """CEO report: Hub improvements + R&D ideas from library."""
    from services.bureau_library import generate_ceo_report

    req = body or LibraryReportRequest()
    return generate_ceo_report(days=req.days)


@router.post("/enrich")
def library_enrich_team(body: LibraryEnrichRequest | None = None) -> dict[str, Any]:
    """Diffuse bibliothèque vers Mem0 de tous les agents du bureau concerné."""
    from services.team_enrichment import enrich_team_from_library, get_enrichment_status

    req = body or LibraryEnrichRequest()
    timing = req.timing if req.timing in ("now", "later") else None
    result = enrich_team_from_library(days=req.days, timing=timing, limit=req.limit)
    result["status"] = get_enrichment_status()
    return result


@router.get("/enrich/status")
def library_enrich_status() -> dict[str, Any]:
    from services.team_enrichment import get_enrichment_status

    return get_enrichment_status()


@router.get("/distribution/status")
def library_distribution_status() -> dict[str, Any]:
    """Alias — prefer GET /library/enrich/status (same payload)."""
    from services.team_enrichment import get_enrichment_status

    return get_enrichment_status()


@router.post("/enrich/distribute-all")
@router.post("/distribution/distribute-all")
def library_distribute_all(
    body: LibraryDistributeAllRequest | None = None,
) -> dict[str, Any]:
    from services.library_distribution import start_distribute_all_job

    req = body or LibraryDistributeAllRequest()
    timing = req.timing if req.timing in ("now", "later") else None
    return start_distribute_all_job(
        skip_distributed=req.skip_distributed,
        timing=timing,
        run_learning=req.run_learning,
    )


@router.post("/enrich/learn-pending")
@router.post("/distribution/learn-pending")
def library_learn_pending() -> dict[str, Any]:
    from services.library_distribution import start_learn_pending_job

    return start_learn_pending_job()


@router.post("/enrich/verify")
@router.post("/distribution/verify")
def library_verify_mem0() -> dict[str, Any]:
    from services.library_distribution import start_verify_all_job

    return start_verify_all_job()


@router.get("/distribution/jobs/{job_id}")
@router.get("/enrich/jobs/{job_id}")
def library_distribution_job(job_id: str) -> dict[str, Any]:
    from services.library_distribution import get_job

    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job introuvable")
    return job


@router.post("/jobs/cancel")
@router.post("/enrich/jobs/cancel")
def library_cancel_job() -> dict[str, Any]:
    from services.library_distribution import cancel_active_job

    return cancel_active_job()


@router.get("/retention/preview")
def library_retention_preview() -> dict[str, Any]:
    from services.library_retention import preview_retention

    return preview_retention()


@router.post("/retention/apply")
def library_retention_apply(
    body: LibraryRetentionApplyRequest | None = None,
) -> dict[str, Any]:
    from services.library_retention import apply_retention

    req = body or LibraryRetentionApplyRequest()
    return apply_retention(
        compress=req.compress,
        purge=req.purge,
        dry_run=req.dry_run,
    )
