"""Background worker and run lifecycle for App Factory."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from agents.base import log_agent_action
from config.github_repos import resolve_target

from services.app_factory_issues import create_issue_on_repo, format_issue_body
from services.app_factory_models import (
    AppFactoryRequest,
    _RUNS,
    default_local_path,
    new_run_id,
    slugify,
    utc_now_iso,
)
from services.app_factory_plan import generate_factory_plan
from services.app_factory_scaffold import (
    ensure_local_scaffold,
    persist_plan,
    register_factory_app,
)

logger = logging.getLogger(__name__)


def run_app_factory_sync(
    run_id: str,
    req: AppFactoryRequest,
    *,
    dry_run: bool = False,
) -> None:
    """Background worker — updates _RUNS[run_id] in place."""
    run = _RUNS[run_id]
    slug = slugify(req.slug or req.name)

    def log(msg: str) -> None:
        run["log"].append(msg)
        logger.info("[AppFactory %s] %s", run_id[:8], msg)

    try:
        run["status"] = "planning"
        run["progress"] = 10
        log(f"Plan MVP pour « {req.name} » ({req.stack})")

        plan = generate_factory_plan(req.name, req.brief, req.stack, dry_run=dry_run)
        run["plan"] = [t.model_dump() for t in plan]
        run["progress"] = 25
        persist_plan(slug, plan)
        log(f"{len(plan)} tâches générées")

        run["status"] = "registering"
        app_entry = register_factory_app(req, slug)
        run["app"] = app_entry
        run["slug"] = slug
        run["progress"] = 40
        log(f"App enregistrée: {slug}")

        local_path = Path(app_entry.get("local_path") or default_local_path(slug))
        if ensure_local_scaffold(slug, req.stack, local_path):
            log(f"Scaffold local créé: {local_path}")

        github_repo = (req.github_repo or app_entry.get("github_repo") or "").strip()
        if not github_repo:
            run["status"] = "needs_github"
            run["progress"] = 100
            log("Pas de repo GitHub — ajoute github_repo dans Mes apps puis relance pipeline")
            return

        if dry_run:
            run["status"] = "completed"
            run["progress"] = 100
            log("Dry-run — issues non créées")
            return

        run["status"] = "creating_issues"
        target = resolve_target(repo_slug=slug)
        issues: list[dict[str, Any]] = []
        for i, task in enumerate(plan):
            labels = ["agent-ready"] if i == 0 else ["backlog"]
            body = format_issue_body(task, req.stack)
            issue = create_issue_on_repo(
                target,
                title=task.title,
                body=body,
                labels=labels,
            )
            issues.append(
                {
                    "number": issue["number"],
                    "title": issue["title"],
                    "url": issue.get("html_url", ""),
                    "agent_ready": i == 0,
                }
            )
            log(f"Issue #{issue['number']}: {task.title}")

        run["issues"] = issues
        run["progress"] = 70

        if req.auto_run_pipeline and issues:
            run["status"] = "coding"
            log(f"Lancement pipeline sur issue #{issues[0]['number']}")
            from skills.skill_gh_issues import get_issue, process_issue

            issue_full = get_issue(issues[0]["number"], repo_slug=slug)
            repo_path = str(target.local_path)
            result = process_issue(issue_full, repo_path, None)
            run["pipeline"] = result
            if result.get("success"):
                run["status"] = "completed"
                run["progress"] = 100
                log(f"PR créée: {result.get('pr_url', '')[:80]}")
            else:
                run["status"] = "pipeline_failed"
                run["progress"] = 100
                log(f"Pipeline échoué: {result.get('error', 'unknown')}")
        else:
            run["status"] = "completed"
            run["progress"] = 100
            log("Issues créées — pipeline non lancé")

        try:
            from database.supabase_client import get_supabase

            log_agent_action(
                get_supabase(),
                "dev_app",
                "app_factory_run",
                input_summary=f"{slug}: {req.name[:60]}",
                output_summary=run["status"],
            )
        except Exception:
            pass
    except Exception as exc:
        logger.exception("App factory run %s failed", run_id)
        run["status"] = "failed"
        run["progress"] = 100
        run["error"] = str(exc)
        log(f"ERREUR: {exc}")


def start_app_factory_run(req: AppFactoryRequest, *, dry_run: bool = False) -> dict[str, Any]:
    """Queue a factory run; caller must schedule run_app_factory_sync in background."""
    run_id = new_run_id()
    _RUNS[run_id] = {
        "run_id": run_id,
        "status": "queued",
        "progress": 0,
        "log": [],
        "slug": slugify(req.slug or req.name),
        "started_at": utc_now_iso(),
        "dry_run": dry_run,
    }
    return {"run_id": run_id, "status": "queued", "slug": _RUNS[run_id]["slug"]}


def get_factory_run(run_id: str) -> dict[str, Any] | None:
    return _RUNS.get(run_id)


def list_factory_runs(limit: int = 20) -> list[dict[str, Any]]:
    items = sorted(
        _RUNS.values(),
        key=lambda r: r.get("started_at", ""),
        reverse=True,
    )
    return items[:limit]


def trigger_pipeline_for_run(run_id: str) -> dict[str, Any]:
    """Manually start coding pipeline on first agent-ready issue."""
    run = _RUNS.get(run_id)
    if not run:
        raise ValueError("Run introuvable")
    slug = run.get("slug") or ""
    issues = run.get("issues") or []
    if not issues:
        raise ValueError("Aucune issue — configure github_repo et relance la factory")
    from skills.skill_gh_issues import get_issue, process_issue

    target = resolve_target(repo_slug=slug)
    issue_full = get_issue(issues[0]["number"], repo_slug=slug)
    result = process_issue(issue_full, str(target.local_path), None)
    run["pipeline"] = result
    run["status"] = "completed" if result.get("success") else "pipeline_failed"
    return result
