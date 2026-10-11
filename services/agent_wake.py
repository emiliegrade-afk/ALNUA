"""Wake idle coding agents — queue Academy issues + optional retry failed."""

from __future__ import annotations

import logging
from typing import Any, Literal

from config.github_repos import get_target_by_slug

# Re-exports — keep ``from services.agent_wake import queue_academy_if_idle`` stable.
from services.agent_wake_queue import (  # noqa: F401
    academy_label_counts,
    queue_academy_if_idle,
    requeue_failed_academy,
    reset_stuck_in_pipeline,
)

logger = logging.getLogger(__name__)

Verdict = Literal["working", "idle", "stuck", "unconfigured"]


def get_pipeline_status() -> dict[str, Any]:
    """CEO-friendly snapshot — are agents working or idling?"""
    target = get_target_by_slug("academy")
    if not target:
        return {"verdict": "unconfigured", "message": "GITHUB_REPO_ACADEMY non configuré"}

    from services.academy_progress import load_progress
    from services.agent_wake_queue import _pipeline_slots_free, academy_label_counts as _counts

    try:
        counts = _counts()
        slots, max_parallel = _pipeline_slots_free()
    except Exception as exc:
        logger.warning("[AgentWake] pipeline status github failed: %s", exc)
        return {
            "verdict": "stuck",
            "message": f"GitHub Academy inaccessible ({exc.__class__.__name__}).",
            "academy": {
                "github_repo": target.github_repo,
                "repo_path_exists": target.local_path.is_dir(),
            },
        }

    progress = load_progress()
    repo_path_exists = target.local_path.is_dir()

    if (counts["in-pipeline"] > 0 or counts["agent-ready"] > 0) and not repo_path_exists:
        # skill_gh_issues.py::process_issue échoue avant même de poser le label
        # "in-pipeline" quand target.local_path n'existe pas — l'issue reste
        # bloquée sur "agent-ready" indéfiniment, et sans ce cas explicite le
        # verdict "working" ("prise en charge sous ~60s") ne se réalise jamais :
        # aucun code n'est jamais écrit, la progression reste à 0% en silence.
        verdict: Verdict = "stuck"
        message = (
            f"Chemin local introuvable : {target.local_path} — "
            f"clone le repo ou configure REPO_PATH_{target.slug.upper()} "
            f"({counts['agent-ready'] + counts['in-pipeline']} issue(s) bloquée(s))."
        )
    elif counts["in-pipeline"] > 0:
        verdict = "working"
        message = f"{counts['in-pipeline']} issue(s) en cours de codage."
    elif counts["agent-ready"] > 0:
        verdict = "working"
        message = f"{counts['agent-ready']} issue(s) en file — prise en charge sous ~60s."
    elif counts["agent-failed"] > 0:
        verdict = "stuck"
        message = (
            f"{counts['agent-failed']} issue(s) en échec — lance wake-agents pour relancer."
        )
    else:
        verdict = "idle"
        message = "Aucune tâche en file — lance wake-agents pour alimenter la queue."

    return {
        "verdict": verdict,
        "message": message,
        "academy": {
            "github_repo": target.github_repo,
            "current_level": progress.get("current_level"),
            "completed": progress.get("completed_exercises"),
            "total": progress.get("total_exercises"),
            "agent_ready": counts["agent-ready"],
            "in_pipeline": counts["in-pipeline"],
            "agent_failed": counts["agent-failed"],
            "slots_free": slots,
            "max_parallel": max_parallel,
            "repo_path_exists": repo_path_exists,
        },
    }


def wake_agents(
    *,
    retry_failed: bool = True,
    mark_ready_count: int | None = None,
    sync: bool = True,
    notify: bool = False,
) -> dict[str, Any]:
    """
    Full wake: sync progress, retry failed, queue next issues if idle.
    CEO one-shot — also called automatically after Academy merges.
    """
    from services.academy_issue_sync import run_academy_sync

    result: dict[str, Any] = {"success": True, "actions": []}

    if sync:
        try:
            result["sync"] = run_academy_sync()
        except Exception as exc:
            logger.warning("[AgentWake] academy sync failed: %s", exc)
            result["sync_error"] = str(exc)

    if retry_failed:
        retried = requeue_failed_academy(count=1)
        result["actions"].append({"retry_failed": retried})

    # Reset zombie in-pipeline labels before queueing — otherwise busy slots
    # stay leaked and queue_academy_if_idle reports pipeline_full forever.
    try:
        reset = reset_stuck_in_pipeline()
        if reset.get("reset_count"):
            result["actions"].append({"reset_stuck_in_pipeline": reset})
    except Exception as exc:
        logger.warning("[AgentWake] reset stuck in-pipeline failed: %s", exc)

    queued = queue_academy_if_idle(count=mark_ready_count)
    result["actions"].append({"queue": queued})

    status = get_pipeline_status()
    result["status"] = status
    result["summary"] = _format_wake_summary(status, queued, result["actions"])

    if notify:
        try:
            from services.orchestration import _notify

            _notify(f"⏰ Wake agents\n{result['summary']}")
        except Exception:
            pass

    logger.info("[AgentWake] %s", result["summary"])
    return result


def _format_wake_summary(
    status: dict[str, Any],
    queued: dict[str, Any],
    actions: list[dict[str, Any]],
) -> str:
    parts = [status.get("message", "")]
    n = int(queued.get("marked_count") or 0)
    if n:
        titles = ", ".join(f"#{m['number']}" for m in queued.get("marked", [])[:5])
        parts.append(f"→ {n} issue(s) mises en file ({titles}).")
    for action in actions:
        retry = action.get("retry_failed") or {}
        rn = int(retry.get("retried_count") or 0)
        if rn:
            parts.append(f"→ {rn} échec(s) relancé(s).")
    ac = status.get("academy") or {}
    if ac.get("completed") is not None:
        parts.append(
            f"Progression L{ac.get('current_level')}: "
            f"{ac.get('completed')}/{ac.get('total')} exercices."
        )
    return " ".join(p for p in parts if p)
