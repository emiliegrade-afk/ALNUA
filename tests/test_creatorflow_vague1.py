"""CreatorFlow V1 Think — ideas, DNA, brainstorm, BYOK."""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Any
from unittest.mock import patch

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


class _FakeV1DB:
    def __init__(self) -> None:
        self._ideas: dict[str, dict[str, Any]] = {}
        self._dna: dict[str, dict[str, Any]] = {}
        self._messages: dict[str, dict[str, Any]] = {}
        self._artifacts: dict[str, dict[str, Any]] = {}
        self._ai: dict[str, dict[str, Any]] = {}
        self._projects: dict[str, dict[str, Any]] = {}
        self._studio_jobs: dict[str, dict[str, Any]] = {}
        self._agent_logs: dict[str, dict[str, Any]] = {}

    def _store(self, table: str) -> dict[str, dict[str, Any]]:
        return {
            "cf_ideas": self._ideas,
            "cf_creator_dna": self._dna,
            "cf_idea_messages": self._messages,
            "cf_idea_artifacts": self._artifacts,
            "cf_user_ai_settings": self._ai,
            "cf_projects": self._projects,
            "cf_studio_jobs": self._studio_jobs,
            "agent_logs": self._agent_logs,
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
        if is_null:
            for col in is_null:
                rows = [r for r in rows if r.get(col) is None]
        if order_by:
            rows.sort(key=lambda r: r.get(order_by, ""), reverse=not ascending)
        if limit is not None:
            rows = rows[:limit]
        return rows

    def insert(self, table: str, row: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        store = self._store(table)
        if table == "cf_user_ai_settings":
            record_id = row["user_id"]
            stored = {**row, "created_at": now, "updated_at": now}
            store[record_id] = stored
            return stored
        record_id = row.get("id") or str(uuid.uuid4())
        stored = {
            "id": record_id,
            "created_at": now,
            "updated_at": now,
            **row,
        }
        if table == "cf_ideas":
            stored.setdefault("tags", [])
            stored.setdefault("status", "spark")
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
        if table == "cf_user_ai_settings" and row_id in store:
            store[row_id] = {**store[row_id], **values, "updated_at": datetime.now(timezone.utc).isoformat()}
            return store[row_id]
        if row_id not in store:
            for rid, row in store.items():
                if row.get(id_column) == row_id:
                    row_id = rid
                    break
        if row_id not in store:
            raise RuntimeError(f"Update on {table} id={row_id} returned no data")
        store[row_id] = {**store[row_id], **values, "updated_at": datetime.now(timezone.utc).isoformat()}
        return store[row_id]

    def delete(self, table: str, row_id: str, id_column: str = "id") -> None:
        store = self._store(table)
        if row_id in store:
            del store[row_id]
            return
        for rid, row in list(store.items()):
            if row.get(id_column) == row_id:
                del store[rid]
                return


@pytest.fixture()
def v1_client(monkeypatch: pytest.MonkeyPatch) -> tuple[TestClient, _FakeV1DB]:
    monkeypatch.setenv("HUB_API_KEY", "test-hub-key-for-ci")
    monkeypatch.setenv("CREATORFLOW_SUPABASE_URL", "https://cf-test.supabase.co")
    monkeypatch.setenv("CREATORFLOW_SUPABASE_SERVICE_ROLE_KEY", "test-cf-service-key")
    from config.settings import get_settings

    get_settings.cache_clear()
    fake_db = _FakeV1DB()
    fake_db.insert(
        "cf_projects",
        {
            "id": str(uuid.uuid4()),
            "user_id": USER_ID,
            "name": "Mon projet",
            "slug": "mon-projet",
            "is_default": True,
        },
    )

    for mod in (
        "services.creatorflow_projects",
        "services.creatorflow_ideas",
        "services.creatorflow_dna",
        "services.creatorflow_user_ai",
        "services.creatorflow_brainstorm",
        "services.creatorflow_llm",
        "services.creatorflow_stats",
        "services.creatorflow_platforms",
        "services.creatorflow_export_runner",
    ):
        monkeypatch.setattr(f"{mod}.get_cf_supabase", lambda: fake_db)

    from api.app import app

    return TestClient(app), fake_db


def test_cf_health_v1(v1_client: tuple[TestClient, _FakeV1DB]) -> None:
    client, _ = v1_client
    res = client.get("/creatorflow/health", headers=HUB_HEADERS)
    assert res.status_code == 200
    assert res.json()["sprint"] == "studio-v3"


def test_cf_ideas_crud(v1_client: tuple[TestClient, _FakeV1DB]) -> None:
    client, _ = v1_client
    headers = {**HUB_HEADERS, "X-User-Id": USER_ID}

    create = client.post(
        "/creatorflow/ideas",
        headers=headers,
        json={"content": "Reel sur les 3 erreurs de montage"},
    )
    assert create.status_code == 201
    idea_id = create.json()["id"]
    assert create.json()["status"] == "spark"

    listing = client.get("/creatorflow/ideas", headers=headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1

    patch_res = client.patch(
        f"/creatorflow/ideas/{idea_id}",
        headers=headers,
        json={"status": "developing"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "developing"


def test_cf_dna_upsert(v1_client: tuple[TestClient, _FakeV1DB]) -> None:
    client, _ = v1_client
    headers = {**HUB_HEADERS, "X-User-Id": USER_ID}

    res = client.put(
        "/creatorflow/dna",
        headers=headers,
        json={
            "scope": "global",
            "voice_tone": "Direct et bienveillant",
            "audience": "Créateurs solo",
            "taboos": ["clickbait"],
        },
    )
    assert res.status_code == 200
    assert res.json()["voice_tone"] == "Direct et bienveillant"

    listing = client.get("/creatorflow/dna", headers=headers)
    assert listing.status_code == 200
    assert len(listing.json()) >= 1


def test_cf_ai_settings_byok(v1_client: tuple[TestClient, _FakeV1DB]) -> None:
    client, _ = v1_client
    headers = {**HUB_HEADERS, "X-User-Id": USER_ID}

    res = client.put(
        "/creatorflow/ai-settings",
        headers=headers,
        json={"api_key": "sk-or-test-key-12345678", "use_own_key": True},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["has_key"] is True
    assert body["use_own_key"] is True
    assert body["api_key_masked"]


@patch("services.creatorflow_brainstorm.cf_llm_chat", return_value="Voici 3 angles forts pour ta vidéo.")
def test_cf_brainstorm(mock_llm: Any, v1_client: tuple[TestClient, _FakeV1DB]) -> None:
    client, _ = v1_client
    headers = {**HUB_HEADERS, "X-User-Id": USER_ID}

    idea = client.post(
        "/creatorflow/ideas",
        headers=headers,
        json={"content": "Tutoriel CapCut avancé"},
    ).json()

    res = client.post(
        f"/creatorflow/ideas/{idea['id']}/brainstorm",
        headers=headers,
        json={"message": "Donne-moi 3 hooks"},
    )
    assert res.status_code == 200
    assert res.json()["message"]["role"] == "assistant"
    mock_llm.assert_called_once()

    msgs = client.get(f"/creatorflow/ideas/{idea['id']}/messages", headers=headers)
    assert len(msgs.json()) >= 2


@patch("services.creatorflow_brainstorm.cf_llm_chat")
def test_cf_generate_script(mock_llm: Any, v1_client: tuple[TestClient, _FakeV1DB]) -> None:
    client, _ = v1_client
    headers = {**HUB_HEADERS, "X-User-Id": USER_ID}
    mock_llm.return_value = '{"title":"Test","hook":"H","sections":[],"cta":"C","estimated_duration_sec":60}'

    idea = client.post(
        "/creatorflow/ideas",
        headers=headers,
        json={"content": "Idée script"},
    ).json()

    res = client.post(f"/creatorflow/ideas/{idea['id']}/generate-script", headers=headers)
    assert res.status_code == 200
    assert res.json()["artifact"]["artifact_type"] == "script"
