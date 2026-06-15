"""
Costs facade — routes all cost reads through one module.

Phase 0: default behaviour unchanged (cost_monitor JSON is primary).
Shadow mode logs deltas vs Supabase legacy without affecting consumers.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

logger = logging.getLogger(__name__)

_SHADOW_DELTA_THRESHOLD_USD = 0.01
_SHADOW_DELTA_RATIO = 0.05


def _settings() -> Any:
    from config.settings import get_settings

    return get_settings()


def _shadow_compare(primary: dict[str, Any], legacy: dict[str, Any], *, label: str) -> None:
    """Log when JSON store and Supabase legacy totals diverge (no UI impact)."""
    if not _settings().costs_shadow_compare:
        return

    primary_total = float(primary.get("total_usd", 0.0))
    legacy_total = float(legacy.get("total_usd", 0.0))
    delta = abs(primary_total - legacy_total)
    denom = max(primary_total, legacy_total, 1e-9)
    ratio = delta / denom

    if delta <= _SHADOW_DELTA_THRESHOLD_USD and ratio <= _SHADOW_DELTA_RATIO:
        return

    logger.info(
        "[costs_facade] shadow %s — primary=$%.4f legacy=$%.4f delta=$%.4f (%.1f%%)",
        label,
        primary_total,
        legacy_total,
        delta,
        ratio * 100,
    )


def get_daily_costs(target_date: date | None = None) -> dict[str, Any]:
    """Hub UI + lobby — cost_monitor primary; optional Supabase shadow."""
    from services import cost_monitor

    primary = cost_monitor.get_daily_costs(target_date)
    if _settings().costs_unified_read:
        return primary

    try:
        from skills import skill_model_usage

        legacy = skill_model_usage.get_daily_costs(target_date)
        _shadow_compare(primary, legacy, label="daily")
    except Exception:
        pass

    return primary


def get_monthly_costs() -> dict[str, Any]:
    """Lobby month widget — same JSON shape as before."""
    from services import cost_monitor

    primary = cost_monitor.get_monthly_costs()
    if _settings().costs_unified_read:
        return primary

    try:
        from skills import skill_model_usage

        legacy = skill_model_usage.get_monthly_costs()
        _shadow_compare(primary, legacy, label="monthly")
    except Exception:
        pass

    return primary


def get_weekly_costs() -> dict[str, Any]:
    """Hub dashboard week chart."""
    from services import cost_monitor

    return cost_monitor.get_weekly_costs()


def get_telegram_costs_report(period: str = "day") -> str:
    """
    Telegram /costs — uses facade reads when unified; legacy formatter otherwise.

    Phase 0: still delegates to skill_model_usage formatter (Supabase path).
    Phase 1+: flip via costs_unified_read without touching the bot.
    """
    if not _settings().costs_unified_read:
        from skills.skill_model_usage import format_costs_report

        return format_costs_report(period)

    if period == "month":
        data = get_monthly_costs()
        header = f"💰 **Coûts LLM — {data['month']}**"
    else:
        data = get_daily_costs()
        header = f"💰 **Coûts LLM — aujourd'hui ({data['date']})**"

    lines = [header, f"**Total : ${data['total_usd']}**", ""]
    by_agent = data.get("by_agent") or {}
    for agent, info in sorted(
        by_agent.items(),
        key=lambda x: x[1] if isinstance(x[1], float) else x[1].get("total_usd", 0),
        reverse=True,
    ):
        cost = info if isinstance(info, float) else info.get("total_usd", 0)
        calls = "" if isinstance(info, float) else f" ({info.get('calls', '?')} appels)"
        lines.append(f"• {agent} : ${cost:.4f}{calls}")

    return "\n".join(lines)


def is_costs_unified_read_enabled() -> bool:
    """When true, all cost reads use cost_monitor JSON only."""
    return _settings().costs_unified_read


def is_costs_shadow_compare_enabled() -> bool:
    """When true, log deltas between cost_monitor and Supabase legacy reads."""
    return _settings().costs_shadow_compare
