"""Cost monitor — model pricing and per-call cost computation."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

MODEL_PRICING: dict[str, dict[str, float]] = {
    "google/gemini-flash-1.5": {"input": 0.075, "output": 0.30},
    "google/gemini-2.0-flash-001": {"input": 0.10, "output": 0.40},
    "anthropic/claude-haiku-4-5": {"input": 0.80, "output": 4.00},
    "anthropic/claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.00},
    "anthropic/claude-sonnet-4-5": {"input": 3.00, "output": 15.00},
    "anthropic/claude-opus-4": {"input": 15.00, "output": 75.00},
    "openai/gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "openai/gpt-4o": {"input": 2.50, "output": 10.00},
    "mistralai/mistral-7b-instruct": {"input": 0.06, "output": 0.06},
    "default": {"input": 1.00, "output": 3.00},
}

_CACHE_READ_MULTIPLIER = 0.1


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


def compute_cost(
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
