"""Cost monitor — JSON persistence and record_call."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

from services.cost_monitor_pricing import CallRecord, compute_cost

logger = logging.getLogger(__name__)

COST_LOG_PATH = Path(__file__).parent.parent / "data" / "cost_log.json"
_cost_log: list[dict[str, Any]] = []
_loaded = False


def ensure_loaded() -> None:
    global _cost_log, _loaded
    if _loaded:
        return
    COST_LOG_PATH.parent.mkdir(exist_ok=True)
    if COST_LOG_PATH.exists():
        try:
            _cost_log = json.loads(COST_LOG_PATH.read_text())
        except Exception:
            _cost_log = []
    _loaded = True


def save_log() -> None:
    try:
        cutoff = time.time() - 30 * 86400
        _cost_log[:] = [e for e in _cost_log if e.get("ts", 0) > cutoff]
        COST_LOG_PATH.write_text(json.dumps(_cost_log, indent=2))
    except Exception as e:
        logger.debug(f"cost_monitor save failed: {e}")


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
    """Record an LLM call and return USD cost."""
    ensure_loaded()
    if native_cost_usd is not None:
        cost = float(native_cost_usd)
    else:
        cost = compute_cost(
            model, prompt_tokens, completion_tokens, cached_tokens=cached_tokens
        )
    if cached_tokens and not note:
        note = f"cached_tokens={cached_tokens}"
    record = CallRecord(
        agent_id=agent_id,
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cost_usd=cost,
        method=method,
        note=note,
    )
    _cost_log.append(record.to_dict())
    save_log()
    return cost
