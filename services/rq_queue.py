"""RQ (Redis Queue) worker — background tasks for prod deploys."""

from __future__ import annotations

import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


def get_queue(name: str = "alnua_default"):
    """Return RQ Queue or None if Redis unavailable."""
    try:
        from rq import Queue
        from services.redis_client import get_redis

        conn = get_redis()
        if conn is None:
            return None
        return Queue(name, connection=conn)
    except ImportError:
        logger.warning("rq not installed — pip install rq redis")
        return None
    except Exception as exc:
        logger.warning("RQ queue unavailable: %s", exc)
        return None


def enqueue_task(fn: Callable[..., Any], *args: Any, job_timeout: int = 600, **kwargs: Any) -> str | None:
    """Enqueue background job; returns job_id or None (runs sync fallback)."""
    q = get_queue()
    if q is None:
        logger.debug("RQ fallback — running %s synchronously", fn.__name__)
        fn(*args, **kwargs)
        return None
    job = q.enqueue(fn, *args, **kwargs, job_timeout=job_timeout)
    return job.id


def job_backup_daily() -> None:
    """RQ job — daily backup."""
    from scripts.backup_daily import main
    main()


def job_deep_research(query: str, agent_id: str = "rnd_agent") -> dict[str, Any]:
    """RQ job — deep research pipeline."""
    from services.deep_research import run_deep_research
    return run_deep_research(query, rounds=2, agent_id=agent_id)


def register_default_jobs() -> None:
    """Document registered RQ job entrypoints for workers."""
    _JOBS = (job_backup_daily, job_deep_research)  # noqa: F841 — reference for worker discovery
