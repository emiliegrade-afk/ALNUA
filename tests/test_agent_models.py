"""Utility-based AUTO models (DEC-037)."""
from __future__ import annotations

from pathlib import Path

import pytest

from config.agent_models_catalog import AVAILABLE_MODELS
from config.agent_models_registry import AGENT_TIERS, TIER_DEFAULTS
from config.agent_models_roles import AGENT_ROLE_MODELS, CODE_UTILITY_AGENT_IDS


def test_role_models_cover_every_tier_agent() -> None:
    assert set(AGENT_ROLE_MODELS) == set(AGENT_TIERS)


def test_role_models_are_in_catalogue() -> None:
    missing = [m for m in AGENT_ROLE_MODELS.values() if m not in AVAILABLE_MODELS]
    assert missing == []


def test_tier_defaults_are_in_catalogue() -> None:
    for model in TIER_DEFAULTS.values():
        assert model in AVAILABLE_MODELS


def test_latest_openrouter_flagships_in_catalogue() -> None:
    for model_id in (
        "anthropic/claude-sonnet-5",
        "anthropic/claude-opus-5",
        "anthropic/claude-fable-5.1",
        "openai/gpt-5.6-sol",
        "openai/gpt-5.6-terra",
        "openai/gpt-5.6-luna",
        "z-ai/glm-5.3",
        "z-ai/glm-5.3-flash",
        "moonshotai/kimi-k3",
        "minimax/minimax-m3",
    ):
        assert model_id in AVAILABLE_MODELS, model_id


def test_auto_defaults_match_ceo_parametres_picks() -> None:
    assert AGENT_ROLE_MODELS["coo"] == "google/gemma-4-31b-it"
    assert AGENT_ROLE_MODELS["secretary"] == "z-ai/glm-5.2"
    assert AGENT_ROLE_MODELS["dev_app"] == "minimax/minimax-m3"
    assert AGENT_ROLE_MODELS["qa"] == "qwen/qwen3-235b-a22b"
    assert AGENT_ROLE_MODELS["marketing"] == "minimax/minimax-m3"
    assert AGENT_ROLE_MODELS["accounting"] == "anthropic/claude-haiku-4-5"
    assert "dev_app" in CODE_UTILITY_AGENT_IDS


def test_auto_resolves_role_model_when_json_empty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from config import agent_models_resolve as resolve

    monkeypatch.setattr(resolve, "_CONFIG_FILE", tmp_path / "agent_models.json")
    monkeypatch.delenv("AGENT_MODEL_COO", raising=False)
    assert resolve.get_model_for_agent("coo") == AGENT_ROLE_MODELS["coo"]
    assert resolve.get_model_for_agent("dev_app") == AGENT_ROLE_MODELS["dev_app"]


def test_parametres_override_wins(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from config import agent_models_resolve as resolve

    cfg = tmp_path / "agent_models.json"
    cfg.write_text('{"coo": "anthropic/claude-haiku-4-5"}', encoding="utf-8")
    monkeypatch.setattr(resolve, "_CONFIG_FILE", cfg)
    monkeypatch.delenv("AGENT_MODEL_COO", raising=False)
    assert resolve.get_model_for_agent("coo") == "anthropic/claude-haiku-4-5"


def test_pm_and_safety_tiers_match_utility() -> None:
    assert AGENT_TIERS["pm"] == "standard"
    assert AGENT_TIERS["controller"] == "standard"
    assert AGENT_TIERS["safety"] == "premium"
    assert AGENT_TIERS["secretary"] == "fast"
