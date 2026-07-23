"""
services/daily_briefing.py — Briefing quotidien orchestré par Aria (COO).

Inspiré de morning-digest (⭐3.2k). Agrège en parallèle :
- Leaderboard compétition (qui performe ?)
- Tendances du jour (HN + Reddit + GitHub)
- Métriques coûts LLM (Rémi)
- Events récents (bus)
→ Aria (COO) synthétise en un brief structuré, actionnable.

Destiné à être déclenché automatiquement par n8n chaque matin.

Usage:
    from services.daily_briefing import run_daily_briefing

    brief = run_daily_briefing(context="Sprint 12 — sortie app prévue vendredi")
    # → dict avec sections : performance, trends, costs, events, coo_brief
"""
from __future__ import annotations

import concurrent.futures
import logging
import time
from datetime import datetime, timezone
from typing import Any

from config.agent_personas import persona_prompt_intro

logger = logging.getLogger(__name__)

_COO_BRIEF_SYSTEM = f"""{persona_prompt_intro("coo", role="COO")}. Tu reçois chaque matin un agrégat
de données opérationnelles et tu génères un brief exécutif concis et actionnable.
Ton brief oriente la journée d'Emilie — priorités, alertes, opportunités.
Réponds en JSON valide uniquement."""


# ---------------------------------------------------------------------------
# Collecteurs parallèles
# ---------------------------------------------------------------------------

def _collect_leaderboard() -> dict[str, Any]:
    try:
        from services.competition import get_leaderboard, get_scores
        board = get_leaderboard()
        scores = get_scores()
        return {
            "top_3": board[:3],
            "total_agents": len(board),
            "top_scorer": board[0].get("agent_id") if board else None,
            "total_points_today": sum(scores.values()),
        }
    except Exception as e:
        return {"error": str(e)}


def _collect_trends() -> dict[str, Any]:
    try:
        from services.trend_monitor import get_raw_trends
        items = get_raw_trends(
            sources=["hackernews", "github"],
            topics=[],
            limit=10,
        )
        return {"items_count": items.get("total", 0), "sample": items.get("items", [])[:5]}
    except Exception as e:
        return {"error": str(e)}


def _collect_costs() -> dict[str, Any]:
    try:
        from services.cost_monitor import get_cost_report, check_budget_alert
        report = get_cost_report(days=1)
        alert = check_budget_alert(daily_budget_usd=5.0)
        return {
            "today_usd": report.get("total_cost_usd", 0),
            "calls_today": report.get("total_calls", 0),
            "alert": alert.get("alert", False),
            "severity": alert.get("severity", "ok"),
            "most_expensive_agent": report.get("most_expensive_agent"),
        }
    except Exception as e:
        return {"error": str(e)}


def _collect_events() -> dict[str, Any]:
    try:
        from services.event_bus import get_recent_events, get_event_stats
        recent = get_recent_events(limit=20)
        stats = get_event_stats()
        return {
            "recent_count": len(recent),
            "recent": recent[:5],
            "top_event_types": list(stats.get("by_type", {}).keys())[:5],
        }
    except Exception as e:
        return {"error": str(e)}


def _collect_academy_gate() -> dict[str, Any]:
    try:
        from services.academy_gate import evaluate_academy_gate

        gate = evaluate_academy_gate(refresh_academy=False)
        return {
            "gate_open": gate.get("gate_open"),
            "readiness_pct": gate.get("readiness_pct"),
            "missing_critical": [
                c["label"]
                for c in (gate.get("criteria") or [])
                if c.get("critical") and not c.get("passed")
            ],
        }
    except Exception as e:
        return {"error": str(e)}


def _collect_memory_health() -> dict[str, Any]:
    """Vérifie si des agents ont besoin de compression mémoire."""
    try:
        from skills.skill_agent_learning import auto_compress_if_needed
        compressed = []
        for agent_id in ["coo", "dev_backend", "marketing", "content", "analyst_data"]:
            try:
                if auto_compress_if_needed(agent_id, threshold=15, blocking=False):
                    compressed.append(agent_id)
            except Exception:
                pass
        return {"agents_compressed": compressed, "checked": 5}
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Synthèse COO
# ---------------------------------------------------------------------------

