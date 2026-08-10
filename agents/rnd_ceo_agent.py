"""
rnd_ceo_agent.py — Package CEO, validation Emilie, dispatch COO (phase 6).

Façade : mixins under ``agents/rnd_ceo_*.py`` keep each module ≤ ~300 lines.
"""
from __future__ import annotations

import os
from pathlib import Path

from agents.base import LLMClient
from agents.rnd_ceo_decision import RndCeoDecisionMixin
from agents.rnd_ceo_dispatch import RndCeoDispatchMixin
from agents.rnd_ceo_errors import (  # noqa: F401 — public API re-export
    CeoDecisionError,
    CeoPackageNotReadyError,
    DispatchNotAllowedError,
)
from agents.rnd_ceo_generation import RndCeoGenerationMixin
from agents.rnd_ceo_helpers import RndCeoHelpersMixin
from agents.rnd_ceo_queue import RndCeoQueueMixin
from services.rnd_repository import get_rnd_repository


class RndCeoAgent(
    RndCeoDispatchMixin,
    RndCeoDecisionMixin,
    RndCeoGenerationMixin,
    RndCeoQueueMixin,
    RndCeoHelpersMixin,
):
    """Package CEO, validation Emilie, dispatch COO — phase 6 R&D dossier hub."""

    AGENT_NAME = "rnd_ceo_agent"

    def __init__(self) -> None:
        self.repo = get_rnd_repository()
        self.llm = LLMClient()
        self.data_root = Path(
            os.getenv("HUB_REPO_PATH", "C:/Dev/ALUNA_HUB")
        ) / "data" / "rnd_dossiers"
