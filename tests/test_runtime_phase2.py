"""Phase 2 — supabase client + releases routing."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

HUB_HEADERS = {"X-Hub-Key": "test-hub-key-for-ci"}


def test_insert_many_raises_when_no_data() -> None:
    from database.supabase_client import SupabaseClient

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.data = None
    mock_client.table.return_value.insert.return_value.execute.return_value = mock_response
    db = SupabaseClient(mock_client)

    with pytest.raises(RuntimeError, match="Insert into widgets returned no data"):
        db.insert_many("widgets", [{"id": "1"}])


def test_insert_many_empty_list_is_noop() -> None:
    from database.supabase_client import SupabaseClient

    db = SupabaseClient(MagicMock())
    assert db.insert_many("widgets", []) == []


def test_get_supabase_warns_without_service_role(monkeypatch: pytest.MonkeyPatch) -> None:
    from config.settings import get_settings
    from database import supabase_client

    supabase_client.get_supabase.cache_clear()
    supabase_client._service_role_warned = False
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "")
    get_settings.cache_clear()

    with patch("database.supabase_client.create_client") as mock_create:
        mock_create.return_value = MagicMock()
        with patch.object(supabase_client.logger, "warning") as mock_warn:
            supabase_client.get_supabase()
            mock_warn.assert_called_once()

    supabase_client.get_supabase.cache_clear()
    get_settings.cache_clear()


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("HUB_API_KEY", "test-hub-key-for-ci")
    from config.settings import get_settings

    get_settings.cache_clear()
    from api.app import app

    return TestClient(app)


def test_get_releases_generate_returns_405_not_404(client: TestClient) -> None:
    res = client.get("/releases/generate", headers=HUB_HEADERS)
    assert res.status_code == 405
    assert "POST" in res.json()["detail"]
