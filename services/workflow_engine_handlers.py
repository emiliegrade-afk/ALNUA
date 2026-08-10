"""Workflow engine — step handler registry."""

from __future__ import annotations

import logging
from typing import Any, Callable

from services.workflow_step_handlers_dossier import (
    _step_control_gaps,
    _step_generate_package,
    _step_mark_ready,
    _step_validate_committee,
    _step_validate_sections,
)
from services.workflow_step_handlers_ops import (
    _step_ceo_queue_reminder,
    _step_cost_snapshot,
    _step_ingest_beta_feedback,
    _step_ops_snapshot,
    _step_remediate_errors,
    _step_sav_ceo_pending,
    _step_scan_errors,
    _step_scan_registry,
    _step_start_investigation,
    _step_sync_product_kb,
    _step_watchdog_status,
    _step_weekly_briefing,
)
from services.workflow_step_handlers_ship import (
    _step_notify_shipped,
    _step_qa_readiness,
    _step_update_lifecycle,
    _step_validate_gaming_readiness,
    _step_validate_registry,
    _step_validate_registry_gaming,
    _step_validate_registry_robotics,
    _step_validate_robotics_readiness,
)

logger = logging.getLogger(__name__)

_STEP_HANDLERS: dict[str, Callable[..., dict[str, Any]]] = {
    "validate_sections": _step_validate_sections,
    "validate_committee": _step_validate_committee,
    "generate_package": _step_generate_package,
    "control_gaps": _step_control_gaps,
    "mark_ready": _step_mark_ready,
    "validate_registry": _step_validate_registry,
    "qa_readiness": _step_qa_readiness,
    "update_lifecycle": _step_update_lifecycle,
    "notify_shipped": _step_notify_shipped,
    "scan_registry": _step_scan_registry,
    "scan_errors": _step_scan_errors,
    "watchdog_status": _step_watchdog_status,
    "remediate_errors": _step_remediate_errors,
    "weekly_briefing": _step_weekly_briefing,
    "ops_snapshot": _step_ops_snapshot,
    "ceo_queue_reminder": _step_ceo_queue_reminder,
    "cost_snapshot": _step_cost_snapshot,
    "start_investigation": _step_start_investigation,
    "sync_product_kb": _step_sync_product_kb,
    "ingest_beta_feedback": _step_ingest_beta_feedback,
    "sav_ceo_pending": _step_sav_ceo_pending,
    "validate_registry_gaming": _step_validate_registry_gaming,
    "validate_registry_robotics": _step_validate_registry_robotics,
    "validate_gaming_readiness": _step_validate_gaming_readiness,
    "validate_robotics_readiness": _step_validate_robotics_readiness,
}


def register_extension_recipes() -> None:
    """Load Phase 30 validation recipes without inlining them here (BUG-004)."""
    try:
        from services.workflow_validation_recipes import register_validation_recipes

        register_validation_recipes()
    except Exception as exc:
        logger.warning("validation recipes not loaded: %s", exc)
