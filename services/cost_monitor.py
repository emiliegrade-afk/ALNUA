"""
services/cost_monitor.py — Suivi coûts LLM en temps réel pour ALNUA.

Inspiré de llm-cost-tracker. Track tokens × prix par modèle/agent.
Rémi (controller) reçoit les alertes. Jules (accounting) les rapports mensuels.

Usage:
    from services.cost_monitor import record_call, get_cost_report, get_monthly_summary

    # Enregistrer un appel LLM (appelé automatiquement par LLMClient si activé)
    record_call(agent_id="dev_backend", model="google/gemini-flash-1.5",
                prompt_tokens=1200, completion_tokens=400)

    # Rapport
    report = get_cost_report(agent_id="dev_backend", days=7)
    alert = check_budget_alert(daily_budget_usd=5.0)
"""
from __future__ import annotations

import json
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timezone, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prix par modèle (USD / 1M tokens) — mis à jour manuellement
# ---------------------------------------------------------------------------
MODEL_PRICING: dict[str, dict[str, float]] = {
    # Format: { input_per_1m, output_per_1m }
    "google/gemini-flash-1.5":          {"input": 0.075, "output": 0.30},
    "google/gemini-2.0-flash-001":      {"input": 0.10,  "output": 0.40},
    "anthropic/claude-haiku-4-5":       {"input": 0.80,  "output": 4.00},
    "anthropic/claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.00},
    "anthropic/claude-sonnet-4-5":      {"input": 3.00,  "output": 15.00},
    "anthropic/claude-opus-4":          {"input": 15.00, "output": 75.00},
    "openai/gpt-4o-mini":               {"input": 0.15,  "output": 0.60},
    "openai/gpt-4o":                    {"input": 2.50,  "output": 10.00},
    "mistralai/mistral-7b-instruct":    {"input": 0.06,  "output": 0.06},
    # Fallback
    "default":                          {"input": 1.00,  "output": 3.00},
}

# ---------------------------------------------------------------------------
# Store en mémoire + persistance JSON
# ---------------------------------------------------------------------------

_COST_LOG_PATH = Path(__file__).parent.parent / "data" / "cost_log.json"
_cost_log: list[dict[str, Any]] = []
_loaded = False


def _ensure_loaded() -> None:
    global _cost_log, _loaded
    if _loaded:
        return
    _COST_LOG_PATH.parent.mkdir(exist_ok=True)
    if _COST_LOG_PATH.exists():
        try:
            _cost_log = json.loads(_COST_LOG_PATH.read_text())
        except Exception:
            _cost_log = []
    _loaded = True


def _save_log() -> None:
    try:
        # Garde seulement 30 jours
        cutoff = time.time() - 30 * 86400
        _cost_log[:] = [e for e in _cost_log if e.get("ts", 0) > cutoff]
        _COST_LOG_PATH.write_text(json.dumps(_cost_log, indent=2))
    except Exception as e:
        logger.debug(f"cost_monitor save failed: {e}")


# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------

@dataclass
class CallRecord:
    agent_id: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    ts: float = field(default_factory=time.time)
    method: str = ""
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "model": self.model,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.prompt_tokens + self.completion_tokens,
            "cost_usd": round(self.cost_usd, 6),
            "ts": self.ts,
            "date": datetime.fromtimestamp(self.ts, tz=timezone.utc).strftime("%Y-%m-%d"),
            "method": self.method,
            "note": self.note,
        }


# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------

# Conservative cache-read multiplier when OpenRouter does not return native cost
_CACHE_READ_MULTIPLIER = 0.1


def _compute_cost(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    *,
    cached_tokens: int = 0,
) -> float:
    pricing = MODEL_PRICING.get(model, MODEL_PRICING["default"])
    cached = max(0, min(int(cached_tokens), int(prompt_tokens)))
    uncached = max(0, int(prompt_tokens) - cached)
    input_cost = (
        uncached * pricing["input"] + cached * pricing["input"] * _CACHE_READ_MULTIPLIER
    )
    return (input_cost + completion_tokens * pricing["output"]) / 1_000_000


