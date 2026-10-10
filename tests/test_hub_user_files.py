# ruff: noqa: F811
"""Hub user file library — upload, list, delete, Live task attachment."""

from __future__ import annotations

from services import live_tasks as lt
from services.hub_user_files import HubUserFileStore, build_attachment_context
from tests.conftest import HUB_HEADERS
from tests.live_tasks_fixtures import registry  # noqa: F401


def _isolated_store(tmp_path, monkeypatch) -> HubUserFileStore:
    store = HubUserFileStore(
        index_path=tmp_path / "hub_files.json",
        uploads_dir=tmp_path / "hub_uploads",
    )
    monkeypatch.setattr("services.hub_user_files._store", store)
    return store


def test_save_list_delete_bytes(tmp_path, monkeypatch):
    store = _isolated_store(tmp_path, monkeypatch)
    record = store.save_bytes(b"hello hub", "notes.txt", "text/plain", source="live")
    assert record.id
    assert store.list_files()[0].name == "notes.txt"
    assert store.read_bytes(record.id) == b"hello hub"
    assert store.delete(record.id)
    assert store.get(record.id) is None


def test_rejects_binary_extension(tmp_path, monkeypatch):
    store = _isolated_store(tmp_path, monkeypatch)
    try:
        store.save_bytes(b"\x00\x01", "evil.exe", "application/octet-stream")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_api_upload_list_delete(hub_client, tmp_path, monkeypatch):
    _isolated_store(tmp_path, monkeypatch)
    res = hub_client.post(
        "/hub/files",
        headers=HUB_HEADERS,
        files={"file": ("brief.md", b"# Spec\n", "text/markdown")},
        data={"source": "live"},
    )
    assert res.status_code == 201
    file_id = res.json()["id"]

    listed = hub_client.get("/hub/files", headers=HUB_HEADERS).json()["files"]
    assert listed[0]["id"] == file_id

    content = hub_client.get(f"/hub/files/{file_id}/content", headers=HUB_HEADERS)
    assert content.status_code == 200
    assert b"Spec" in content.content

    assert hub_client.delete(f"/hub/files/{file_id}", headers=HUB_HEADERS).status_code == 204


def test_live_task_with_file_expands_prompt(hub_client, tmp_path, monkeypatch, registry):
    store = _isolated_store(tmp_path, monkeypatch)
    uploaded = store.save_bytes(b"contenu secret", "doc.txt", "text/plain", source="live")

    monkeypatch.setattr(lt, "_run_chat_agent", lambda *_a, **_k: lt.Outcome(text="ok"))
    captured: list[str] = []

    def spy_execute(agent_id: str, instruction: str, session_id: str) -> lt.Outcome:
        captured.append(instruction)
        return lt.Outcome(text="done")

    monkeypatch.setattr(lt, "_execute", spy_execute)

    res = hub_client.post(
        "/live/tasks",
        json={
            "agent_id": "secretary",
            "instruction": "Résume",
            "file_ids": [uploaded.id],
        },
        headers=HUB_HEADERS,
    )
    assert res.status_code == 201
    task_id = res.json()["id"]
    lt.run_task(task_id)
    assert "contenu secret" in captured[0]
    assert "Pièce jointe" in captured[0]


def test_hub_files_requires_hub_key(hub_client, tmp_path, monkeypatch):
    _isolated_store(tmp_path, monkeypatch)
    assert hub_client.get("/hub/files").status_code in (401, 403)


def test_build_attachment_context_unknown_id(tmp_path, monkeypatch):
    _isolated_store(tmp_path, monkeypatch)
    try:
        build_attachment_context(["missing"])
        assert False
    except ValueError:
        pass
