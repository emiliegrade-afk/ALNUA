"""HUB_API_KEY enforcement — mandatory in every environment (SEC-002, 2026-07-25).

Supersedes the old "Phase 6 — DevEx" behavior that allowed an open dev mode
without a key. See DECISIONS.md / BUGS.md SEC-002 for why that was reversed.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-supabase-key")
os.environ.setdefault("OPENROUTER_API_KEY", "test-openrouter-key")


class _FakeDB:
    def select(self, *args, **kwargs):
        return []


def _clear_settings_cache(monkeypatch: pytest.MonkeyPatch, **env: str) -> None:
    # Import BEFORE mutating env: config/__init__.py eagerly builds a module-level
    # `settings = get_settings()` on first import — if that first import happens
    # while HUB_API_KEY is already patched empty, the import itself raises before
    # we ever reach a `pytest.raises` block. Importing first (while conftest.py's
    # valid default HUB_API_KEY is still in effect) sidesteps that ordering trap.
    from config.settings import get_settings

    for key, value in env.items():
        monkeypatch.setenv(key, value)
    get_settings.cache_clear()


@pytest.mark.parametrize("environment", ["development", "staging", "production"])
def test_settings_requires_hub_key_in_every_environment(
    monkeypatch: pytest.MonkeyPatch, environment: str
) -> None:
    _clear_settings_cache(monkeypatch, HUB_API_KEY="", ENVIRONMENT=environment)
    from config.settings import Settings

    with pytest.raises(ValueError, match="HUB_API_KEY is required"):
        Settings(
            SUPABASE_URL="https://example.supabase.co",
            SUPABASE_KEY="k",
            OPENROUTER_API_KEY="k",
            ENVIRONMENT=environment,
            HUB_API_KEY="",
        )


def test_app_requires_hub_key_to_boot(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_settings_cache(monkeypatch, HUB_API_KEY="", ENVIRONMENT="development")
    monkeypatch.setattr("database.supabase_client.get_supabase", lambda: _FakeDB())
    from config.settings import get_settings

    with pytest.raises(ValueError, match="HUB_API_KEY is required"):
        get_settings()


def test_dev_with_hub_key_still_requires_header(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_settings_cache(
        monkeypatch,
        HUB_API_KEY="dev-local-key",
        ENVIRONMENT="development",
    )
    monkeypatch.setattr("database.supabase_client.get_supabase", lambda: _FakeDB())
    from api.app import app

    client = TestClient(app)
    assert client.get("/projects").status_code == 401
    res = client.get("/projects", headers={"X-Hub-Key": "dev-local-key"})
    assert res.status_code == 200


def test_hub_api_key_valid_false_when_expected_key_empty() -> None:
    """Defense in depth: even if settings somehow carried an empty key
    (e.g. mocked), hub_api_key_valid must never treat that as "open"."""
    from api.middleware import hub_api_key_valid

    with patch("services.hub_auth.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(
            hub_api_key="",
            hub_api_key_web="",
            hub_api_key_n8n="",
            hub_api_key_mcp="",
            hub_api_key_cursor="",
            hub_ip_allowlist="",
        )
        assert hub_api_key_valid("anything") is False
        assert hub_api_key_valid(None) is False
