"""CreatorFlow Studio — catalog, jobs, and async runner."""

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
os.environ.setdefault("STUDIO_GOOGLE_API_KEY", "test-google-key")
os.environ.setdefault("HUB_API_KEY", "test-hub-key-for-ci")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret")
os.environ.setdefault("ENVIRONMENT", "development")

HUB_HEADERS = {"X-Hub-Key": "test-hub-key-for-ci"}
USER_ID = str(uuid.uuid4())
FAKE_MP4 = b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00"
FAKE_WAV = b"RIFF\x24\x00\x00\x00WAVEfmt "


class _FakeStudioDB:
    def __init__(self) -> None:
        self._ideas: dict[str, dict[str, Any]] = {}
        self._jobs: dict[str, dict[str, Any]] = {}
        self._assets: dict[str, dict[str, Any]] = {}
        self._projects: dict[str, dict[str, Any]] = {}
        self._dna: dict[str, dict[str, Any]] = {}
        self._artifacts: dict[str, dict[str, Any]] = {}

    def _store(self, table: str) -> dict[str, dict[str, Any]]:
        return {
            "cf_ideas": self._ideas,
            "cf_studio_jobs": self._jobs,
            "cf_assets": self._assets,
            "cf_projects": self._projects,
            "cf_creator_dna": self._dna,
            "cf_idea_artifacts": self._artifacts,
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
        store[record_id] = stored
        return stored

    def update(self, table: str, row_id: str, values: dict[str, Any], id_column: str = "id") -> dict[str, Any]:
        store = self._store(table)
        if row_id not in store:
            raise RuntimeError(f"Update on {table} id={row_id} returned no data")
        store[row_id] = {**store[row_id], **values, "updated_at": datetime.now(timezone.utc).isoformat()}
        return store[row_id]


@pytest.fixture()
def studio_client(monkeypatch: pytest.MonkeyPatch) -> tuple[TestClient, _FakeStudioDB]:
    monkeypatch.setenv("HUB_API_KEY", "test-hub-key-for-ci")
    monkeypatch.setenv("CREATORFLOW_SUPABASE_URL", "https://cf-test.supabase.co")
    monkeypatch.setenv("CREATORFLOW_SUPABASE_SERVICE_ROLE_KEY", "test-cf-service-key")
    monkeypatch.setenv("STUDIO_GOOGLE_API_KEY", "test-google-key")
    from config.settings import get_settings

    get_settings.cache_clear()
    fake_db = _FakeStudioDB()
    fake_db.insert(
        "cf_projects",
        {"id": str(uuid.uuid4()), "user_id": USER_ID, "name": "P", "slug": "p", "is_default": True},
    )

    def _fake_cf_db() -> _FakeStudioDB:
        return fake_db

    for mod in (
        "services.studio.jobs",
        "services.studio.runner",
        "services.creatorflow_ideas",
        "services.creatorflow_dna",
        "services.creatorflow_brainstorm",
        "database.creatorflow_supabase_client",
    ):
        monkeypatch.setattr(f"{mod}.get_cf_supabase", _fake_cf_db)

    def _fake_execute(tool_id: str, prompt: str, params: dict, slug: str) -> tuple[bytes, str, str]:
        if tool_id in ("google_tts", "elevenlabs_tts"):
            return FAKE_WAV, "audio/wav", "studio-tts.wav"
        return FAKE_MP4, "video/mp4", "studio-veo.mp4"

    monkeypatch.setattr(
        "services.studio.jobs.sign_storage_path",
        lambda db, path, **kwargs: f"https://signed.test/{path}",
    )
    monkeypatch.setattr("services.studio.runner.execute_studio_tool", _fake_execute)
    monkeypatch.setattr(
        "services.studio.runner.upload_cf_asset_file",
        lambda db, user_id, content, filename, mime_type: f"{user_id}/fake-{filename}",
    )

    from api.app import app

    return TestClient(app), fake_db


def test_studio_catalog(studio_client: tuple[TestClient, _FakeStudioDB]) -> None:
    client, _ = studio_client
    res = client.get("/creatorflow/studio/catalog", headers=HUB_HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert len(data["tools"]) >= 2
    assert "veo3_video" in {t["id"] for t in data["tools"]}
    assert "google_tts" in {t["id"] for t in data["tools"]}
    assert data["providers"]["google"]["ready"] is True


def test_studio_job_create_and_list(studio_client: tuple[TestClient, _FakeStudioDB]) -> None:
    client, fake_db = studio_client
    headers = {**HUB_HEADERS, "X-User-Id": USER_ID}
    idea = fake_db.insert(
        "cf_ideas",
        {"user_id": USER_ID, "content": "Reel test", "title": "Test"},
    )
    create = client.post(
        f"/creatorflow/ideas/{idea['id']}/studio/jobs",
        headers=headers,
        json={"tool_id": "veo3_video"},
    )
    assert create.status_code == 201
    job_id = create.json()["id"]

    fetched = client.get(f"/creatorflow/studio/jobs/{job_id}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["status"] == "succeeded"
    assert fetched.json()["artifact_url"].startswith("https://signed.test/")
    assert fetched.json()["asset_id"]

    listed = client.get(f"/creatorflow/ideas/{idea['id']}/studio/jobs", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert listed.json()[0]["status"] == "succeeded"


def test_cf_health_studio_v3(studio_client: tuple[TestClient, _FakeStudioDB]) -> None:
    client, _ = studio_client
    res = client.get("/creatorflow/health", headers=HUB_HEADERS)
    assert res.status_code == 200
    assert res.json()["sprint"] == "studio-v3"


def test_studio_google_tts_job(studio_client: tuple[TestClient, _FakeStudioDB]) -> None:
    client, fake_db = studio_client
    headers = {**HUB_HEADERS, "X-User-Id": USER_ID}
    idea = fake_db.insert(
        "cf_ideas",
        {"user_id": USER_ID, "content": "Bonjour, ceci est un test voix off.", "title": "TTS"},
    )
    fake_db.insert(
        "cf_idea_artifacts",
        {
            "idea_id": idea["id"],
            "user_id": USER_ID,
            "artifact_type": "script",
            "content": {
                "hook": "Accroche forte.",
                "sections": [{"label": "Intro", "script": "Texte narré pour le test TTS."}],
            },
        },
    )
    create = client.post(
        f"/creatorflow/ideas/{idea['id']}/studio/jobs",
        headers=headers,
        json={"tool_id": "google_tts", "params": {"voice_name": "Kore"}},
    )
    assert create.status_code == 201
    assert create.json()["capability"] == "tts"
    assert "Texte narré" in create.json()["prompt"]

    fetched = client.get(f"/creatorflow/studio/jobs/{create.json()['id']}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["status"] == "succeeded"


def test_studio_runway_job(studio_client: tuple[TestClient, _FakeStudioDB], monkeypatch: pytest.MonkeyPatch) -> None:
    client, fake_db = studio_client
    headers = {**HUB_HEADERS, "X-User-Id": USER_ID}
    monkeypatch.setenv("STUDIO_RUNWAY_API_KEY", "test-runway-key")
    from config.settings import get_settings

    get_settings.cache_clear()

    monkeypatch.setattr(
        "services.studio.runner.execute_studio_tool",
        lambda tool_id, prompt, params, slug: (
            (FAKE_MP4, "video/mp4", "studio-runway.mp4")
            if tool_id == "runway_video"
            else (FAKE_MP4, "video/mp4", "studio-veo.mp4")
        ),
    )

    idea = fake_db.insert(
        "cf_ideas",
        {"user_id": USER_ID, "content": "Cinematic reel", "title": "Runway test"},
    )
    create = client.post(
        f"/creatorflow/ideas/{idea['id']}/studio/jobs",
        headers=headers,
        json={"tool_id": "runway_video", "params": {"aspect_ratio": "9:16", "duration": 5}},
    )
    assert create.status_code == 201
    assert create.json()["provider"] == "runway"

    fetched = client.get(f"/creatorflow/studio/jobs/{create.json()['id']}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["status"] == "succeeded"
