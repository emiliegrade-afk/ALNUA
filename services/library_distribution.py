"""Library distribution ledger — track Mem0 fanout + agent learning per entry.

Façade : siblings under ``services/library_distribution_*.py`` keep each module ≤ ~300 lines.
"""

from __future__ import annotations

from services.library_distribution_jobs import (  # noqa: F401 — re-export
    cancel_active_job,
    start_distribute_all_job,
    start_learn_pending_job,
    start_verify_all_job,
    verify_entry_in_mem0,
)
from services.library_distribution_status import (  # noqa: F401 — re-export
    expected_slots_for_entry,
    get_distribution_status,
)
from services.library_distribution_store import (  # noqa: F401 — re-export
    LEDGER_FILE,
    _load_ledger,
    begin_batch_mode,
    end_batch_mode,
    get_job,
    is_distributed,
    receipt_key,
    record_distributed,
    record_learned,
    record_verified,
)

__all__ = [
    "LEDGER_FILE",
    "_load_ledger",
    "begin_batch_mode",
    "cancel_active_job",
    "end_batch_mode",
    "expected_slots_for_entry",
    "get_distribution_status",
    "get_job",
    "is_distributed",
    "receipt_key",
    "record_distributed",
    "record_learned",
    "record_verified",
    "start_distribute_all_job",
    "start_learn_pending_job",
    "start_verify_all_job",
    "verify_entry_in_mem0",
]
