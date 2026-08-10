"""Finance estimates for R&D dossiers — solo founder + AI agents + real ALNUA data.

Façade : siblings under ``services/rnd_finance_*.py`` keep each module ≤ ~300 lines.
"""

from __future__ import annotations

from services.rnd_finance_estimate_core import estimate_rnd_project  # noqa: F401 — re-export
from services.rnd_finance_helpers import (  # noqa: F401 — re-export
    is_stale_finance,
    normalize_finance_for_display,
)
from services.rnd_finance_markdown import finance_json_to_markdown  # noqa: F401 — re-export

__all__ = [
    "estimate_rnd_project",
    "finance_json_to_markdown",
    "is_stale_finance",
    "normalize_finance_for_display",
]
