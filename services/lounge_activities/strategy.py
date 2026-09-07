"""Strategy — light optimization / planning challenges (Phase 46 V6)."""

from __future__ import annotations

from typing import Any

CHALLENGES: list[dict[str, Any]] = [
    {
        "id": "strat-knapsack-lite",
        "activity": "strategy",
        "title": "Sac à dos express",
        "difficulty": 2,
        "mode": "exact",
        "prompt": (
            "Objets : A=3pts/2kg, B=4pts/3kg, C=5pts/4kg. Capacité 5kg. "
            "Quel score max ? Réponds par un entier."
        ),
        "answer": "7",
        "accepted": ["7", "sept", "seven"],
    },
    {
        "id": "strat-meeting",
        "activity": "strategy",
        "title": "Créneau unique",
        "difficulty": 1,
        "mode": "exact",
        "prompt": (
            "3 agents libres : 10h–12h, 11h–13h, 9h–11h. "
            "Quel créneau d'1h est libre pour les 3 ? Format Hh (ex: 11h)."
        ),
        "answer": "11h",
        "accepted": ["11h", "11", "11:00", "11h00"],
    },
    {
        "id": "strat-nim",
        "activity": "strategy",
        "title": "Nim express",
        "difficulty": 2,
        "mode": "exact",
        "prompt": (
            "Pile de 7 allumettes. Chaque joueur en retire 1 ou 2. "
            "Qui gagne si les deux jouent optimal (premier / second) ?"
        ),
        "answer": "premier",
        "accepted": ["premier", "first", "1", "joueur 1"],
    },
]
