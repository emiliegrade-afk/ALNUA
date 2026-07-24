"""services/elevenlabs_monitor.py — ElevenLabs usage/cost tracking.

ElevenLabs bills per subscription tier (a fixed monthly fee for an included
character quota), not per-call like OpenRouter, so there is no equivalent
of cost_monitor.py's per-call ledger. What their API does expose reliably
is real-time quota usage via GET /v1/user/subscription. That's the primary,
always-honest signal here: characters used / character quota / reset date.

A USD estimate is only computed if the user tells us what their plan costs
per month (there's no way to derive it from the API alone) — without that,
we report usage only rather than inventing a dollar figure.
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_API_BASE = "https://api.elevenlabs.io/v1"
_USAGE_LOG_PATH = Path(__file__).parent.parent / "data" / "elevenlabs_usage_log.json"
_CONFIG_PATH = Path(__file__).parent.parent / "data" / "elevenlabs_config.json"


def _api_key() -> str:
    return os.getenv("ELEVENLABS_API_KEY", "").strip()


def is_configured() -> bool:
    return bool(_api_key())


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.debug("elevenlabs_monitor read %s failed: %s", path, exc)
        return {}


def _save_json(path: Path, data: dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        logger.debug("elevenlabs_monitor write %s failed: %s", path, exc)


def set_monthly_plan_cost(usd_per_month: float) -> None:
    """Only way to get a USD estimate — ElevenLabs plan pricing isn't in the API."""
    cfg = _load_json(_CONFIG_PATH)
    cfg["monthly_plan_cost_usd"] = usd_per_month
    _save_json(_CONFIG_PATH, cfg)


def get_monthly_plan_cost() -> float | None:
    return _load_json(_CONFIG_PATH).get("monthly_plan_cost_usd")


def fetch_subscription_usage() -> dict[str, Any] | None:
    """Live call to GET /v1/user/subscription. None if unconfigured or unreachable."""
    api_key = _api_key()
    if not api_key:
        return None
    try:
        import httpx

        resp = httpx.get(
            f"{_API_BASE}/user/subscription",
            headers={"xi-api-key": api_key},
            timeout=10.0,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("ElevenLabs subscription fetch failed: %s", exc)
        return None


def record_snapshot() -> dict[str, Any] | None:
    """Poll current usage and append a timestamped snapshot for trend reporting."""
    usage = fetch_subscription_usage()
    if usage is None:
        return None

    snapshot = {
        "ts": time.time(),
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "character_count": usage.get("character_count", 0),
        "character_limit": usage.get("character_limit", 0),
        "tier": usage.get("tier", "unknown"),
        "next_reset_unix": usage.get("next_character_count_reset_unix"),
        "status": usage.get("status", "unknown"),
    }

    log = _load_json(_USAGE_LOG_PATH)
    entries: list[dict[str, Any]] = log.get("entries", [])
    entries.append(snapshot)
    cutoff = time.time() - 90 * 86400
    entries = [e for e in entries if e.get("ts", 0) > cutoff]
    _save_json(_USAGE_LOG_PATH, {"entries": entries})
    return snapshot


def get_elevenlabs_report() -> dict[str, Any]:
    """Current quota usage + optional USD estimate — GET /costs/elevenlabs."""
    if not is_configured():
        return {
            "configured": False,
            "message": "ELEVENLABS_API_KEY absente — usage non suivi.",
        }

    usage = fetch_subscription_usage()
    if usage is None:
        return {
            "configured": True,
            "reachable": False,
            "message": "API ElevenLabs injoignable (clé invalide ou service indisponible).",
        }

    character_count = int(usage.get("character_count", 0))
    character_limit = int(usage.get("character_limit", 0))
    pct_used = round(character_count / character_limit * 100, 1) if character_limit else 0.0

    reset_unix = usage.get("next_character_count_reset_unix")
    reset_date = (
        datetime.fromtimestamp(reset_unix, tz=timezone.utc).strftime("%Y-%m-%d")
        if reset_unix
        else None
    )

    plan_cost = get_monthly_plan_cost()
    estimated_usd = (
        round(character_count / character_limit * plan_cost, 2)
        if plan_cost and character_limit
        else None
    )

    return {
        "configured": True,
        "reachable": True,
        "tier": usage.get("tier", "unknown"),
        "character_count": character_count,
        "character_limit": character_limit,
        "pct_used": pct_used,
        "reset_date": reset_date,
        "monthly_plan_cost_usd": plan_cost,
        "estimated_cost_this_period_usd": estimated_usd,
    }


def get_usage_history(days: int = 30) -> list[dict[str, Any]]:
    log = _load_json(_USAGE_LOG_PATH)
    entries: list[dict[str, Any]] = log.get("entries", [])
    cutoff = time.time() - days * 86400
    return [e for e in entries if e.get("ts", 0) > cutoff]
