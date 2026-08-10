"""Tests for services/autonomy_resolver.py — DEC-011 trust bands."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def trust_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    path = tmp_path / "agent_trust.json"
    monkeypatch.setattr("services.agent_trust._STORE", path)
    return path


def test_trust_bands() -> None:
    from services.autonomy_resolver import trust_score_to_autonomy

    assert trust_score_to_autonomy(0.69) == 0
    assert trust_score_to_autonomy(0.70) == 1
    assert trust_score_to_autonomy(0.79) == 1
    assert trust_score_to_autonomy(0.80) == 2
    assert trust_score_to_autonomy(0.89) == 2
    assert trust_score_to_autonomy(0.90) == 3
    assert trust_score_to_autonomy(0.99) == 3


def test_resolve_idle_max_level() -> None:
    from services.autonomy_resolver import resolve_idle_max_level

    assert resolve_idle_max_level(0) == 0
    assert resolve_idle_max_level(1) == 1
    assert resolve_idle_max_level(2) == 2
    assert resolve_idle_max_level(3) == 2


def test_resolve_from_trust(trust_store: Path) -> None:
    from services.agent_trust import record_validation
    from services.autonomy_resolver import resolve_autonomy_level

    assert resolve_autonomy_level("content") == 1  # default 0.7 → band 1

    for _ in range(8):
        record_validation("content", success=True, weight=2.0)
    high = resolve_autonomy_level("content")
    assert high >= 2


def test_empty_agent_uses_default() -> None:
    from services.autonomy_resolver import resolve_autonomy_level

    level = resolve_autonomy_level("")
    assert 0 <= level <= 3
