"""
Costs facade — single read path via cost_monitor JSON.

Legacy Supabase skill_model_usage writes are retired (LLMClient → cost_monitor only).
"""

from __future__ import annotations

from datetime import date
from typing import Any


def get_daily_costs(target_date: date | None = None) -> dict[str, Any]:
    """Hub UI + lobby + Telegram — cost_monitor primary."""
    from services import cost_monitor

    return cost_monitor.get_daily_costs(target_date)


def get_monthly_costs() -> dict[str, Any]:
    """Lobby month widget / Telegram month report."""
    from services import cost_monitor

    return cost_monitor.get_monthly_costs()


def get_weekly_costs() -> dict[str, Any]:
    """Hub dashboard week chart."""
    from services import cost_monitor

    return cost_monitor.get_weekly_costs()


def get_telegram_costs_report(period: str = "day") -> str:
    """Telegram /costs — formatted from cost_monitor."""
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
        if isinstance(info, dict):
            usd = info.get("total_usd", 0)
            calls = info.get("calls", "?")
            lines.append(f"• `{agent}` — ${usd} ({calls} calls)")
        else:
            lines.append(f"• `{agent}` — ${info}")
    return "\n".join(lines)


# Back-compat alias used by CrewAI tools / older imports
format_costs_report = get_telegram_costs_report
