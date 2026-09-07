"""Simulation — isolated what-if scenarios, no prod side-effects (Phase 46 V6)."""

from __future__ import annotations

from typing import Any

CHALLENGES: list[dict[str, Any]] = [
    {
        "id": "sim-budget-cut",
        "activity": "simulation",
        "title": "Coupe budget LLM",
        "difficulty": 2,
        "mode": "llm_free",
        "prompt": (
            "Simulation : budget LLM −40 % demain. Liste 3 actions idle/Lounge "
            "à garder et 2 à geler — sans toucher la prod."
        ),
        "min_chars": 60,
    },
    {
        "id": "sim-dept-outage",
        "activity": "simulation",
        "title": "Outage département",
        "difficulty": 2,
        "mode": "llm_free",
        "prompt": (
            "Simulation : le pôle APP est offline 4h. Plan de continuité "
            "(qui couvre, quoi différer, quoi monitorer) en 5 puces."
        ),
        "min_chars": 60,
    },
]
