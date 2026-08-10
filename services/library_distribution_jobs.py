"""Library distribution — background jobs (distribute, learn, verify)."""

from __future__ import annotations

import logging
import threading
from typing import Any

from services.library_distribution_store import (
    _active_job_snapshot,
    _create_job,
    _load_ledger,
    _update_job,
    _utc_now,
    end_batch_mode,
    get_job,
    record_verified,
)

logger = logging.getLogger(__name__)


def cancel_active_job() -> dict[str, Any]:
    from services.library_distribution_runners import set_job_cancelled

    ledger = _load_ledger()
    active = _active_job_snapshot(ledger)
    if not active:
        return {"success": False, "message": "Aucun job en cours."}
    set_job_cancelled(True)
    _update_job(
        active["id"],
        status="failed",
        finished_at=_utc_now(),
        message="Annulé par l'utilisateur.",
    )
    end_batch_mode()
    return {"success": True, "message": "Job annulé.", "job_id": active["id"]}


def verify_entry_in_mem0(entry: dict[str, Any], agent_id: str) -> bool:
    """Check whether a library entry actually landed in Mem0 for an agent.

    Mem0's search is semantic (vector nearest-neighbor), so querying with the
    entry's own UUID — a string with no semantic content — almost never
    surfaces the right memory once an agent has more than a handful of
    entries. Querying with the entry's real title instead reuses the same
    text that was embedded at write time (see `_memory_line`), which is what
    actually gives the vector search something to match on.

    Checks for either marker: `[library:<id>]` (the raw source pushed at
    distribute time) or `[learned:<id>]` (the distilled lesson pushed at
    learn time — added after this fix, so older entries learned before it
    only carry the first marker). Either one found means real content for
    this entry actually reached Mem0 for this agent, not just that the
    write call didn't throw.
    """
    entry_id = str(entry.get("id") or "")
    query = str(entry.get("title") or "").strip() or f"library:{entry_id}"
    try:
        from skills.skill_mem0 import recall

        snippet = recall(query, agent_id=agent_id)
        snippet_lower = snippet.lower() if snippet else ""
        found = bool(snippet) and (
            f"library:{entry_id}".lower() in snippet_lower
            or f"learned:{entry_id}".lower() in snippet_lower
        )
        record_verified(entry_id, agent_id, mem0_found=found)
        return found
    except Exception as exc:
        logger.debug("verify_entry_in_mem0 failed %s/%s: %s", entry_id, agent_id, exc)
        record_verified(entry_id, agent_id, mem0_found=False)
        return False


def _load_all_entries() -> list[dict[str, Any]]:
    from services.library_distribution_status import _load_all_entries as _load

    return _load()


def start_distribute_all_job(
    *,
    skip_distributed: bool = True,
    timing: str | None = None,
    run_learning: bool = True,
) -> dict[str, Any]:
    from services.library_distribution_runners import run_distribute_all_job

    entries = _load_all_entries()
    if timing in ("now", "later"):
        entries = [e for e in entries if e.get("timing") == timing]

    if _active_job_snapshot(_load_ledger()):
        return {
            "success": False,
            "message": "Un job est déjà en cours — attends la fin ou rafraîchis le statut.",
        }

    job_id = _create_job("distribute_all", len(entries))
    threading.Thread(
        target=run_distribute_all_job,
        kwargs={
            "job_id": job_id,
            "skip_distributed": skip_distributed,
            "timing": timing,
            "run_learning": run_learning,
        },
        daemon=True,
    ).start()
    return {
        "success": True,
        "job_id": job_id,
        "status": get_job(job_id),
        "message": f"Distribution lancée — {len(entries)} fiche(s) en file.",
    }


def start_learn_pending_job() -> dict[str, Any]:
    from services.library_distribution_runners import run_learn_pending_job

    if _active_job_snapshot(_load_ledger()):
        return {"success": False, "message": "Un job est déjà en cours."}

    job_id = _create_job("learn_pending", 0)
    threading.Thread(target=run_learn_pending_job, args=(job_id,), daemon=True).start()
    return {
        "success": True,
        "job_id": job_id,
        "status": get_job(job_id),
        "message": "Apprentissage des fiches distribuées lancé.",
    }


def start_verify_all_job() -> dict[str, Any]:
    from services.library_distribution_runners import run_verify_all_job

    if _active_job_snapshot(_load_ledger()):
        return {"success": False, "message": "Un job est déjà en cours."}

    job_id = _create_job("verify_all", 0)
    threading.Thread(target=run_verify_all_job, args=(job_id,), daemon=True).start()
    return {
        "success": True,
        "job_id": job_id,
        "status": get_job(job_id),
        "message": "Vérification Mem0 lancée.",
    }
