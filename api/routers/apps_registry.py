"""App registry — link Hub to local repos and GitHub projects."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter(prefix="/apps", tags=["apps"])


class AppRegistryUpsertBody(BaseModel):
    slug: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=120)
    branch: Literal["app", "gaming", "robotics", "hub", "other"] = "app"
    github_repo: str = ""
    local_path: str = ""
    description: str = ""
    stack: str = ""
    prod_url: str = ""
    lifecycle_status: Literal["idea", "build", "beta", "prod"] = "build"
    enabled: bool = True


@router.get("/registry")
def apps_registry_list(include_disabled: bool = True) -> dict[str, Any]:
    from services.app_registry import list_apps, registry_summary

    apps = list_apps(include_disabled=include_disabled)
    return {
        "summary": registry_summary(),
        "apps": [a.model_dump() for a in apps],
    }


@router.get("/registry/{slug}")
def apps_registry_get(slug: str) -> dict[str, Any]:
    from services.app_registry import get_app

    entry = get_app(slug)
    if not entry:
        raise HTTPException(status_code=404, detail="App not found")
    return entry.model_dump()


@router.post("/registry")
def apps_registry_upsert(body: AppRegistryUpsertBody) -> dict[str, Any]:
    from services.app_registry import AppRegistryUpsert, upsert_app

    entry = upsert_app(AppRegistryUpsert(**body.model_dump()))
    return entry.model_dump()


@router.delete("/registry/{slug}")
def apps_registry_delete(slug: str) -> dict[str, str]:
    from services.app_registry import get_app, remove_app

    entry = get_app(slug)
    if not entry:
        raise HTTPException(status_code=404, detail="App not found")
    if entry.source == "env":
        raise HTTPException(
            status_code=400,
            detail="App definie dans .env — modifie GITHUB_REPO_* ou desactive via upsert",
        )
    if not remove_app(slug):
        raise HTTPException(status_code=400, detail="Suppression impossible")
    return {"status": "deleted", "slug": slug}


class AppFactoryBody(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    brief: str = Field(..., min_length=10, max_length=8000)
    stack: Literal["nextjs", "expo"] = "nextjs"
    slug: str = ""
    github_repo: str = ""
    local_path: str = ""
    branch: Literal["app", "gaming", "robotics", "other"] = "app"
    auto_run_pipeline: bool = True
    dry_run: bool = False


@router.post("/factory")
async def apps_factory_start(body: AppFactoryBody) -> dict[str, Any]:
    """Brief → plan MVP → registry → issues GitHub → pipeline (Phase 2)."""
    from services.app_factory import AppFactoryRequest, run_app_factory_sync, start_app_factory_run

    req = AppFactoryRequest(**body.model_dump(exclude={"dry_run"}))
    queued = start_app_factory_run(req, dry_run=body.dry_run)
    run_id = queued["run_id"]
    asyncio.create_task(
        asyncio.to_thread(run_app_factory_sync, run_id, req, dry_run=body.dry_run)
    )
    return queued


@router.get("/factory/runs")
def apps_factory_list_runs(limit: int = 20) -> dict[str, Any]:
    from services.app_factory import list_factory_runs

    runs = list_factory_runs(limit=limit)
    return {"runs": runs, "count": len(runs)}


@router.get("/factory/runs/{run_id}")
def apps_factory_get_run(run_id: str) -> dict[str, Any]:
    from services.app_factory import get_factory_run

    run = get_factory_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.post("/factory/runs/{run_id}/pipeline")
def apps_factory_trigger_pipeline(run_id: str) -> dict[str, Any]:
    from services.app_factory import trigger_pipeline_for_run

    try:
        return trigger_pipeline_for_run(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
