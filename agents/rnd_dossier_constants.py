"""Constants for R&D dossier agent — anti-fluff and LLM section keys."""
from __future__ import annotations

import re

FLUFF_PATTERNS = re.compile(
    r"vont adorer|marché énorme|énorme marché|millennials vont|génération .+ va",
    re.IGNORECASE,
)

CORE_LLM_SECTIONS = (
    "problem", "solution", "market", "mvp", "feasibility", "risks", "decision",
)
