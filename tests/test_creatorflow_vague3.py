"""CreatorFlow V3 — idea → asset → calendar pipeline."""

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
os.environ.setdefault("JWT_SECRET", "test-jwt-secret")
os.environ.setdefault("ENVIRONMENT", "development")

HUB_HEADERS = {"X-Hub-Key": "test-hub-key-for-ci"}
USER_ID = str(uuid.uuid4())


class _FakePipelineDB:
    def __init__(self) -> None:
        self._ideas: dict[str, dict[str, Any]] = {}
        self._assets: dict[str, dict[str, Any]] = {}
        self._calendar: dict[str, dict[str, Any]] = {}
        self._artifacts: dict[str, dict[str, Any]] = {}
        self._projects: dict[str, dict[str, Any]] = {}

    def _store(self, table: str) -> dict[str, dict[str, Any]]:
        return {
            "cf_ideas": self._ideas,
            "cf_assets": self._assets,
            "cf_calendar_entries": self._calendar,
            "cf_idea_artifacts": self._artifacts,
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
        store = self._store(table)
        record_id = row.get("id") or str(uuid.uuid4())
        stored = {"id": record_id, "created_at": now, "updated_at": now, **row}
        if table == "cf_ideas":
            stored.setdefault("tags", [])
            stored.setdefault("status", "spark")
        if table == "cf_calendar_entries":
            stored.setdefault("hashtags", [])
            stored.setdefault("status", "scheduled")
        store[record_id] = stored
        return stored

    def update(self, table: str, row_id: str, values: dict[str, Any], id_column: str = "id") -> dict[str, Any]:
        store = self._store(table)
        if row_id not in store:
            raise RuntimeError(f"Update on {table} id={row_id} returned no data")
        store[row_id] = {**store[row_id], **values, "updated_at": datetime.now(timezone.utc).isoformat()}
        return store[row_id]


@pytest.fixture()
def pipeline_client(monkeypatch: pytest.MonkeyPatch) -> tuple[TestClient, _FakePipelineDB]:
    monkeypatch.setenv("HUB_API_KEY", "test-hub-key-for-ci")
    monkeypatch.setenv("CREATORFLOW_SUPABASE_URL", "https://cf-test.supabase.co")
    monkeypatch.setenv("CREATORFLOW_SUPABASE_SERVICE_ROLE_KEY", "test-cf-service-key")
    from config.settings import get_settings

    get_settings.cache_clear()
    fake_db = _FakePipelineDB()
    project_id = str(uuid.uuid4())
    fake_db.insert(
        "cf_projects",
        {"id": project_id, "user_id": USER_ID, "name": "Mon projet", "slug": "mon-projet", "is_default": True},
    )

    for mod in (
        "services.creatorflow_projects",
        "services.creatorflow_ideas",
        "services.creatorflow_brainstorm",
        "services.creatorflow_pipeline",
        "services.studio.jobs",
    ):
        monkeypatch.setattr(f"{mod}.get_cf_supabase", lambda: fake_db)

    from api.app import app

    return TestClient(app), fake_db


def test_cf_health_v3(pipeline_client: tuple[TestClient, _FakePipelineDB]) -> None:
    client, _ = pipeline_client
    res = client.get("/creatorflow/health", headers=HUB_HEADERS)
    assert res.status_code == 200
    assert res.json()["sprint"] == "studio-v3"


def test_cf_idea_pipeline_schedule_link(pipeline_client: tuple[TestClient, _FakePipelineDB]) -> None:
    client, db = pipeline_client
    headers = {**HUB_HEADERS, "X-User-Id": USER_ID}

    idea = client.post(
        "/creatorflow/ideas",
        headers=headers,
        json={"content": "Reel productivité", "title": "3 hacks"},
    ).json()
    idea_id = idea["id"]

    asset = db.insert(
        "cf_assets",
        {
            "user_id": USER_ID,
            "title": "Export final",
            "file_url": "https://cdn.example.com/v.mp4",
            "file_type": "video",
            "status": "pending",
        },
    )

    link = client.post(
        f"/creatorflow/ideas/{idea_id}/link-asset",
        headers=headers,
        json={"asset_id": asset["id"]},
    )
    assert link.status_code == 200
    assert link.json()["idea"]["linked_asset_id"] == asset["id"]

    db.insert(
        "cf_idea_artifacts",
        {
            "idea_id": idea_id,
            "user_id": USER_ID,
            "artifact_type": "script",
            "version": 1,
            "content": {"hook": "Accroche", "sections": [], "cta": "Abonne-toi"},
        },
    )

    pipe = client.get(f"/creatorflow/ideas/{idea_id}/pipeline", headers=headers)
    assert pipe.status_code == 200
    body = pipe.json()
    assert body["steps"]["asset"] is True
    assert body["asset"]["id"] == asset["id"]

    sched = client.post(
        f"/creatorflow/ideas/{idea_id}/schedule",
        headers=headers,
        json={"platform": "youtube", "title": "3 hacks productivité"},
    )
    assert sched.status_code == 200
    entry = sched.json()
    assert entry["platform"] == "youtube"
    assert entry["asset_id"] == asset["id"]

    pipe2 = client.get(f"/creatorflow/ideas/{idea_id}/pipeline", headers=headers)
    assert pipe2.json()["steps"]["scheduled"] is True
    assert pipe2.json()["calendar_entry"]["id"] == entry["id"]
