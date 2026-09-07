"""Creative Lab — short generative challenges (Phase 46 V6)."""

from __future__ import annotations

from typing import Any

CHALLENGES: list[dict[str, Any]] = [
    {
        "id": "creative-tagline",
        "activity": "creative",
        "title": "Tagline Lounge",
        "difficulty": 1,
        "mode": "llm_free",
        "prompt": (
            "Écris 3 taglines (FR) pour l'Agent Lounge ALNUA — "
            "expérimentation, pas « les IA se reposent »."
        ),
        "min_chars": 40,
    },
    {
        "id": "creative-scene",
        "activity": "creative",
        "title": "Micro-scène",
        "difficulty": 1,
        "mode": "llm_free",
        "prompt": (
            "Écris une micro-scène (80–120 mots) : Theo et Hao en Code Duel "
            "dans le Lounge, ton premium ALNUA."
        ),
        "min_chars": 80,
    },
]
