"""Lounge puzzle catalog — deterministic challenges (DEC-031 / Phase 46 V3)."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

# Public fields only in API responses — never leak `answer` until session ends.
PUZZLES: list[dict[str, Any]] = [
    {
        "id": "logic-lights",
        "title": "Trois interrupteurs",
        "difficulty": 2,
        "prompt": (
            "Trois interrupteurs. Un seul allume une ampoule dans une pièce fermée. "
            "Tu peux manipuler les interrupteurs, puis entrer UNE seule fois. "
            "Comment identifier l'interrupteur de l'ampoule ?"
        ),
        "answer": "chaleur",
        "hints": [
            "allume un interrupteur longtemps",
            "touche l'ampoule",
        ],
        "accepted": [
            "chaleur",
            "chaude",
            "chaud",
            "temperature",
            "température",
            "heat",
            "warm",
        ],
    },
    {
        "id": "river-wolf-goat",
        "title": "Loup, chèvre, chou",
        "difficulty": 2,
        "prompt": (
            "Un fermier doit faire traverser un loup, une chèvre et un chou. "
            "La barque ne porte que le fermier + 1. Loup ne peut pas rester seul "
            "avec la chèvre, ni la chèvre avec le chou. Quelle est la clé du problème ?"
        ),
        "answer": "retour",
        "hints": ["ramener", "aller-retour"],
        "accepted": [
            "retour",
            "ramener",
            "revenir",
            "aller-retour",
            "back",
            "bring back",
        ],
    },
    {
        "id": "binary-sum",
        "title": "Somme binaire",
        "difficulty": 1,
        "prompt": (
            "En binaire, que vaut 1011 + 0101 ? Réponds en décimal (nombre entier)."
        ),
        "answer": "16",
        "hints": ["11+5"],
        "accepted": ["16", "seize", "sixteen"],
    },
    {
        "id": "aluna-acronym",
        "title": "Sigle ALNUA",
        "difficulty": 1,
        "prompt": (
            "Dans le Hub ALNUA, quel agent persona porte le rôle COO "
            "(prénom uniquement) ?"
        ),
        "answer": "aria",
        "hints": ["Aria Voss"],
        "accepted": ["aria", "aria voss"],
    },
    {
        "id": "monty-doors",
        "title": "Trois portes",
        "difficulty": 2,
        "prompt": (
            "Trois portes : une voiture, deux chèvres. Tu choisis la porte 1. "
            "L'animateur ouvre la porte 3 (chèvre) et propose de changer pour la 2. "
            "Dois-tu changer ? Réponds oui ou non."
        ),
        "answer": "oui",
        "hints": ["probabilité 2/3"],
        "accepted": ["oui", "yes", "changer", "switch", "true"],
    },
]


def list_puzzles_public() -> list[dict[str, Any]]:
    return [
        {
            "id": p["id"],
            "title": p["title"],
            "difficulty": p["difficulty"],
            "prompt": p["prompt"],
        }
        for p in PUZZLES
    ]


def get_puzzle(puzzle_id: str) -> dict[str, Any] | None:
    for p in PUZZLES:
        if p["id"] == puzzle_id:
            return p
    return None


def pick_puzzle(puzzle_id: str | None = None) -> dict[str, Any]:
    if puzzle_id:
        found = get_puzzle(puzzle_id)
        if found is None:
            raise ValueError(f"unknown puzzle_id: {puzzle_id}")
        return found
    # Rotate by count of puzzles — callers may pass index via runtime.
    return PUZZLES[0]


def normalize_answer(text: str) -> str:
    cleaned = unicodedata.normalize("NFKD", text or "")
    cleaned = "".join(c for c in cleaned if not unicodedata.combining(c))
    cleaned = cleaned.lower().strip()
    cleaned = re.sub(r"[^\w\s\-]", " ", cleaned, flags=re.UNICODE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def evaluate_answer(puzzle: dict[str, Any], raw_answer: str) -> dict[str, Any]:
    norm = normalize_answer(raw_answer)
    accepted = [normalize_answer(a) for a in puzzle.get("accepted", [])]
    canonical = normalize_answer(str(puzzle.get("answer", "")))
    if canonical and canonical not in accepted:
        accepted.append(canonical)

    won = False
    if norm:
        for cand in accepted:
            if cand and (cand == norm or cand in norm or norm in cand):
                won = True
                break

    hints = puzzle.get("hints") or []
    return {
        "won": won,
        "normalized": norm,
        "expected_hint": hints[0] if hints else None,
    }
