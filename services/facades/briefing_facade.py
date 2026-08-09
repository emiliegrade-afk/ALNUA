"""
Briefing facade — compose operational, COO, and orchestration paths without merging them.

Three call sites still exist in the wild; prefer this module for new code:

| Path | Module | Role |
|------|--------|------|
| Operational | `briefing_generator` via `fetch_operational_briefing_for_date` | Persisted Supabase daily ops brief |
| Executive COO | `daily_briefing` via `fetch_coo_daily_briefing` | Aria synthesis (trends/costs/events) |
| Agent method | `COOAgent.get_daily_briefing` | Legacy agent-facing wrapper used by dashboard/bots |

Phase 0: thin wrappers + feature flags. Do not collapse these into one pipeline
without an explicit product decision — they serve different consumers.
"""

from __future__ import annotations

from datetime import date
from typing import Any


def _settings() -> Any:
    from config.settings import get_settings

    return get_settings()


def is_briefing_coo_section_enabled() -> bool:
    """UI gate for the COO tab on /briefing (Phase 2)."""
    return _settings().briefing_coo_section_enabled


def is_briefing_unified_generate_enabled() -> bool:
    """When true, manual generate prefers orchestration/morning-run (Phase 2)."""
    return _settings().briefing_unified_generate


def is_admin_costs_page_enabled() -> bool:
    return _settings().admin_costs_page_enabled


def is_admin_events_page_enabled() -> bool:
    return _settings().admin_events_page_enabled


def is_admin_ab_test_page_enabled() -> bool:
    return _settings().admin_ab_test_page_enabled


def fetch_operational_briefing_for_date(
    db: Any,
    target_date: date,
) -> dict[str, Any] | None:
    """Operational briefing from Supabase (briefing_generator pipeline)."""
    from services.briefing_generator import get_briefing_for_date

    return get_briefing_for_date(db, target_date)


def fetch_coo_daily_briefing(
    *,
    context: str = "",
    include_trends: bool = True,
    include_costs: bool = True,
    include_events: bool = True,
) -> dict[str, Any]:
    """
    Executive COO brief (daily_briefing pipeline).

    Gated by briefing_coo_section_enabled for UI; API/orchestration may call directly.
    """
    from services.daily_briefing import run_daily_briefing

    return run_daily_briefing(
        context=context,
        include_trends=include_trends,
        include_costs=include_costs,
        include_events=include_events,
    )
