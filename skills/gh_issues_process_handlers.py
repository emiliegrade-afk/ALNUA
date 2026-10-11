"""GitHub Issues pipeline — success/failure handlers."""

from __future__ import annotations

import logging
import re

from skills.gh_issues_client import post_comment, set_label

logger = logging.getLogger(__name__)


def handle_success(
    *,
    issue_number: int,
    title: str,
    target,
    github_repo: str,
    local_path: str,
    spec: dict,
    result: dict,
    activity_id: str,
    telegram_notify_fn,
    run_and_report,
    merge_pr_if_allowed,
    resolve_default_branch,
    should_auto_merge_repo,
) -> None:
    from services.coding_activity import finish_task

    set_label(
        issue_number,
        ["agent-done"],
        remove_labels=["in-pipeline"],
        github_repo=github_repo,
    )
    commit_sha = result.get("commit_sha") or ""
    short_sha = commit_sha[:7] if commit_sha else "n/a"
    post_comment(
        issue_number,
        f"[OK] **PR créée avec succès !**\n\n"
        f"**PR :** {result['pr_url']}\n"
        f"**Branch :** `{result['branch']}`\n"
        f"**Commit :** `{short_sha}`\n\n"
        f"Les tests QA ont été lancés automatiquement.",
        github_repo=github_repo,
    )
    if telegram_notify_fn:
        telegram_notify_fn(
            f"[OK] **Pipeline terminé** ({target.name})\n"
            f"Issue #{issue_number} : {title}\n"
            f"PR : {result['pr_url']}"
        )

    match = re.search(r"/pull/(\d+)", result.get("pr_url") or "")
    test_passed = bool(result.get("qa_passed"))
    if match:
        pr_number = int(match.group(1))
        if target.slug != "academy":
            try:
                qa = run_and_report(
                    local_path,
                    result["branch"],
                    pr_number,
                    telegram_notify_fn,
                    github_repo=github_repo,
                )
                test_passed = bool(qa.get("passed")) or test_passed
            except Exception as exc:
                logger.warning("[GHIssues] QA tests failed to run: %s", exc)

        merge_result = merge_pr_if_allowed(
            local_path,
            pr_number,
            tests_passed=test_passed,
            repo_slug=target.slug,
            agent_id="gh_issues",
        )
        if merge_result.get("merged"):
            post_comment(
                issue_number,
                f"[OK] **PR #{pr_number} mergée sur `{resolve_default_branch(local_path)}`** "
                f"(auto-merge {'academy' if target.slug == 'academy' else 'global'}).",
                github_repo=github_repo,
            )
            if target.slug == "academy":
                academy_post_merge(issue_number, github_repo, spec, result, title)
            if telegram_notify_fn:
                telegram_notify_fn(
                    f"[OK] PR #{pr_number} auto-mergée ({target.name})"
                )
        elif test_passed and not should_auto_merge_repo(target.slug):
            post_comment(
                issue_number,
                "Tests QA passés — PR en attente de review manuelle.",
                github_repo=github_repo,
            )
        elif not test_passed:
            post_comment(
                issue_number,
                "[ATTENTION] PR créée mais QA non validée — review manuelle requise.",
                github_repo=github_repo,
            )

    pr_line = result.get("pr_url") or "PR ok"
    finish_task(activity_id, success=True, message=f"[OK] {pr_line[:120]}")
    log_agent_action(issue_number, title, str(pr_line)[:200], "success")


def academy_post_merge(
    issue_number: int,
    github_repo: str,
    spec: dict,
    result: dict,
    title: str,
) -> None:
    try:
        from services.academy_issue_sync import close_issue
        from services.coding_learning import record_coding_success
        from services.agent_wake import queue_academy_if_idle

        record_coding_success(
            agent_name="dev_app",
            task_id=spec.get("task_id"),
            repo_slug="academy",
            outcome_summary=result.get("pr_url") or title,
        )
        # DEC-043: a merged academy PR = a validated exercise — feed the trust
        # loop (paper weight 0.5, capped at ACADEMY_TRUST_CAP by the store).
        from services.agent_trust import record_validation

        m = re.search(r"\[ACADEMY\s+(N\d+\.\d+)\]", title or "", re.I)
        eid = m.group(1).upper() if m else f"issue-{issue_number}"
        record_validation(
            "dev_app",
            success=True,
            weight=0.5,
            note=f"{eid} merged (issue #{issue_number})",
            source="academy:app",
        )
        close_issue(
            issue_number,
            github_repo=github_repo,
            comment="[BOT] PR mergée — exercice terminé.",
        )
        wake = queue_academy_if_idle()
        if wake.get("marked_count"):
            logger.info(
                "[GHIssues] Auto-queue après merge #%s: %s",
                issue_number,
                wake.get("marked"),
            )
    except Exception as exc:
        logger.warning("[GHIssues] academy post-merge sync: %s", exc)


def handle_failure(
    *,
    issue_number: int,
    title: str,
    target,
    github_repo: str,
    spec: dict,
    result: dict,
    activity_id: str,
    telegram_notify_fn,
) -> None:
    from services.coding_activity import finish_task

    set_label(
        issue_number,
        ["agent-failed"],
        remove_labels=["in-pipeline"],
        github_repo=github_repo,
    )
    post_comment(
        issue_number,
        f"[ERREUR] **Pipeline échoué**\n\nErreur : `{result['error']}`\n\nIntervention humaine requise.",
        github_repo=github_repo,
    )
    if telegram_notify_fn:
        telegram_notify_fn(
            f"[ERREUR] **Pipeline échoué** ({target.name})\n"
            f"Issue #{issue_number} : {title}\n"
            f"Erreur : {result['error']}"
        )
    try:
        from services.coding_learning import record_qa_failure

        if result.get("error"):
            record_qa_failure(
                agent_name="dev_app",
                task_id=spec.get("task_id"),
                repo_slug=target.slug,
                error_message=str(result["error"]),
                task_context=title,
            )
        # DEC-043: a crashed academy pipeline = failed exercise (weight 2.0,
        # same as terminal failure in the drill academies). Academy scope only
        # — production repos feed trust via workflows/review board instead.
        if getattr(target, "slug", "") == "academy":
            from services.agent_trust import record_validation

            m = re.search(r"\[ACADEMY\s+(N\d+\.\d+)\]", title or "", re.I)
            eid = m.group(1).upper() if m else f"issue-{issue_number}"
            record_validation(
                "dev_app",
                success=False,
                weight=2.0,
                note=f"{eid} pipeline failed (issue #{issue_number})",
                source="academy:app",
            )
    except Exception:
        pass
    finish_task(activity_id, success=False, message=f"[ERREUR] {result.get('error', '')[:120]}")
    log_agent_action(issue_number, title, str(result.get("error", ""))[:200], "error")


def log_agent_action(issue_number: int, title: str, output_summary: str, status: str) -> None:
    try:
        from agents.base import log_agent_action as _log
        from database.supabase_client import get_supabase

        _log(
            get_supabase(),
            "dev_app",
            "coding_pipeline",
            input_summary=f"#{issue_number} {title[:80]}",
            output_summary=output_summary,
            status=status,
        )
    except Exception:
        pass
