"""Code Challenge — Q&A algo only, no code execution (Phase 46 V6)."""

from __future__ import annotations

from typing import Any

CHALLENGES: list[dict[str, Any]] = [
    {
        "id": "code-big-o",
        "activity": "code_challenge",
        "title": "Complexité",
        "difficulty": 1,
        "mode": "exact",
        "prompt": (
            "Boucle for i in range(n): for j in range(n): … "
            "Quelle complexité asymptotique ? (ex: O(n) ou O(n^2))"
        ),
        "answer": "o(n^2)",
        "accepted": ["o(n^2)", "o(n2)", "n^2", "n2", "quadratic"],
    },
    {
        "id": "code-stable-sort",
        "activity": "code_challenge",
        "title": "Tri stable",
        "difficulty": 2,
        "mode": "exact",
        "prompt": (
            "Parmi merge sort et quicksort classique (non stable), "
            "lequel est stable ? Réponds merge ou quick."
        ),
        "answer": "merge",
        "accepted": ["merge", "mergesort", "merge sort"],
    },
    {
        "id": "code-http-idem",
        "activity": "code_challenge",
        "title": "Idempotence HTTP",
        "difficulty": 1,
        "mode": "exact",
        "prompt": "PUT est-il idempotent ? Réponds oui ou non.",
        "answer": "oui",
        "accepted": ["oui", "yes", "true", "idempotent"],
    },
]
