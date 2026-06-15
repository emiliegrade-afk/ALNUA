"""Shared pytest fixtures for ALNUA Hub tests."""

from __future__ import annotations

import os
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-supabase-key")
os.environ.setdefault("OPENROUTER_API_KEY", "test-openrouter-key")
os.environ.setdefault("HUB_API_KEY", "test-hub-key-for-ci")
os.environ.setdefault("ENVIRONMENT", "development")

HUB_HEADERS = {"X-Hub-Key": "test-hub-key-for-ci"}


class FakeDB:
    """Minimal Supabase stand-in for API tests."""

    def select(self, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        return []

    def insert(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return {"id": "fake-id"}

    def insert_many(self, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        return [{"id": "fake-id"}]

    def update(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return {"id": "fake-id"}

    def table(self, name: str) -> "FakeDB":
        return self

    def select_columns(self, *args: Any, **kwargs: Any) -> "FakeDB":
        return self

    def order(self, *args: Any, **kwargs: Any) -> "FakeDB":
        return self

    def limit(self, *args: Any, **kwargs: Any) -> "FakeDB":
        return self

    def delete(self) -> "FakeDB":
        return self

    def eq(self, *args: Any, **kwargs: Any) -> "FakeDB":
        return self

    def ilike(self, *args: Any, **kwargs: Any) -> "FakeDB":
        return self

    def execute(self) -> MagicMock:
        m = MagicMock()
        m.data = []
        return m


@pytest.fixture()
def hub_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    from config.settings import get_settings

    monkeypatch.setenv("HUB_API_KEY", "test-hub-key-for-ci")
    get_settings.cache_clear()
    monkeypatch.setattr("database.supabase_client.get_supabase", lambda: FakeDB())
    from api.app import app

    return TestClient(app)
