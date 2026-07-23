"""Phase 6 — DevEx: optional dev HUB_API_KEY, BYOK Fernet, open dev middleware."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-supabase-key")
os.environ.setdefault("OPENROUTER_API_KEY", "test-openrouter-key")


class _FakeDB:
    def select(self, *args, **kwargs):
        return []


def _clear_settings_cache(monkeypatch: pytest.MonkeyPatch, **env: str) -> None:
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    from config.settings import get_settings

    get_settings.cache_clear()


def test_settings_allows_missing_hub_key_in_development(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_settings_cache(monkeypatch, HUB_API_KEY="", ENVIRONMENT="development")
    from config.settings import get_settings

    settings = get_settings()
    assert settings.hub_api_key == ""


def test_settings_requires_hub_key_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_settings_cache(monkeypatch, HUB_API_KEY="", ENVIRONMENT="production")
    from config.settings import Settings

    with pytest.raises(ValueError, match="HUB_API_KEY is required"):
        Settings(
            SUPABASE_URL="https://example.supabase.co",
            SUPABASE_KEY="k",
            OPENROUTER_API_KEY="k",
            ENVIRONMENT="production",
            HUB_API_KEY="",
        )


def test_dev_open_mode_skips_hub_key_on_protected_route(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_settings_cache(monkeypatch, HUB_API_KEY="", ENVIRONMENT="development")
    monkeypatch.setattr("database.supabase_client.get_supabase", lambda: _FakeDB())
    import api.middleware as mw

    mw._warned_open_dev_api = False
    from api.app import app

    client = TestClient(app)
    res = client.get("/projects")
    assert res.status_code == 200


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


def test_hub_api_key_valid_open_when_enforcement_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_settings_cache(monkeypatch, HUB_API_KEY="", ENVIRONMENT="development")
    from api.middleware import hub_api_key_valid

    assert hub_api_key_valid(None) is True
