"""
Bureau library — research results stored per department, nothing discarded.

Each entry is tagged ``now`` (actionable today) or ``later`` (keep for future).
"""
from __future__ import annotations

from services.bureau_library_constants import (  # noqa: F401 — re-export
    AGENT_TO_BUREAU,
    BUREAU_LABELS,
    BureauId,
    LIBRARY_FILE,
    ROOT,
    Timing,
    VALID_BUREAUS,
)
from services.bureau_library_entries import (  # noqa: F401 — re-export
    add_entry,
    bureau_for_agent,
    get_bureaus_meta,
    list_entries,
)
from services.bureau_library_extract import _extract_entries_from_research  # noqa: F401 — re-export
from services.bureau_library_report import generate_ceo_report
from services.bureau_library_research import (  # noqa: F401 — re-export
    _notify_research_complete_impl as _notify_research_complete,
    run_bureau_research,
)
from services.bureau_library_store import (  # noqa: F401 — re-export
    _load_store,
    _save_store,
    _utc_now,
)

__all__ = [
    "AGENT_TO_BUREAU",
    "BUREAU_LABELS",
    "BureauId",
    "LIBRARY_FILE",
    "ROOT",
    "Timing",
    "VALID_BUREAUS",
    "_extract_entries_from_research",
    "_notify_research_complete",
    "_load_store",
    "_save_store",
    "_utc_now",
    "add_entry",
    "bureau_for_agent",
    "generate_ceo_report",
    "get_bureaus_meta",
    "list_entries",
    "run_bureau_research",
]
