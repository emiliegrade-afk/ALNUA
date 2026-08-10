"""JSON extraction helpers for LLM responses."""

from __future__ import annotations

import json
from typing import Any


def parse_json_response(text: str) -> dict[str, Any]:
    """Extract JSON object from LLM response (fences + trailing prose)."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = lines[1:] if lines[0].startswith("```") else lines
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        if start < 0:
            raise
        data, _ = json.JSONDecoder().raw_decode(cleaned[start:])
    if not isinstance(data, dict):
        raise ValueError("Expected a JSON object from LLM response")
    return data
