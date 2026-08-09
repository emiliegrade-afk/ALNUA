"""Vague E / Phase 28 — R&D Explorer signals + brief."""
from __future__ import annotations

from typing import Any
from unittest.mock import patch

from services.trend_monitor import TrendItem


def _fake_items() -> list[TrendItem]:
    return [
        TrendItem(title="New AI agents framework ships", url="https://ex/1", source="hackernews", score=200),
        TrendItem(title="Cooking recipes weekly", url="https://ex/2", source="reddit", score=500),
        TrendItem(title="edge AI on Pi robotics kit", url="https://ex/3", source="github", score=90),
    ]


def test_scan_signals_ranks_topics() -> None:
    from services.rnd_explorer import scan_signals

    with patch("services.trend_monitor.aggregate_trends", return_value=_fake_items()):
        out = scan_signals(topics=["AI agents", "robotics"], limit=10)
    assert out["ok"] is True
    titles = [i["title"] for i in out["items"]]
    assert titles[0] in (
        "New AI agents framework ships",
        "edge AI on Pi robotics kit",
    )
    assert "Cooking recipes weekly" in titles  # kept, lower rank


def test_brief_explorer_empty() -> None:
    from services.rnd_explorer import brief_explorer

    with patch("services.trend_monitor.aggregate_trends", return_value=[]):
        out = brief_explorer(topics=["LLM"])
    assert out["ok"] is False
    assert out["error"]


def test_brief_explorer_llm_path() -> None:
    from services.rnd_explorer import brief_explorer

    with patch("services.trend_monitor.aggregate_trends", return_value=_fake_items()):
        with patch(
            "services.rnd_explorer._synthesize_rnd",
            return_value={
                "synthesis": "Agents and edge robotics accelerating.",
                "rnd_signals": ["agents", "edge"],
                "dossier_hooks": ["Pi + vision kit"],
            },
        ):
            out = brief_explorer(topics=["AI agents"], agent_id="brainstorm")
    assert out["ok"] is True
    assert "Agents" in out["synthesis"]
    assert out["dossier_hooks"]


def test_explorer_router_signals(monkeypatch: Any) -> None:
    from fastapi.testclient import TestClient

    from api.app import app
    from config.settings import get_settings

    monkeypatch.setenv("HUB_API_KEY", "test-hub-key-for-ci")
    get_settings.cache_clear()
    with patch(
        "services.rnd_explorer.scan_signals",
        return_value={
            "ok": True,
            "mode": "signals",
            "topics": ["LLM"],
            "sources": ["hn"],
            "total": 1,
            "items": [],
            "fetched_at": "t",
            "empty_reason": None,
        },
    ):
        client = TestClient(app)
        res = client.get(
            "/rnd/explorer/signals?topics=LLM",
            headers={"X-Hub-Key": "test-hub-key-for-ci"},
        )
    assert res.status_code == 200
    assert res.json()["ok"] is True
