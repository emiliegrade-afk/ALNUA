"""GitHub Issues — full issue pipeline (spec → coding agent → labels/QA)."""

from __future__ import annotations

import logging
from datetime import datetime

from config.github_repos import issue_target
from skills.gh_issues_client import post_comment, set_label
from skills.gh_issues_process_handlers import handle_failure, handle_success
from skills.gh_issues_spec import issue_to_spec

logger = logging.getLogger(__name__)


def process_issue(
    issue: dict,
    repo_path: str | None = None,
    telegram_notify_fn=None,
) -> dict:
    """
    Traite une issue complète : spec → coding agent → update issue.
    L'issue doit être annotée (_repo_slug, _github_repo) ou issue_target() échouera.
    """
    from skills.skill_coding_agent import execute_coding_task
    from skills.skill_playwright import run_and_report
    from services.coding_pipeline import merge_pr_if_allowed, resolve_default_branch, should_auto_merge_repo

    target = issue_target(issue)
    local_path = repo_path or issue.get("_repo_path") or str(target.local_path)
    number = issue["number"]
    title = issue["title"]
    github_repo = target.github_repo

    logger.info(
        "[GHIssues] Traitement issue #%s (%s) : %s",
        number,
        target.name,
        title,
    )

    if not target.local_path.is_dir():
        error = (
            f"Chemin local introuvable pour {target.name} : {target.local_path}. "
            f"Clone le repo ou configure REPO_PATH_{target.slug.upper()}."
        )
        logger.error("[GHIssues] %s", error)
        return {"success": False, "error": error, "pr_url": None, "branch": None}

    set_label(
        number,
        ["in-pipeline"],
        remove_labels=["agent-ready"],
        github_repo=github_repo,
    )
    post_comment(
        number,
        f"[BOT] **Dev App Agent** prend en charge cette issue ({target.name}).\n\n"
        f"Pipeline démarré à {datetime.now().strftime('%H:%M')}...",
        github_repo=github_repo,
    )

    from services.coding_activity import append_log, set_progress, start_task

    activity_id = start_task(
        issue_number=number,
        title=title,
        repo_slug=target.slug,
        github_repo=github_repo,
    )
    try:
        from agents.base import log_agent_action
        from database.supabase_client import get_supabase

        log_agent_action(
            get_supabase(),
            "dev_app",
            "coding_pipeline",
            input_summary=f"#{number} {title[:80]}",
            output_summary="en cours",
            status="pending",
        )
    except Exception:
        pass

    if telegram_notify_fn:
        telegram_notify_fn(
            f"🔧 Pipeline démarré ({target.name})\n**Issue #{number}** : {title}"
        )

    spec = issue_to_spec(issue, local_path)
    spec["activity_id"] = activity_id
    append_log(activity_id, "Lancement coding agent (worktree + PR)...")
    set_progress(activity_id, 25)
    result = execute_coding_task(spec, telegram_notify_fn=telegram_notify_fn)
    set_progress(activity_id, 90)

    if result["success"]:
        handle_success(
            issue_number=number,
            title=title,
            target=target,
            github_repo=github_repo,
            local_path=local_path,
            spec=spec,
            result=result,
            activity_id=activity_id,
            telegram_notify_fn=telegram_notify_fn,
            run_and_report=run_and_report,
            merge_pr_if_allowed=merge_pr_if_allowed,
            resolve_default_branch=resolve_default_branch,
            should_auto_merge_repo=should_auto_merge_repo,
        )
    else:
        handle_failure(
            issue_number=number,
            title=title,
            target=target,
            github_repo=github_repo,
            spec=spec,
            result=result,
            activity_id=activity_id,
            telegram_notify_fn=telegram_notify_fn,
        )

    return result
