"""API middleware and auth exemption tests."""

from __future__ import annotations

import os
from typing import Any

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-supabase-key")
os.environ.setdefault("OPENROUTER_API_KEY", "test-openrouter-key")
os.environ.setdefault("HUB_API_KEY", "test-hub-key-for-ci")
os.environ.setdefault("ENVIRONMENT", "development")


class _FakeDB:
    def select(self, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        return []


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("HUB_API_KEY", "test-hub-key-for-ci")
    from config.settings import get_settings

    get_settings.cache_clear()
    monkeypatch.setattr("database.supabase_client.get_supabase", lambda: _FakeDB())
    from api.app import app

    return TestClient(app)


def test_health_is_public(client: TestClient) -> None:
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_protected_route_requires_hub_key(client: TestClient) -> None:
    res = client.get("/projects")
    assert res.status_code == 401


def test_protected_route_with_valid_hub_key(client: TestClient) -> None:
    res = client.get("/projects", headers={"X-Hub-Key": "test-hub-key-for-ci"})
    assert res.status_code == 200
    assert res.json() == []
