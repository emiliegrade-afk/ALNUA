"""
services/orchestration.py — Chaînes agent→agent pour n8n et l'orchestration autonome.

Façade — implémentations dans orchestration_*.py.
"""

from __future__ import annotations

from database.supabase_client import get_supabase  # noqa: F401 — patch target in tests

from services.orchestration_academy import (
    run_academy_gate_orchestration,
    run_academy_poll_orchestration,
    run_academy_sprint_orchestration,
)
from services.orchestration_catalog import WORKFLOW_CATALOG
from services.orchestration_chains import (
    run_content_sprint,
    run_github_pr_review,
    run_spec_qa_chain,
    run_welcome_sequence,
)
from services.orchestration_helpers import (
    MORNING_COO_PROMPT,
    WEEKLY_COO_PROMPT,
    _log_run,
    _notify,
    _resolve_project_id,
)
from services.orchestration_morning import (
    run_morning_orchestration,
    run_secretary_morning_notify,
)
from services.orchestration_ops import (
    run_prd_decompose_orchestration,
    run_security_ingest_orchestration,
    run_sentry_ingest_orchestration,
)

__all__ = [
    "MORNING_COO_PROMPT",
    "WEEKLY_COO_PROMPT",
    "WORKFLOW_CATALOG",
    "_log_run",
    "_notify",
    "_resolve_project_id",
    "get_supabase",
    "run_academy_gate_orchestration",
    "run_academy_poll_orchestration",
    "run_academy_sprint_orchestration",
    "run_content_sprint",
    "run_github_pr_review",
    "run_morning_orchestration",
    "run_prd_decompose_orchestration",
    "run_secretary_morning_notify",
    "run_security_ingest_orchestration",
    "run_sentry_ingest_orchestration",
    "run_spec_qa_chain",
    "run_welcome_sequence",
]
