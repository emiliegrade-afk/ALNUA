"""Phase 1 security — beta admin auth, webhooks, hub key."""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from tests.conftest import FakeDB

HUB_HEADERS = {"X-Hub-Key": "test-hub-key-for-ci"}


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("HUB_API_KEY", "test-hub-key-for-ci")
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("SENTRY_WEBHOOK_ALLOW_UNSIGNED", "0")
    monkeypatch.delenv("SENTRY_WEBHOOK_SECRET", raising=False)
    monkeypatch.delenv("TELEGRAM_WEBHOOK_SECRET", raising=False)
    from config.settings import get_settings

    get_settings.cache_clear()
    monkeypatch.setattr("database.supabase_client.get_supabase", lambda: FakeDB())
    from api.app import app

    return TestClient(app)


@pytest.mark.parametrize(
    "method,path",
    [
        ("GET", "/beta/testers"),
        ("GET", "/beta/testers/export"),
        ("GET", "/beta/feedback"),
        ("GET", "/beta/stats"),
        ("POST", "/beta/invite"),
    ],
)
def test_beta_admin_routes_require_hub_key(
    client: TestClient,
    method: str,
    path: str,
) -> None:
    res = client.request(method, path, json={"project_id": "x"} if method == "POST" else None)
    assert res.status_code == 401


def test_beta_public_info_not_hub_key_gated(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """Public tester route must not return 401 (404 when project missing is OK)."""
    monkeypatch.setattr(
        "api.routers.beta.resolve_project_by_slug",
        lambda db, slug: {
            "id": "proj-1",
            "name": "Demo",
            "description": "Test",
            "status": "active",
        },
    )
    monkeypatch.setattr("api.routers.beta.latest_app_version", lambda db, pid: "1.0.0")
    res = client.get("/beta/info/demo-app")
    assert res.status_code == 200


def test_beta_public_register_not_hub_key_gated(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "api.routers.beta.resolve_project_by_slug",
        lambda db, slug: {"id": "proj-1", "name": "Demo", "status": "active"},
    )
    monkeypatch.setattr("api.routers.beta.latest_app_version", lambda db, pid: "1.0.0")

    class RegisterDB(FakeDB):
        def select(self, *args: Any, **kwargs: Any) -> list:
            return []

        def insert(self, *args: Any, **kwargs: Any) -> dict:
            return {
                "id": "tester-1",
                "first_name": "Test",
                "app_version": "1.0.0",
                "feedback_count": 0,
            }

    monkeypatch.setattr("api.routers.beta.get_supabase", lambda: RegisterDB())
    res = client.post(
        "/beta/register",
        json={
            "project_slug": "demo",
            "email": "t@test.com",
            "first_name": "Test",
        },
    )
    assert res.status_code == 200


def test_sentry_webhook_rejects_unsigned_when_no_allow_flag(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SENTRY_WEBHOOK_ALLOW_UNSIGNED", "0")
    monkeypatch.delenv("SENTRY_WEBHOOK_SECRET", raising=False)
    from config.settings import get_settings

    get_settings.cache_clear()

    body = {"action": "created", "data": {"issue": {"title": "x", "level": "error"}}}
    res = client.post("/webhook/sentry", json=body)
    assert res.status_code == 401


def test_sentry_webhook_accepts_with_valid_signature(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret = "sentry-test-secret"
    monkeypatch.setenv("SENTRY_WEBHOOK_SECRET", secret)
    monkeypatch.setenv("SENTRY_WEBHOOK_ALLOW_UNSIGNED", "0")
    monkeypatch.setenv("SENTRY_AUTO_ISSUE", "false")
    from config.settings import get_settings

    get_settings.cache_clear()

    payload = {"action": "resolved", "data": {}}
    raw = json.dumps(payload).encode("utf-8")
    sig = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()

    with patch("services.production_ops.run_sentry_webhook") as mock_run:
        mock_run.return_value = {"success": True, "action": "ignored"}
        res = client.post(
            "/webhook/sentry",
            content=raw,
            headers={
                "Content-Type": "application/json",
                "Sentry-Hook-Signature": sig,
            },
        )
    assert res.status_code == 200
    mock_run.assert_called_once()


def test_sentry_webhook_allow_unsigned_dev_opt_in(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SENTRY_WEBHOOK_ALLOW_UNSIGNED", "1")
    monkeypatch.delenv("SENTRY_WEBHOOK_SECRET", raising=False)
    from config.settings import get_settings

    get_settings.cache_clear()

    with patch("services.production_ops.run_sentry_webhook") as mock_run:
        mock_run.return_value = {"success": True, "action": "ignored"}
        res = client.post("/webhook/sentry", json={"action": "resolved", "data": {}})
    assert res.status_code == 200


def test_telegram_webhook_rejects_bad_secret(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:ABC")
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "expected-secret")
    from config.settings import get_settings

    get_settings.cache_clear()

    res = client.post(
        "/webhook/telegram",
        json={"update_id": 1},
        headers={"X-Telegram-Bot-Api-Secret-Token": "wrong"},
    )
    assert res.status_code == 401


def test_telegram_webhook_accepts_valid_secret(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret = "expected-secret"
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:ABC")
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", secret)
    from config.settings import get_settings

    get_settings.cache_clear()

    mock_bot = MagicMock()
    mock_bot.process_update = AsyncMock()
    with patch("api.routers.releases.get_telegram_bot", return_value=mock_bot):
        res = client.post(
            "/webhook/telegram",
            json={"update_id": 1},
            headers={"X-Telegram-Bot-Api-Secret-Token": secret},
        )
    assert res.status_code == 200
    assert res.json() == {"ok": True}


def test_orchestration_sentry_ingest_uses_trusted_relay(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with patch("services.production_ops.run_sentry_webhook") as mock_run:
        mock_run.return_value = {"success": True, "action": "ignored", "workflow": "sentry_ingest"}
        res = client.post(
            "/orchestration/sentry-ingest",
            headers=HUB_HEADERS,
            json={"action": "created", "data": {}},
        )
    assert res.status_code == 200
    _, kwargs = mock_run.call_args
    assert kwargs.get("trusted_relay") is True


def test_hub_api_key_valid_uses_compare_digest() -> None:
    from api.middleware import hub_api_key_valid

    with patch("api.middleware.get_settings") as mock_settings:
        mock_settings.return_value.hub_api_key = "secret-key"
        assert hub_api_key_valid("secret-key") is True
        assert hub_api_key_valid("secret-ke") is False
        assert hub_api_key_valid(None) is False
