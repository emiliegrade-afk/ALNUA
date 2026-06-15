"""Facades — single entry points for gradual migration (Phase 0 safety net)."""

from services.facades.briefing_facade import (
    fetch_coo_daily_briefing,
    fetch_operational_briefing_for_date,
    is_briefing_coo_section_enabled,
    is_briefing_unified_generate_enabled,
)
from services.facades.costs_facade import (
    get_daily_costs,
    get_monthly_costs,
    get_telegram_costs_report,
    get_weekly_costs,
    is_costs_shadow_compare_enabled,
    is_costs_unified_read_enabled,
)

__all__ = [
    "fetch_coo_daily_briefing",
    "fetch_operational_briefing_for_date",
    "get_daily_costs",
    "get_monthly_costs",
    "get_telegram_costs_report",
    "get_weekly_costs",
    "is_briefing_coo_section_enabled",
    "is_briefing_unified_generate_enabled",
    "is_costs_shadow_compare_enabled",
    "is_costs_unified_read_enabled",
]
