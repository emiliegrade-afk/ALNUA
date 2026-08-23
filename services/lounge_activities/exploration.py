"""Exploration — borned free-form insight (LLM or manual) (Phase 46 V6)."""

from __future__ import annotations

from typing import Any

CHALLENGES: list[dict[str, Any]] = [
    {
        "id": "explore-hub-friction",
        "activity": "exploration",
        "title": "Friction Hub",
        "difficulty": 1,
        "mode": "llm_free",
        "prompt": (
            "En 3–5 phrases : une friction UX du Hub ALNUA et une expérimentation "
            "Lounge pour la tester sans toucher la prod."
        ),
        "min_chars": 60,
    },
    {
        "id": "explore-agent-collab",
        "activity": "exploration",
        "title": "Collab agents",
        "difficulty": 1,
        "mode": "llm_free",
        "prompt": (
            "Propose un protocole de duel créatif entre 2 agents de départements "
            "différents (qui, brief, critère de succès)."
        ),
        "min_chars": 60,
    },
]
