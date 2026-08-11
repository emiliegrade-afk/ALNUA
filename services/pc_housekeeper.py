"""PC housekeeper façade — organize Desktop/Documents with quarantine (DEC-030)."""

from __future__ import annotations

from services.pc_housekeeper_actions import (
    apply_proposals,
    purge_quarantine,
    quarantine_for_delete,
)
from services.pc_housekeeper_core import (
    list_quarantine,
    propose_organization,
    resolve_roots,
    scan_clutter,
    set_autonomy,
    status,
)

__all__ = [
    "apply_proposals",
    "list_quarantine",
    "propose_organization",
    "purge_quarantine",
    "quarantine_for_delete",
    "resolve_roots",
    "scan_clutter",
    "set_autonomy",
    "status",
]
