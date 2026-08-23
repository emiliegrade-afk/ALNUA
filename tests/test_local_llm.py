"""Tests du fallback LLM local (services/local_llm.py)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest


def test_is_credit_exhausted_402() -> None:
    from services.local_llm import is_credit_exhausted

    assert is_credit_exhausted(402) is True
    assert is_credit_exhausted(402, "anything") is True


def test_is_credit_exhausted_markers() -> None:
    from services.local_llm import is_credit_exhausted

    assert is_credit_exhausted(429, "Insufficient credits") is True
    assert is_credit_exhausted(403, "quota exceeded") is True
    assert is_credit_exhausted(500, "internal server error") is False
    assert is_credit_exhausted(401, "missing auth") is False


def test_clean_messages_strips_openrouter_cache_fields() -> None:
    from services.local_llm import _clean_messages

    payload: dict[str, Any] = {
        "messages": [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": "Tu es Nadia.",
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
            },
            {"role": "user", "content": "Bonjour"},
        ],
        "session_id": "alnua:secretary",
        "cache_control": {"type": "ephemeral"},
    }
    assert _clean_messages(payload) == [
        {"role": "system", "content": "Tu es Nadia."},
        {"role": "user", "content": "Bonjour"},
    ]


def test_config_merge_file_over_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import services.local_llm as llm

    monkeypatch.setattr(llm, "_CONFIG_FILE", tmp_path / "llm_connectivity.json")

    class _FakeSettings:
        local_llm_enabled = False
        local_llm_fallback_on_credit = True
        local_llm_base_url = "http://localhost:11434/v1"
        local_llm_model = "qwen2.5:7b-instruct-q4_K_M"
        local_llm_api_key = ""

    import importlib

    _settings_module = importlib.import_module("config.settings")
    monkeypatch.setattr(_settings_module, "get_settings", lambda: _FakeSettings())

    llm.save_local_llm_config(
        {"enabled": True, "base_url": "http://localhost:1234/v1", "model": "llama3"},
        api_key="secret",
    )
    cfg = llm.get_local_llm_config()
    assert cfg["enabled"] is True
    assert cfg["base_url"] == "http://localhost:1234/v1"
    assert cfg["model"] == "llama3"
    assert cfg["api_key"] == "secret"
    assert cfg["fallback_on_credit"] is True  # hérité de l'env


def test_local_fallback_returns_content(monkeypatch: pytest.MonkeyPatch) -> None:
    from agents.base_llm import LLMClient
    from services import local_llm

    client = LLMClient.__new__(LLMClient)
    monkeypatch.setattr(local_llm, "local_llm_available", lambda: True)
    monkeypatch.setattr(local_llm, "fallback_on_credit_enabled", lambda: True)
    monkeypatch.setattr(local_llm, "complete_local_sync", lambda payload: "réponse locale")

    assert client._local_fallback({}, RuntimeError("402")) == "réponse locale"


def test_local_fallback_disabled_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    from agents.base_llm import LLMClient
    from services import local_llm

    client = LLMClient.__new__(LLMClient)
    monkeypatch.setattr(local_llm, "local_llm_available", lambda: True)
    monkeypatch.setattr(local_llm, "fallback_on_credit_enabled", lambda: False)

    assert client._local_fallback({}, RuntimeError("402")) is None
