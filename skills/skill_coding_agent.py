"""Coding agent skill — façade (debt paydown).

Public API unchanged: execute_coding_task, run_command, build_claude_prompt,
_cleanup_stale_worktree.
"""
from __future__ import annotations

from skills.coding_agent_backends import _execute_coding_task_core  # noqa: F401
from skills.coding_agent_hub_aider import (  # noqa: F401
    _execute_aider_task_core,
    _execute_hub_task_core,
)
from skills.coding_agent_cli import _resolve_cli, run_command  # noqa: F401
from skills.coding_agent_prompt import build_claude_prompt  # noqa: F401
from skills.coding_agent_worktree import (  # noqa: F401
    _cleanup_stale_worktree,
    _enforce_pre_pr_qa,
    _enforce_worktree_limit,
    _finalize_pr,
    _prepare_worktree,
    _resolve_spec_agent_id,
    _worktree_has_changes,
)

def execute_coding_task(

    spec: dict,
    telegram_notify_fn=None,
) -> dict:
    """

    Point d'entrée principal — avec retry intelligent.
    Consulte le journal d'erreurs avant chaque tentative.
    """

    spec = {**spec, "agent_id": _resolve_spec_agent_id(spec)}
    from skills.skill_retry_loop import retry_with_learning

    def _attempt(learning_context: str) -> dict:
        from services.coding_learning import enrich_spec_with_lessons, record_qa_failure
        enriched_spec = enrich_spec_with_lessons(dict(spec))
        if learning_context:
            enriched_spec["description"] = spec["description"] + learning_context
        try:
            return _execute_coding_task_core(enriched_spec)
        except RuntimeError as exc:
            if "QA pre-PR" in str(exc) or "QA" in str(exc):
                record_qa_failure(
                    agent_name=spec.get("agent_id"),
                    task_id=spec.get("task_id"),
                    repo_slug=spec.get("repo_slug"),
                    error_message=str(exc),
                    task_context=spec.get("title", ""),
                )
            raise
    retry_result = retry_with_learning(
        agent_name=spec.get("agent_id"),
        task_fn=_attempt,
        task_id=spec.get("task_id"),
        task_context=f"Tâche : {spec.get('title')}\nRepo : {spec.get('repo_path')}",
        max_attempts=3,
        telegram_notify_fn=telegram_notify_fn,
    )
    if retry_result["success"]:
        return retry_result["result"]
    return {
        "success": False,
        "pr_url": None,
        "branch": spec.get("branch_name"),
        "commit_sha": None,
        "claude_output": "",
        "error": retry_result["error"],
        "escalated": retry_result["escalated"],
    }

