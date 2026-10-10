"""Shared pytest fixtures for ALNUA Hub tests."""

from __future__ import annotations

import os
import tempfile
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-supabase-key")
os.environ.setdefault("OPENROUTER_API_KEY", "test-openrouter-key")
os.environ.setdefault("HUB_API_KEY", "test-hub-key-for-ci")
os.environ.setdefault("ENVIRONMENT", "development")

# Session-level hermetic hub repo (DEC-043): anything resolving data paths via
# get_hub_repo_path() — trust store, idle queue, cost log — lands in a session
# tmp dir, even if a module is re-imported or a background thread outlives its
# test (monkeypatch alone proved leaky: suite runs polluted the live store).
_TESTS_REPO_ROOT = tempfile.mkdtemp(prefix="alnua_hub_tests_")
os.environ["HUB_REPO_PATH"] = _TESTS_REPO_ROOT

HUB_HEADERS = {"X-Hub-Key": "test-hub-key-for-ci"}


@pytest.fixture(autouse=True)
def _isolate_agent_trust_store(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the trust store hermetic: engine paths (academy QA outcomes, review
    board, validation recipes) record trust on real agents — tests must never
    write to the live data/agent_trust.json (DEC-043)."""
    from config.paths import get_hub_repo_path
    from services import agent_trust

    get_hub_repo_path.cache_clear()
    monkeypatch.setattr(agent_trust, "_STORE", tmp_path / "agent_trust.json")


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
