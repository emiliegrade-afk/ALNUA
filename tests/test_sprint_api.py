"""Tests for API versioning, feedback, metrics, plugins."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from tests.conftest import FakeDB, HUB_HEADERS


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("HUB_API_KEY", "test-hub-key-for-ci")
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "0")
    from config.settings import get_settings

    get_settings.cache_clear()
    monkeypatch.setattr("database.supabase_client.get_supabase", lambda: FakeDB())
    from api.app import app

    return TestClient(app)


def test_v1_prefix_not_mounted(client: TestClient) -> None:
    """Routers are mounted once (bare path only) — /v1/* must stay 404.

    Double-mounting each router under /v1 used to duplicate operation_id in the
    OpenAPI schema and risked collisions in the fastapi-mcp tool list; guard
    against it silently coming back.
    """
    res = client.get("/v1/health")
    assert res.status_code == 404

    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_metrics_endpoint_public(client: TestClient) -> None:
    res = client.get("/metrics")
    assert res.status_code == 200
    assert "text/plain" in res.headers.get("content-type", "")


def test_agent_feedback(client: TestClient) -> None:
    res = client.post(
        "/feedback/agent",
        headers=HUB_HEADERS,
        json={
            "agent_id": "coo",
            "response_id": "resp-123",
            "rating": 1,
        },
    )
    assert res.status_code == 200
    assert res.json()["recorded"] is True


def test_plugins_list(client: TestClient) -> None:
    res = client.get("/plugins", headers=HUB_HEADERS)
    assert res.status_code == 200
    plugins = res.json()
    assert any(p["id"] == "example_echo" for p in plugins)


def test_plugin_run(client: TestClient) -> None:
    res = client.post(
        "/plugins/example_echo/run",
        headers=HUB_HEADERS,
        json={"message": "hello"},
    )
    assert res.status_code == 200
    assert res.json()["echo"] == "hello"


def test_personality_get_set(client: TestClient) -> None:
    res = client.put(
        "/personality",
        headers=HUB_HEADERS,
        json={"tone": "concise", "vocabulary": "business", "emoji": False, "response_length": 500},
    )
    assert res.status_code == 200
    assert res.json()["saved"] is True

    res2 = client.get("/personality", headers=HUB_HEADERS)
    assert res2.json()["overrides"]["tone"] == "concise"
