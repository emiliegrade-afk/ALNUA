"""Shared constants for the autonomous bug-fix pipeline."""
from __future__ import annotations

import os

MAX_PIPELINE_ATTEMPTS = int(os.getenv("WATCHDOG_MAX_ATTEMPTS", "3"))

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
REVIEW_MODEL = os.getenv("REVIEW_MODEL", "anthropic/claude-sonnet-4-5")
FIX_MODEL = os.getenv("FIX_MODEL", "minimax/minimax-m1")

# Contexte croissant selon le numéro de tentative
CONTEXT_LEVELS = [
    {"files": 2, "history": 3, "depth": "shallow"},  # Tentative 1 : rapide
    {"files": 5, "history": 8, "depth": "medium"},  # Tentative 2 : élargi
    {"files": 10, "history": 15, "depth": "deep"},  # Tentative 3 : complet
    {"files": 20, "history": 20, "depth": "exhaustive"},  # Tentative 4+ : tout
]