def _coo_synthesize(data: dict[str, Any], context: str) -> dict[str, Any]:
    """Aria génère le brief exécutif à partir des données agrégées."""
    try:
        from agents.base import LLMClient, parse_json_response

        llm = LLMClient()
        date_str = datetime.now(timezone.utc).strftime("%A %d %B %Y")

        prompt = f"""Date : {date_str}
Contexte d'aujourd'hui : {context or "Aucun contexte particulier"}

DONNÉES OPÉRATIONNELLES :
{str(data)[:4000]}

Génère le brief exécutif quotidien avec :
- headline (string): phrase résumant la situation du jour en 1 ligne
- priority_1 (string): action #1 pour Emilie aujourd'hui
- priority_2 (string): action #2
- priority_3 (string): action #3
- alerts (list[string]): alertes critiques (budget, agents en échec, etc.)
- opportunities (list[string]): opportunités à saisir (trends, momentum, etc.)
- team_performance (string): résumé de la performance équipe en 1 phrase
- recommended_focus (string): sur quoi Emilie devrait concentrer 80% de son énergie aujourd'hui"""

        raw = llm.complete(_COO_BRIEF_SYSTEM, prompt, agent_id="coo", temperature=0.3)
        return parse_json_response(raw)
    except Exception as e:
        return {
            "headline": f"Brief généré avec erreurs partielle: {e}",
            "priority_1": "Vérifier les alertes coûts",
            "priority_2": "Vérifier le leaderboard",
            "priority_3": "Consulter les trends",
            "alerts": [], "opportunities": [], "team_performance": "", "recommended_focus": "",
        }


# ---------------------------------------------------------------------------
# Point d'entrée principal
# ---------------------------------------------------------------------------

def run_daily_briefing(
    context: str = "",
    include_trends: bool = True,
    include_costs: bool = True,
    include_events: bool = True,
) -> dict[str, Any]:
    """
    Génère le briefing quotidien complet.
    Collecte toutes les données en parallèle → COO synthétise.

    Endpoint: POST /services/briefing/daily
    """
    start = time.monotonic()
    logger.info("Daily briefing started")

    # Collecte parallèle
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            "leaderboard": executor.submit(_collect_leaderboard),
            "costs": executor.submit(_collect_costs) if include_costs else None,
            "events": executor.submit(_collect_events) if include_events else None,
            "memory_health": executor.submit(_collect_memory_health),
            "academy_gate": executor.submit(_collect_academy_gate),
        }
        if include_trends:
            futures["trends"] = executor.submit(_collect_trends)

        data = {
            key: future.result() if future else {}
            for key, future in futures.items()
        }

    # Synthèse COO
    coo_brief = _coo_synthesize(data, context)

    # Points compétition à Aria pour le brief
    try:
        from services.competition import add_points
        add_points("coo", "document_produced", note="Daily briefing")
    except Exception:
        pass

    duration_ms = int((time.monotonic() - start) * 1000)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    return {
        "date": date_str,
        "context": context,
        "duration_ms": duration_ms,
        "coo_brief": coo_brief,
        "raw_data": {
            "leaderboard": data.get("leaderboard", {}),
            "costs": data.get("costs", {}),
            "events": data.get("events", {}),
            "trends_collected": bool(data.get("trends")),
            "memory_health": data.get("memory_health", {}),
            "academy_gate": data.get("academy_gate", {}),
        },
    }


def run_quick_briefing(context: str = "") -> dict[str, Any]:
    """
    Version rapide du briefing — leaderboard + coûts uniquement, pas de trends.
    Endpoint: POST /services/briefing/quick
    """
    return run_daily_briefing(
        context=context,
        include_trends=False,
        include_events=False,
    )