def record_call(
    agent_id: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    method: str = "",
    note: str = "",
    *,
    cached_tokens: int = 0,
    native_cost_usd: float | None = None,
) -> float:
    """
    Enregistre un appel LLM et retourne le coût USD.
    Appelable depuis LLMClient après chaque appel.
    Prefer OpenRouter native `usage.cost` when present; else estimate with cache discount.
    """
    _ensure_loaded()
    if native_cost_usd is not None:
        cost = float(native_cost_usd)
    else:
        cost = _compute_cost(
            model, prompt_tokens, completion_tokens, cached_tokens=cached_tokens
        )
    if cached_tokens and not note:
        note = f"cached_tokens={cached_tokens}"
    record = CallRecord(
        agent_id=agent_id, model=model,
        prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
        cost_usd=cost, method=method, note=note,
    )
    _cost_log.append(record.to_dict())
    _save_log()
    return cost


def get_cost_report(
    agent_id: str | None = None,
    days: int = 7,
    model: str | None = None,
) -> dict[str, Any]:
    """
    Rapport de coûts par agent sur N jours.
    Endpoint: GET /services/costs/report
    """
    _ensure_loaded()
    cutoff = time.time() - days * 86400
    entries = [e for e in _cost_log if e.get("ts", 0) > cutoff]

    if agent_id:
        entries = [e for e in entries if e.get("agent_id") == agent_id]
    if model:
        entries = [e for e in entries if e.get("model") == model]

    # Agrégation par agent
    by_agent: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "calls": 0, "cost_usd": 0.0,
        "prompt_tokens": 0, "completion_tokens": 0,
    })
    by_model: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "calls": 0, "cost_usd": 0.0,
    })
    by_day: dict[str, float] = defaultdict(float)

    for e in entries:
        aid = e.get("agent_id", "unknown")
        mod = e.get("model", "unknown")
        day = e.get("date", "unknown")
        cost = e.get("cost_usd", 0.0)

        by_agent[aid]["calls"] += 1
        by_agent[aid]["cost_usd"] += cost
        by_agent[aid]["prompt_tokens"] += e.get("prompt_tokens", 0)
        by_agent[aid]["completion_tokens"] += e.get("completion_tokens", 0)

        by_model[mod]["calls"] += 1
        by_model[mod]["cost_usd"] += cost

        by_day[day] += cost

    total_cost = sum(e.get("cost_usd", 0.0) for e in entries)

    return {
        "period_days": days,
        "agent_id_filter": agent_id,
        "total_calls": len(entries),
        "total_cost_usd": round(total_cost, 4),
        "by_agent": {
            k: {**v, "cost_usd": round(v["cost_usd"], 4)}
            for k, v in sorted(by_agent.items(), key=lambda x: x[1]["cost_usd"], reverse=True)
        },
        "by_model": {
            k: {**v, "cost_usd": round(v["cost_usd"], 4)}
            for k, v in sorted(by_model.items(), key=lambda x: x[1]["cost_usd"], reverse=True)
        },
        "by_day": dict(sorted(by_day.items())),
        "most_expensive_agent": max(by_agent, key=lambda k: by_agent[k]["cost_usd"], default=None),
    }


def get_monthly_summary(month: str | None = None) -> dict[str, Any]:
    """
    Résumé mensuel des coûts LLM — pour Jules (accounting).
    month format: "2026-06" (défaut: mois en cours)
    Endpoint: GET /services/costs/monthly
    """
    _ensure_loaded()
    if not month:
        month = datetime.now(timezone.utc).strftime("%Y-%m")

    entries = [e for e in _cost_log if e.get("date", "").startswith(month)]
    total = sum(e.get("cost_usd", 0.0) for e in entries)
    calls = len(entries)

    by_agent: dict[str, float] = defaultdict(float)
    for e in entries:
        by_agent[e.get("agent_id", "unknown")] += e.get("cost_usd", 0.0)

    return {
        "month": month,
        "total_cost_usd": round(total, 4),
        "total_calls": calls,
        "avg_cost_per_call_usd": round(total / calls, 6) if calls else 0,
        "by_agent": {k: round(v, 4) for k, v in sorted(by_agent.items(), key=lambda x: x[1], reverse=True)},
        "projection_30d_usd": round(total * 30 / max(1, len({e.get("date") for e in entries})), 2),
    }


