"""
skill_model_usage.py

Récupère les coûts LLM depuis OpenRouter et les stocke dans Supabase.
Génère des rapports par agent pour le brief matinal COO.

Table Supabase requise :
CREATE TABLE agent_costs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    agent_name TEXT NOT NULL,
    model TEXT NOT NULL,
    tokens_input INTEGER DEFAULT 0,
    tokens_output INTEGER DEFAULT 0,
    cost_usd NUMERIC(10,6) DEFAULT 0,
    task_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

Variables d'env :
- OPENROUTER_API_KEY
- SUPABASE_URL
- SUPABASE_KEY
"""

import logging
from datetime import date, datetime

logger = logging.getLogger(__name__)


def log_usage(
    agent_name: str,
    model: str,
    tokens_in: int,
    tokens_out: int,
    cost_usd: float,
    task_id: str | None = None,
) -> None:
    """
    Enregistre une utilisation LLM dans Supabase.
    À appeler après chaque réponse LLM dans les agents.
    """
    from database.supabase_client import get_supabase

    db = get_supabase()
    db.table("agent_costs").insert(
        {
            "agent_name": agent_name,
            "model": model,
            "tokens_input": tokens_in,
            "tokens_output": tokens_out,
            "cost_usd": cost_usd,
            "task_id": task_id,
        }
    ).execute()


def get_daily_costs(target_date: date | None = None) -> dict:
    """
    Retourne les coûts du jour (ou d'une date donnée) groupés par agent.

    Returns:
        {
            "date": "2026-06-11",
            "total_usd": 0.042,
            "by_agent": {
                "COO": {"total_usd": 0.01, "calls": 5},
                "DevApp": {"total_usd": 0.032, "calls": 2},
                ...
            }
        }

    Si Supabase est indisponible ou la table absente, retourne by_agent vide
    (voir database/agent_costs_migration.sql pour créer la table).
    """
    if target_date is None:
        target_date = date.today()

    empty = {
        "date": target_date.isoformat(),
        "total_usd": 0.0,
        "by_agent": {},
    }

    try:
        from database.supabase_client import get_supabase

        db = get_supabase()
        start = datetime.combine(target_date, datetime.min.time()).isoformat()
        end = datetime.combine(target_date, datetime.max.time()).isoformat()

        rows = (
            db.table("agent_costs")
            .select("agent_name, cost_usd, tokens_input, tokens_output")
            .gte("created_at", start)
            .lte("created_at", end)
            .execute()
            .data
        )
    except Exception as exc:
        logger.warning(
            "[ModelUsage] get_daily_costs indisponible (%s) — "
            "exécuter database/agent_costs_migration.sql si besoin",
            exc,
        )
        return empty

    by_agent: dict[str, dict] = {}
    total = 0.0
    for row in rows or []:
        name = row["agent_name"]
        cost = float(row["cost_usd"])
        total += cost
        if name not in by_agent:
            by_agent[name] = {
                "total_usd": 0.0,
                "calls": 0,
                "tokens_in": 0,
                "tokens_out": 0,
            }
        by_agent[name]["total_usd"] = round(by_agent[name]["total_usd"] + cost, 6)
        by_agent[name]["calls"] += 1
        by_agent[name]["tokens_in"] += row.get("tokens_input", 0)
        by_agent[name]["tokens_out"] += row.get("tokens_output", 0)

    return {
        "date": target_date.isoformat(),
        "total_usd": round(total, 4),
        "by_agent": by_agent,
    }


def get_monthly_costs() -> dict:
    """Retourne les coûts du mois en cours."""
    today = date.today()
    first_day = today.replace(day=1)

    from database.supabase_client import get_supabase

    db = get_supabase()

    rows = (
        db.table("agent_costs")
        .select("agent_name, cost_usd")
        .gte("created_at", first_day.isoformat())
        .execute()
        .data
    )

    total = sum(float(r["cost_usd"]) for r in (rows or []))
    by_agent: dict[str, float] = {}
    for row in rows or []:
        name = row["agent_name"]
        by_agent[name] = by_agent.get(name, 0.0) + float(row["cost_usd"])

    return {
        "month": today.strftime("%B %Y"),
        "total_usd": round(total, 4),
        "by_agent": {k: round(v, 4) for k, v in by_agent.items()},
    }


def get_weekly_costs() -> dict:
    """
    Retourne les coûts des 7 derniers jours groupés par jour et par agent.

    Returns:
        {
            "total_usd": 0.12,
            "by_day": [
                {"date": "04/06", "COO": 0.01, "DevApp": 0.02, ...},
                ...
            ]
        }
    """
    from datetime import timedelta

    from database.supabase_client import get_supabase

    db = get_supabase()
    today = date.today()
    start = today - timedelta(days=6)

    rows = (
        db.table("agent_costs")
        .select("agent_name, cost_usd, created_at")
        .gte("created_at", start.isoformat())
        .execute()
        .data
    )

    agent_names = {
        "coo_agent": "COO",
        "dev_app": "DevApp",
        "game_director": "GameDirector",
        "dev_gaming": "DevGaming",
        "hardware": "Hardware",
        "embedded": "EmbeddedDev",
        "marketing": "Marketing",
        "pm_agent": "PM",
    }

    by_date: dict[str, dict[str, float]] = {}
    total = 0.0

    for row in rows or []:
        created = row.get("created_at", "")[:10]
        if not created:
            continue
        day_key = created
        raw_name = row["agent_name"]
        agent = agent_names.get(raw_name, raw_name)
        cost = float(row["cost_usd"])
        total += cost
        if day_key not in by_date:
            by_date[day_key] = {}
        by_date[day_key][agent] = round(by_date[day_key].get(agent, 0.0) + cost, 6)

    by_day: list[dict] = []
    for i in range(7):
        d = start + timedelta(days=i)
        key = d.isoformat()
        label = d.strftime("%d/%m")
        entry: dict = {"date": label}
        for agent, cost in by_date.get(key, {}).items():
            entry[agent] = round(cost, 4)
        by_day.append(entry)

    return {"total_usd": round(total, 4), "by_day": by_day}


def format_costs_report(period: str = "day") -> str:
    """
    Formate un rapport de coûts lisible pour Telegram.
    period: "day" ou "month"
    """
    if period == "month":
        data = get_monthly_costs()
        header = f"💰 **Coûts LLM — {data['month']}**"
    else:
        data = get_daily_costs()
        header = f"💰 **Coûts LLM — aujourd'hui ({data['date']})**"

    lines = [header, f"**Total : ${data['total_usd']}**", ""]

    if "by_agent" in data:
        for agent, info in sorted(
            data["by_agent"].items(),
            key=lambda x: x[1] if isinstance(x[1], float) else x[1].get("total_usd", 0),
            reverse=True,
        ):
            cost = info if isinstance(info, float) else info.get("total_usd", 0)
            calls = "" if isinstance(info, float) else f" ({info.get('calls', '?')} appels)"
            lines.append(f"• {agent} : ${cost:.4f}{calls}")

    return "\n".join(lines)
