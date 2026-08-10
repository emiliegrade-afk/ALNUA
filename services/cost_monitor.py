"""
services/cost_monitor.py — Suivi coûts LLM en temps réel pour ALNUA (facade).

Usage:
    from services.cost_monitor import record_call, get_cost_report, get_monthly_summary
"""

from __future__ import annotations

from services.cost_monitor_pricing import (  # noqa: F401 — re-export
    MODEL_PRICING,
    CallRecord,
    compute_cost as _compute_cost,
)
from services.cost_monitor_reports import (  # noqa: F401 — re-export
    check_budget_alert,
    get_cost_report,
    get_monthly_summary,
    get_top_costs,
)
from services.cost_monitor_store import (  # noqa: F401 — re-export
    COST_LOG_PATH as _COST_LOG_PATH,
    _cost_log,
    _loaded,
    record_call,
)
from services.cost_monitor_ui import (  # noqa: F401 — re-export
    get_daily_costs,
    get_monthly_costs,
    get_weekly_costs,
)

__all__ = [
    "MODEL_PRICING",
    "CallRecord",
    "_COST_LOG_PATH",
    "_compute_cost",
    "_cost_log",
    "_loaded",
    "check_budget_alert",
    "get_cost_report",
    "get_daily_costs",
    "get_monthly_costs",
    "get_monthly_summary",
    "get_top_costs",
    "get_weekly_costs",
    "record_call",
]
