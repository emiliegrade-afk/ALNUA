"""Arcade — quick deterministic mini-challenges (Phase 46 V6)."""

from __future__ import annotations

from typing import Any

CHALLENGES: list[dict[str, Any]] = [
    {
        "id": "arcade-seq-3",
        "activity": "arcade",
        "title": "Séquence flash",
        "difficulty": 1,
        "mode": "exact",
        "prompt": (
            "Mémorise : 7 · 2 · 9 · 4. Quelle est la 3ᵉ valeur ? "
            "Réponds par un seul chiffre."
        ),
        "answer": "9",
        "accepted": ["9", "neuf", "nine"],
    },
    {
        "id": "arcade-parity",
        "activity": "arcade",
        "title": "Réflexe parité",
        "difficulty": 1,
        "mode": "exact",
        "prompt": "Combien d'entiers pairs entre 1 et 10 inclus ?",
        "answer": "5",
        "accepted": ["5", "cinq", "five"],
    },
    {
        "id": "arcade-mirror",
        "activity": "arcade",
        "title": "Mirror bytes",
        "difficulty": 2,
        "mode": "exact",
        "prompt": "Inverse la chaîne ALNUA (casse conservée). Réponds en un mot.",
        "answer": "AUNLA",
        "accepted": ["aunla", "AUNLA"],
    },
]
