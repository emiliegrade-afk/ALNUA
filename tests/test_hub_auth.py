"""H2 security — scoped hub keys, IP allowlist, middleware exemptions."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from tests.conftest import FakeDB


def _mock_settings(**overrides: str) -> MagicMock:
    defaults = {
        "hub_api_key": "master-key",
        "hub_api_key_web": "",
        "hub_api_key_n8n": "",
        "hub_api_key_mcp": "",
        "hub_api_key_cursor": "",
        "hub_ip_allowlist": "",
    }
    defaults.update(overrides)
    mock = MagicMock()
    for name, value in defaults.items():
        setattr(mock, name, value)
    return mock


def test_valid_hub_api_keys_master_only() -> None:
    from services.hub_auth import valid_hub_api_keys

    with patch("services.hub_auth.get_settings", return_value=_mock_settings()):
        assert valid_hub_api_keys() == ["master-key"]


def test_valid_hub_api_keys_includes_scoped_channels() -> None:
    from services.hub_auth import valid_hub_api_keys

    with patch(
        "services.hub_auth.get_settings",
        return_value=_mock_settings(
            hub_api_key_web="web-key",
            hub_api_key_n8n="n8n-key",
        ),
    ):
        keys = valid_hub_api_keys()
        assert keys == ["master-key", "web-key", "n8n-key"]


def test_hub_api_key_valid_master_key() -> None:
    from services.hub_auth import hub_api_key_valid

    with patch("services.hub_auth.get_settings", return_value=_mock_settings()):
        assert hub_api_key_valid("master-key") is True


def test_hub_api_key_valid_channel_key() -> None:
    from services.hub_auth import hub_api_key_valid

    with patch(
        "services.hub_auth.get_settings",
        return_value=_mock_settings(hub_api_key_mcp="mcp-only-key"),
    ):
        assert hub_api_key_valid("mcp-only-key") is True
        assert hub_api_key_valid("master-key") is True


def test_hub_api_key_valid_wrong_key() -> None:
    from services.hub_auth import hub_api_key_valid

    with patch("services.hub_auth.get_settings", return_value=_mock_settings()):
        assert hub_api_key_valid("wrong-key") is False
        assert hub_api_key_valid(None) is False
        assert hub_api_key_valid("") is False


def test_client_ip_allowed_empty_allowlist() -> None:
    from services.hub_auth import client_ip_allowed

    with patch("services.hub_auth.get_settings", return_value=_mock_settings()):
        assert client_ip_allowed("203.0.113.50") is True
        assert client_ip_allowed(None) is True


def test_client_ip_allowed_exact_match() -> None:
    from services.hub_auth import client_ip_allowed

    with patch(
        "services.hub_auth.get_settings",
        return_value=_mock_settings(hub_ip_allowlist="127.0.0.1, 10.0.0.5"),
    ):
        assert client_ip_allowed("127.0.0.1") is True
        assert client_ip_allowed("10.0.0.5") is True
        assert client_ip_allowed("203.0.113.50") is False
        assert client_ip_allowed(None) is False


def test_middleware_reexports_hub_api_key_valid() -> None:
    from api.middleware import hub_api_key_valid as mw_valid
    from services.hub_auth import hub_api_key_valid as auth_valid

    assert mw_valid is auth_valid


def test_is_hub_api_key_exempt_secretary_webhook() -> None:
    from api.middleware import _is_hub_api_key_exempt

    assert _is_hub_api_key_exempt("/webhook/telegram/secretary", "POST") is True
    assert _is_hub_api_key_exempt("/webhook/telegram/secretary", "GET") is False
    assert _is_hub_api_key_exempt("/projects", "GET") is False


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("HUB_API_KEY", "test-hub-key-for-ci")
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.delenv("HUB_IP_ALLOWLIST", raising=False)
    from config.settings import get_settings

    get_settings.cache_clear()
    monkeypatch.setattr("database.supabase_client.get_supabase", lambda: FakeDB())
    from api.app import app

    return TestClient(app)


def test_middleware_rejects_unknown_ip_when_allowlist_set(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HUB_IP_ALLOWLIST", "10.0.0.99")
    from config.settings import get_settings

    get_settings.cache_clear()

    res = client.get(
        "/projects",
        headers={"X-Hub-Key": "test-hub-key-for-ci"},
    )
    assert res.status_code == 403
    assert "IP" in res.json()["detail"]


def test_middleware_accepts_scoped_channel_key(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HUB_API_KEY_WEB", "web-scoped-key")
    from config.settings import get_settings

    get_settings.cache_clear()

    res = client.get("/projects", headers={"X-Hub-Key": "web-scoped-key"})
    assert res.status_code == 200
