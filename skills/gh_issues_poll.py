"""GitHub Issues — async polling loop with bounded parallelism."""

from __future__ import annotations

import asyncio
import logging

import httpx

from skills.gh_issues_client import RATE_LIMIT_BACKOFF
from skills.gh_issues_fetch import list_ready_issues
from skills.gh_issues_process import process_issue

logger = logging.getLogger(__name__)

POLL_INTERVAL = 60  # secondes entre chaque vérification

_issue_semaphore: asyncio.Semaphore | None = None
_repo_semaphores: dict[str, asyncio.Semaphore] = {}


def _issue_processing_semaphore() -> asyncio.Semaphore:
    global _issue_semaphore
    if _issue_semaphore is None:
        from services.coding_pipeline import get_coding_config

        limit = get_coding_config().max_parallel
        _issue_semaphore = asyncio.Semaphore(limit)
        logger.info("[GHIssues] Parallélisme max issues : %s", limit)
    return _issue_semaphore


def _repo_processing_semaphore(slug: str) -> asyncio.Semaphore:
    """One coding pipeline per target repo at a time (BUG-032).

    File-level locks make same-repo parallelism useless AND harmful: two
    coding loops on the same working tree collide on shared files
    (LockBusyError on app/(tabs)/_layout.tsx, seen repeatedly in prod) and
    double the CPU burst inside the API process (health-check flap).
    Different repos still run concurrently, bounded by the global semaphore.
    Lazily created per slug — safe in the single-threaded event loop."""
    if slug not in _repo_semaphores:
        _repo_semaphores[slug] = asyncio.Semaphore(1)
    return _repo_semaphores[slug]


async def _process_issue_bounded(
    issue: dict,
    repo_path: str | None,
    telegram_notify_fn=None,
) -> None:
    repo_slug = str(issue.get("_repo_slug") or "default")
    async with _issue_processing_semaphore(), _repo_processing_semaphore(repo_slug):
        try:
            await asyncio.to_thread(process_issue, issue, repo_path, telegram_notify_fn)
        except Exception:
            logger.exception(
                "[GHIssues] Issue #%s crash (isole — Hub continue)",
                issue.get("number"),
            )


def _task_done_callback(task: asyncio.Task) -> None:
    try:
        exc = task.exception()
        if exc is not None:
            logger.error("[GHIssues] Task background echouee: %s", exc)
    except asyncio.CancelledError:
        pass
    except Exception as exc:
        logger.warning("[GHIssues] Task callback: %s", exc)


async def poll_issues_loop(telegram_notify_fn=None):
    """
    Boucle de polling asynchrone. À lancer en background task FastAPI.
    Vérifie toutes les POLL_INTERVAL secondes sur tous les repos configurés.
    """
    logger.info("[GHIssues] Démarrage du polling GitHub Issues (multi-repo)...")
    cycle = 0
    while True:
        cycle += 1
        try:
            issues = list_ready_issues()
            if issues:
                logger.info("[GHIssues] %s issue(s) trouvée(s)", len(issues))
                for issue in issues:
                    repo_path = issue.get("_repo_path")
                    task = asyncio.create_task(
                        _process_issue_bounded(issue, repo_path, telegram_notify_fn)
                    )
                    task.add_done_callback(_task_done_callback)
            else:
                _idle_cycle(cycle)
        except httpx.HTTPStatusError as exc:
            if exc.response is not None and exc.response.status_code in (403, 429):
                retry_after = int(
                    exc.response.headers.get("Retry-After", RATE_LIMIT_BACKOFF)
                )
                logger.warning(
                    "[GHIssues] Rate limit — pause %ss avant prochain poll",
                    retry_after,
                )
                await asyncio.sleep(retry_after)
                continue
            logger.error("[GHIssues] Erreur HTTP polling : %s", exc)
        except Exception as exc:
            logger.error("[GHIssues] Erreur polling : %s", exc)

        await asyncio.sleep(POLL_INTERVAL)


def _idle_cycle(cycle: int) -> None:
    logger.debug("[GHIssues] Aucune issue à traiter")
    try:
        from services.agent_wake import queue_academy_if_idle

        wake = queue_academy_if_idle()
        if wake.get("marked_count"):
            logger.info(
                "[GHIssues] Auto-wake idle pipeline: %s",
                wake.get("marked"),
            )
    except Exception as exc:
        logger.debug("[GHIssues] Auto-wake skipped: %s", exc)

    if cycle % 10 == 0:
        try:
            from services.orchestration import run_academy_poll_orchestration

            run_academy_poll_orchestration(notify=False, mark_ready_count=1)
            logger.info("[GHIssues] Academy sync cycle (idle backup)")
        except Exception as exc:
            logger.debug("[GHIssues] Academy sync backup skipped: %s", exc)
