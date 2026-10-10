# ruff: noqa: F811
"""Assistant chat with Hub file attachments."""

from __future__ import annotations

from services.hub_user_files import HubUserFileStore
from tests.conftest import HUB_HEADERS


def _isolated_store(tmp_path, monkeypatch) -> HubUserFileStore:
    store = HubUserFileStore(
        index_path=tmp_path / "hub_files.json",
        uploads_dir=tmp_path / "hub_uploads",
    )
    monkeypatch.setattr("services.hub_user_files._store", store)
    return store


def test_assistant_chat_with_file_ids(hub_client, tmp_path, monkeypatch):
    store = _isolated_store(tmp_path, monkeypatch)
    record = store.save_bytes(b"contrat ACME", "contrat.txt", "text/plain", source="secretary")
    captured: list[str] = []

    async def fake_chat(message: str, **kwargs):
        captured.append(message)
        return {
            "agent_id": "secretary",
            "agent_name": "Nadia Faure",
            "response": "OK",
            "issue_created": False,
        }

    monkeypatch.setattr("services.assistant_router.assistant_chat_async", fake_chat)

    res = hub_client.post(
        "/assistant/chat",
        json={"message": "Résume", "agent": "secretary", "file_ids": [record.id]},
        headers=HUB_HEADERS,
    )
    assert res.status_code == 200
    assert "contrat ACME" in captured[0]
    assert "Pièce jointe" in captured[0]


def test_assistant_chat_rejects_empty_without_files(hub_client):
    res = hub_client.post(
        "/assistant/chat",
        json={"message": "   ", "agent": "auto"},
        headers=HUB_HEADERS,
    )
    assert res.status_code == 400
