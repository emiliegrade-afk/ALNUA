"""CreatorFlow API tests — Sprint 0–4."""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Any

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-supabase-key")
os.environ.setdefault("OPENROUTER_API_KEY", "test-openrouter-key")
os.environ.setdefault("HUB_API_KEY", "test-hub-key-for-ci")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("CF_EXPORT_MODE", "mock")

HUB_HEADERS = {"X-Hub-Key": "test-hub-key-for-ci"}
USER_ID = str(uuid.uuid4())


class _FakeStorageBucket:
    def upload(self, path: str, content: bytes, file_options: dict | None = None) -> None:
        return None

    def download(self, path: str) -> bytes:
        return b"fake-video-bytes"

    def create_signed_url(self, path: str, expires_in: int) -> dict[str, str]:
        return {"signedURL": f"https://cdn.test/signed/{path}?e={expires_in}"}


class _FakeCfDB:
    def __init__(self) -> None:
        self._assets: dict[str, dict[str, Any]] = {}
        self._calendar: dict[str, dict[str, Any]] = {}
        self._exports: dict[str, dict[str, Any]] = {}
        self._platforms: dict[str, dict[str, Any]] = {}
        self._projects: dict[str, dict[str, Any]] = {}
        self.raw = type(
            "Raw",
            (),
            {"storage": type("S", (), {"from_": lambda _s, _b: _FakeStorageBucket()})()},
        )()

    def _store(self, table: str) -> dict[str, dict[str, Any]]:
        return {
            "cf_assets": self._assets,
            "cf_calendar_entries": self._calendar,
            "cf_exports": self._exports,
            "cf_platform_connections": self._platforms,
            "cf_projects": self._projects,
        }[table]

    def select(
        self,
        table: str,
        columns: str = "*",
        filters: dict[str, Any] | None = None,
        is_null: list[str] | None = None,
        order_by: str | None = None,
        ascending: bool = True,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        store = self._store(table)
        filters = filters or {}
        rows = list(store.values())
        for key, value in filters.items():
            rows = [r for r in rows if r.get(key) == value]
        if order_by:
            rows.sort(key=lambda r: r.get(order_by, ""), reverse=not ascending)
        if limit is not None:
            rows = rows[:limit]
        return rows

    def insert(self, table: str, row: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        record_id = str(uuid.uuid4())
        store = self._store(table)
        if table == "cf_assets":
            stored = {
                "id": record_id,
                "metadata": {},
                "ai_analysis": {},
                "created_at": now,
                "updated_at": now,
                **row,
            }
        elif table == "cf_exports":
            stored = {
                "id": record_id,
                "adapted_metadata": {},
                "created_at": now,
                **row,
            }
        else:
            stored = {
                "id": record_id,
                "status": row.get("status", "draft"),
                "created_at": now,
                "updated_at": now,
                **row,
            }
        store[record_id] = stored
        return stored

    def update(
        self,
        table: str,
        row_id: str,
        values: dict[str, Any],
        id_column: str = "id",
    ) -> dict[str, Any]:
        store = self._store(table)
        if row_id not in store:
            raise RuntimeError(f"Update on {table} id={row_id} returned no data")
        store[row_id] = {**store[row_id], **values}
        return store[row_id]

    def delete(self, table: str, row_id: str, id_column: str = "id") -> None:
        self._store(table).pop(row_id, None)


@pytest.fixture()
def fake_db() -> _FakeCfDB:
    return _FakeCfDB()


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch, fake_db: _FakeCfDB) -> TestClient:
    monkeypatch.setenv("HUB_API_KEY", "test-hub-key-for-ci")
    monkeypatch.setenv("CF_EXPORT_MODE", "mock")
    monkeypatch.setenv("CREATORFLOW_SUPABASE_URL", "https://cf-test.supabase.co")
    monkeypatch.setenv("CREATORFLOW_SUPABASE_SERVICE_ROLE_KEY", "test-cf-service-key")
    from config.settings import get_settings

    get_settings.cache_clear()
    for mod in (
        "services.creatorflow_export_runner",
        "services.creatorflow_platforms",
        "services.creatorflow_stats",
        "services.creatorflow_projects",
        "api.routers.creatorflow",
    ):
        monkeypatch.setattr(f"{mod}.get_cf_supabase", lambda: fake_db)
    monkeypatch.setattr(
        "agents.cf_timing_optimizer.get_cf_timing_suggestions",
        lambda user_id, platform, db=None: [
            {
                "platform": platform,
                "suggested_at": "2026-06-20T18:00:00+00:00",
                "score": 0.91,
                "reason": "Test slot",
            }
        ],
    )
    monkeypatch.setattr(
        "services.creatorflow_platforms.has_active_connection",
        lambda _uid, _toolkit: False,
    )
    _connect_mock = lambda platform, user_id: {
        "platform": platform,
        "oauth_url": f"https://composio.dev/oauth/{platform}",
        "already_connected": False,
        "message": None,
    }
    _sync_mock = lambda user_id, platform, db=None: {
        "platform": platform,
        "is_active": True,
        "platform_username": "test_channel",
        "connected_at": datetime.now(timezone.utc).isoformat(),
    }
    monkeypatch.setattr(
        "services.creatorflow_platforms.start_cf_platform_connect",
        _connect_mock,
    )
    monkeypatch.setattr(
        "api.routers.creatorflow.start_cf_platform_connect",
        _connect_mock,
    )
    monkeypatch.setattr(
        "services.creatorflow_platforms.sync_cf_platform_connection",
        _sync_mock,
    )
    monkeypatch.setattr(
        "api.routers.creatorflow.sync_cf_platform_connection",
        _sync_mock,
    )
    monkeypatch.setattr(
        "services.creatorflow_platforms.list_cf_platform_status",
        lambda user_id, db=None: [
            {"platform": "youtube", "is_active": False, "platform_username": None, "connected_at": None},
            {"platform": "instagram", "is_active": False, "platform_username": None, "connected_at": None},
        ],
    )

    def _mock_run_export(export_id: str, user_id: str, db: Any) -> None:
        entries = db.select("cf_exports", filters={"id": export_id}, limit=1)
        if not entries:
            return
        entry_id = entries[0]["calendar_entry_id"]
        db.update("cf_exports", export_id, {"status": "processing"})
        db.update(
            "cf_exports",
            export_id,
            {
                "status": "success",
                "platform_post_id": f"mock_{export_id[:8]}",
                "platform_post_url": f"https://youtube.com/post/mock_{export_id[:8]}",
                "adapted_metadata": {"publish_mode": "mock"},
            },
        )
        db.update("cf_calendar_entries", entry_id, {"status": "exported"})

    monkeypatch.setattr("services.creatorflow_export_runner.run_cf_export", _mock_run_export)
    monkeypatch.setattr("api.routers.creatorflow.run_cf_export", _mock_run_export)

    from api.app import app

    return TestClient(app)


def test_creatorflow_health_sprint4(client: TestClient) -> None:
    res = client.get("/creatorflow/health", headers=HUB_HEADERS)
    assert res.status_code == 200
    assert res.json()["sprint"] == "studio-v3"


def test_cf_projects_default_and_create(client: TestClient) -> None:
    user_headers = {**HUB_HEADERS, "X-User-Id": USER_ID}
    listed = client.get("/creatorflow/projects", headers=user_headers)
    assert listed.status_code == 200
    projects = listed.json()
    assert len(projects) >= 1
    assert projects[0]["is_default"] is True

    created = client.post(
        "/creatorflow/projects",
        headers=user_headers,
        json={"name": "Campagne été"},
    )
    assert created.status_code == 201
    assert created.json()["name"] == "Campagne été"

    again = client.get("/creatorflow/projects", headers=user_headers)
    assert len(again.json()) >= 2


def test_cf_export_stats(client: TestClient) -> None:
    user_headers = {**HUB_HEADERS, "X-User-Id": USER_ID}
    scheduled = datetime(2026, 6, 20, 18, 0, tzinfo=timezone.utc).isoformat()
    entry = client.post(
        "/creatorflow/calendar",
        headers=user_headers,
        json={"platform": "youtube", "scheduled_at": scheduled, "title": "Stats test"},
    ).json()
    client.post(
        "/creatorflow/exports",
        headers=user_headers,
        json={"calendar_entry_id": entry["id"], "platform": "youtube"},
    )
    stats = client.get("/creatorflow/stats/exports", headers=user_headers)
    assert stats.status_code == 200
    body = stats.json()
    assert body["total"] >= 1
    assert "success_rate_pct" in body


def test_cf_platform_connect(client: TestClient) -> None:
    user_headers = {**HUB_HEADERS, "X-User-Id": USER_ID}
    res = client.post(
        "/creatorflow/platforms/connect",
        headers=user_headers,
        json={"platform": "youtube"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["platform"] == "youtube"
    assert body["oauth_url"].startswith("https://")


def test_cf_platform_sync(client: TestClient) -> None:
    user_headers = {**HUB_HEADERS, "X-User-Id": USER_ID}
    res = client.post(
        "/creatorflow/platforms/sync?platform=instagram",
        headers=user_headers,
    )
    assert res.status_code == 200
    assert res.json()[0]["is_active"] is True


def test_cf_export_rate_limit(client: TestClient) -> None:
    rate_user = str(uuid.uuid4())
    user_headers = {**HUB_HEADERS, "X-User-Id": rate_user}
    scheduled = datetime(2026, 6, 20, 18, 0, tzinfo=timezone.utc).isoformat()
    entry = client.post(
        "/creatorflow/calendar",
        headers=user_headers,
        json={"platform": "youtube", "scheduled_at": scheduled, "title": "Rate test"},
    ).json()

    from config.settings import get_settings

    get_settings.cache_clear()
    limit = get_settings().cf_export_daily_limit

    for _ in range(limit):
        r = client.post(
            "/creatorflow/exports",
            headers=user_headers,
            json={"calendar_entry_id": entry["id"], "platform": "youtube"},
        )
        assert r.status_code == 201

    blocked = client.post(
        "/creatorflow/exports",
        headers=user_headers,
        json={"calendar_entry_id": entry["id"], "platform": "youtube"},
    )
    assert blocked.status_code == 429


def test_cf_export_flow(client: TestClient) -> None:
    user_headers = {**HUB_HEADERS, "X-User-Id": USER_ID}
    scheduled = datetime(2026, 6, 20, 18, 0, tzinfo=timezone.utc).isoformat()
    entry = client.post(
        "/creatorflow/calendar",
        headers=user_headers,
        json={"platform": "youtube", "scheduled_at": scheduled, "title": "Launch teaser"},
    ).json()

    export = client.post(
        "/creatorflow/exports",
        headers=user_headers,
        json={"calendar_entry_id": entry["id"], "platform": "youtube"},
    )
    assert export.status_code == 201
    export_id = export.json()["id"]

    detail = client.get(f"/creatorflow/exports/{export_id}", headers=user_headers)
    assert detail.status_code == 200
    assert detail.json()["status"] == "success"
