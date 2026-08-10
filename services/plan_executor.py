"""
services/plan_executor.py — Exécuteur autonome de plans COO ALNUA (facade).

Usage:
    from services.plan_executor import run_coo_plan, execute_plan, ExecutionPlan
"""

from __future__ import annotations

from services.plan_executor_models import (  # noqa: F401 — re-export
    ExecutionPlan,
    ExecutionStep,
    StepResult,
)
from services.plan_executor_parser import parse_coo_plan  # noqa: F401 — re-export
from services.plan_executor_run import execute_plan, run_coo_plan  # noqa: F401 — re-export

__all__ = [
    "ExecutionPlan",
    "ExecutionStep",
    "StepResult",
    "execute_plan",
    "parse_coo_plan",
    "run_coo_plan",
]
