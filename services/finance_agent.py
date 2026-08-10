"""Finance agent — monthly aggregation + OpenRouter summary (facade)."""

from __future__ import annotations

from services.finance_agent_constants import (  # noqa: F401 — re-export
    CATEGORY_LABELS,
    EXPENSE_CATEGORIES,
    FINANCE_MODEL,
    INCOME_CATEGORIES,
    SYSTEM_PROMPT,
)
from services.finance_agent_dashboard import (  # noqa: F401 — re-export
    attach_project_names,
    build_dashboard,
    estimate_project,
    fetch_recurring_expenses,
)
from services.finance_agent_summary import (  # noqa: F401 — re-export
    generate_monthly_summary,
    get_or_generate_summary,
    get_summary_row,
)
from services.finance_agent_transactions import (  # noqa: F401 — re-export
    compute_totals,
    fetch_transactions,
    month_bounds,
    previous_month,
)

__all__ = [
    "CATEGORY_LABELS",
    "EXPENSE_CATEGORIES",
    "FINANCE_MODEL",
    "INCOME_CATEGORIES",
    "SYSTEM_PROMPT",
    "attach_project_names",
    "build_dashboard",
    "compute_totals",
    "estimate_project",
    "fetch_recurring_expenses",
    "fetch_transactions",
    "generate_monthly_summary",
    "get_or_generate_summary",
    "get_summary_row",
    "month_bounds",
    "previous_month",
]
