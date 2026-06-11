"""ALNUA Hub agents package — lazy exports to support `python -m agents.coo_agent`."""

from __future__ import annotations

import importlib
from typing import Any

from agents.base import LLMClient, log_agent_action, parse_json_response

__all__ = [
    "LLMClient",
    "log_agent_action",
    "parse_json_response",
    "COOAgent",
    "route_to_agent",
    "PMAgent",
    "QAAgent",
    "ContentAgent",
    "BrainstormAgent",
    "SpecAgent",
    "GameDirectorAgent",
    "DevGamingAgent",
    "HardwareAgent",
    "EmbeddedDevAgent",
    "MarketingAgent",
]

_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    "COOAgent": ("agents.coo_agent", "COOAgent"),
    "route_to_agent": ("agents.coo_agent", "route_to_agent"),
    "PMAgent": ("agents.pm_agent", "PMAgent"),
    "QAAgent": ("agents.qa_agent", "QAAgent"),
    "ContentAgent": ("agents.content_agent", "ContentAgent"),
    "BrainstormAgent": ("agents.brainstorm_agent", "BrainstormAgent"),
    "SpecAgent": ("agents.spec_agent", "SpecAgent"),
    "GameDirectorAgent": ("agents.game_director_agent", "GameDirectorAgent"),
    "DevGamingAgent": ("agents.dev_gaming_agent", "DevGamingAgent"),
    "HardwareAgent": ("agents.hardware_agent", "HardwareAgent"),
    "EmbeddedDevAgent": ("agents.embedded_dev_agent", "EmbeddedDevAgent"),
    "MarketingAgent": ("agents.marketing_agent", "MarketingAgent"),
}


def __getattr__(name: str) -> Any:
    if name in _LAZY_EXPORTS:
        module_path, attr = _LAZY_EXPORTS[name]
        return getattr(importlib.import_module(module_path), attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