def check_budget_alert(
    daily_budget_usd: float = 5.0,
    agent_id: str | None = None,
) -> dict[str, Any]:
    """
    Vérifie si le budget journalier est dépassé.
    Rémi (controller) reçoit l'alerte. Endpoint: GET /services/costs/alert
    """
    _ensure_loaded()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    entries = [e for e in _cost_log if e.get("date") == today]
    if agent_id:
        entries = [e for e in entries if e.get("agent_id") == agent_id]

    spent = sum(e.get("cost_usd", 0.0) for e in entries)
    pct = spent / daily_budget_usd * 100 if daily_budget_usd > 0 else 0
    alert = spent >= daily_budget_usd

    return {
        "date": today,
        "agent_id_filter": agent_id,
        "daily_budget_usd": daily_budget_usd,
        "spent_usd": round(spent, 4),
        "remaining_usd": round(max(0, daily_budget_usd - spent), 4),
        "pct_used": round(pct, 1),
        "alert": alert,
        "severity": "critical" if pct >= 100 else "warning" if pct >= 80 else "ok",
        "calls_today": len(entries),
    }


def get_top_costs(limit: int = 10, days: int = 7) -> list[dict[str, Any]]:
    """Top N appels les plus coûteux sur N jours."""
    _ensure_loaded()
    cutoff = time.time() - days * 86400
    entries = [e for e in _cost_log if e.get("ts", 0) > cutoff]
    return sorted(entries, key=lambda e: e.get("cost_usd", 0), reverse=True)[:limit]


# ---------------------------------------------------------------------------
# UI adapters — same shapes as skill_model_usage for /costs/* routes
# ---------------------------------------------------------------------------

def get_daily_costs(target_date: date | None = None) -> dict[str, Any]:
    """Coûts du jour groupés par agent (Hub UI + lobby)."""
    from datetime import date as date_cls

    _ensure_loaded()
    if target_date is None:
        target_date = date_cls.today()

    day_key = target_date.isoformat()
    entries = [e for e in _cost_log if e.get("date") == day_key]

    by_agent: dict[str, dict[str, Any]] = {}
    total = 0.0
    for e in entries:
        name = e.get("agent_id", "unknown")
        cost = float(e.get("cost_usd", 0.0))
        total += cost
        if name not in by_agent:
            by_agent[name] = {"total_usd": 0.0, "calls": 0, "tokens_in": 0, "tokens_out": 0}
        by_agent[name]["total_usd"] = round(by_agent[name]["total_usd"] + cost, 6)
        by_agent[name]["calls"] += 1
        by_agent[name]["tokens_in"] += e.get("prompt_tokens", 0)
        by_agent[name]["tokens_out"] += e.get("completion_tokens", 0)

    return {
        "date": day_key,
        "total_usd": round(total, 4),
        "by_agent": by_agent,
    }


def get_monthly_costs() -> dict[str, Any]:
    """Coûts du mois en cours — format lobby / finances."""
    from datetime import date as date_cls

    today = date_cls.today()
    month_prefix = today.strftime("%Y-%m")
    summary = get_monthly_summary(month=month_prefix)
    return {
        "month": today.strftime("%B %Y"),
        "total_usd": summary.get("total_cost_usd", 0.0),
        "by_agent": summary.get("by_agent", {}),
    }


def get_weekly_costs() -> dict[str, Any]:
    """Coûts des 7 derniers jours — format Hub dashboard."""
    from datetime import date as date_cls

    _ensure_loaded()
    today = date_cls.today()
    start = today - timedelta(days=6)

    by_date: dict[str, dict[str, float]] = {}
    total = 0.0
    for e in _cost_log:
        day = e.get("date", "")
        if not day:
            continue
        try:
            d = date_cls.fromisoformat(day)
        except ValueError:
            continue
        if d < start or d > today:
            continue
        agent = e.get("agent_id", "unknown")
        cost = float(e.get("cost_usd", 0.0))
        total += cost
        by_date.setdefault(day, {})
        by_date[day][agent] = round(by_date[day].get(agent, 0.0) + cost, 6)

    by_day: list[dict[str, Any]] = []
    for i in range(7):
        d = start + timedelta(days=i)
        key = d.isoformat()
        entry: dict[str, Any] = {"date": d.strftime("%d/%m")}
        for agent, cost in by_date.get(key, {}).items():
            entry[agent] = round(cost, 4)
        by_day.append(entry)

    return {"total_usd": round(total, 4), "by_day": by_day}
