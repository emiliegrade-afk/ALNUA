"""Library distribution — background job workers (distribute, learn, verify)."""

from __future__ import annotations

import logging
import time
from typing import Any

from services.library_distribution_status import expected_slots_for_entry, get_distribution_status
from services.library_distribution_store import (
    _create_job,
    _load_ledger,
    _update_job,
    _utc_now,
    begin_batch_mode,
    end_batch_mode,
    receipt_key,
)

logger = logging.getLogger(__name__)

_CANCEL_ACTIVE_JOB = False


def job_cancelled() -> bool:
    return _CANCEL_ACTIVE_JOB


def set_job_cancelled(value: bool) -> None:
    global _CANCEL_ACTIVE_JOB
    _CANCEL_ACTIVE_JOB = value


def _load_all_entries() -> list[dict[str, Any]]:
    from services.library_distribution_status import _load_all_entries as _load

    return _load()


def run_distribute_all_job(
    job_id: str,
    *,
    skip_distributed: bool,
    timing: str | None,
    run_learning: bool,
) -> None:
    global _CANCEL_ACTIVE_JOB
    _CANCEL_ACTIVE_JOB = False
    from services.team_enrichment import fanout_library_entry

    entries = _load_all_entries()
    if timing in ("now", "later"):
        entries = [e for e in entries if e.get("timing") == timing]

    _update_job(job_id, status="running", total=len(entries), message="Distribution en cours…")
    distributed_count = 0
    learned_count = 0
    errors = 0

    begin_batch_mode()
    try:
        for i, entry in enumerate(entries):
            if job_cancelled():
                break
            entry_id = str(entry.get("id") or "")
            try:
                agents = fanout_library_entry(
                    entry,
                    distill_lessons=False,
                    skip_if_distributed=skip_distributed,
                )
                distributed_count += len(agents)
            except Exception as exc:
                errors += 1
                logger.debug("distribute entry %s failed: %s", entry_id, exc)

            if (i + 1) % 25 == 0 or i + 1 == len(entries):
                _update_job(
                    job_id,
                    processed=i + 1,
                    distributed=distributed_count,
                    learned=learned_count,
                    errors=errors,
                    message=f"{i + 1}/{len(entries)} fiches traitées",
                )
                get_distribution_status(force=True)
                time.sleep(0.05)
    finally:
        end_batch_mode()

    if job_cancelled():
        return

    _update_job(
        job_id,
        status="completed",
        processed=len(entries),
        distributed=distributed_count,
        learned=learned_count,
        errors=errors,
        finished_at=_utc_now(),
        message=(
            f"Distribution terminée — {distributed_count} diffusion(s) Mem0, "
            f"{errors} erreur(s)."
        ),
    )
    get_distribution_status(force=True)

    if run_learning and distributed_count > 0:
        import threading

        learn_id = _create_job("learn_pending", 0)
        threading.Thread(
            target=run_learn_pending_job,
            args=(learn_id,),
            daemon=True,
        ).start()


def run_learn_pending_job(job_id: str) -> None:
    from services.team_enrichment import distill_library_entry_for_agent

    entries = _load_all_entries()
    ledger = _load_ledger()
    receipts = ledger.get("receipts", {})

    pending: list[tuple[dict[str, Any], str]] = []
    for entry in entries:
        entry_id = str(entry.get("id") or "")
        for agent_id in expected_slots_for_entry(entry):
            row = receipts.get(receipt_key(entry_id, agent_id), {})
            if row.get("distributed_at") and not row.get("learned_at"):
                pending.append((entry, agent_id))

    _update_job(
        job_id,
        status="running",
        total=len(pending),
        message="Apprentissage des fiches distribuées…",
    )
    learned_count = 0
    errors = 0

    for i, (entry, agent_id) in enumerate(pending):
        try:
            if distill_library_entry_for_agent(entry, agent_id, blocking=True):
                learned_count += 1
        except Exception as exc:
            errors += 1
            logger.debug("learn pending failed: %s", exc)

        if (i + 1) % 10 == 0 or i + 1 == len(pending):
            _update_job(
                job_id,
                processed=i + 1,
                learned=learned_count,
                errors=errors,
                message=f"{i + 1}/{len(pending)} apprentissages",
            )

    _update_job(
        job_id,
        status="completed",
        processed=len(pending),
        learned=learned_count,
        errors=errors,
        finished_at=_utc_now(),
        message=f"Terminé — {learned_count} leçon(s) distillée(s).",
    )


def run_verify_all_job(job_id: str) -> None:
    from services.library_distribution_jobs import verify_entry_in_mem0

    entries = _load_all_entries()
    ledger = _load_ledger()
    receipts = ledger.get("receipts", {})

    pairs: list[tuple[dict[str, Any], str]] = []
    for entry in entries:
        entry_id = str(entry.get("id") or "")
        for agent_id in expected_slots_for_entry(entry):
            row = receipts.get(receipt_key(entry_id, agent_id), {})
            if row.get("distributed_at"):
                pairs.append((entry, agent_id))

    _update_job(
        job_id,
        status="running",
        total=len(pairs),
        message="Vérification Mem0…",
    )
    verified = 0
    confirmed = 0
    errors = 0

    for i, (entry, agent_id) in enumerate(pairs):
        try:
            if verify_entry_in_mem0(entry, agent_id):
                confirmed += 1
            verified += 1
        except Exception:
            errors += 1

        if (i + 1) % 50 == 0 or i + 1 == len(pairs):
            _update_job(
                job_id,
                processed=i + 1,
                verified=verified,
                distributed=confirmed,
                errors=errors,
                message=f"{i + 1}/{len(pairs)} vérifications",
            )

    _update_job(
        job_id,
        status="completed",
        processed=len(pairs),
        verified=verified,
        distributed=confirmed,
        errors=errors,
        finished_at=_utc_now(),
        message=f"Terminé — {confirmed}/{len(pairs)} confirmé(s) dans Mem0.",
    )
