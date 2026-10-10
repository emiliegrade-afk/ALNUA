"""Gaming Academy → Wyrdheim production gate — compat wrapper (DEC-036).

Logic lives in the generic ``studio_academy_gate`` engine; check names are
unchanged (``success_rate_65``, ``n3_slice_complete``, ``roles_coverage_10``,
``canon_clean``, ``v2_prereq_configured``).
"""

from __future__ import annotations

from typing import Any

from services import studio_academy_gate as _gate
from services.academy_program_gaming import GAMING_PROGRAM


def evaluate_gate(*, persist: bool = True) -> dict[str, Any]:
    """Evaluate readiness checks and persist them into the progress file."""
    return _gate.evaluate_gate(GAMING_PROGRAM, persist=persist)
