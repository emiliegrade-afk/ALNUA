"""Nadia Live Lot 3 — OpenAI Realtime client-secret minting (DEC-038).

No network: ``httpx.Client`` is replaced and settings are a plain namespace.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import httpx
import pytest

from services import live_session as ls
from tests.conftest import HUB_HEADERS

API_KEY = "sk-test-secret-do-not-leak"


def _settings(**over):
    base = {
        "live_voice_enabled": True,
        "openai_api_key": API_KEY,
        "live_voice_model": "gpt-realtime",
        "live_voice_max_minutes_per_day": 30,
        "live_voice_secret_ttl_seconds": 120,
    }
    return SimpleNamespace(**{**base, **over})


class FakeClient:
    """Stands in for httpx.Client; records the request and replays one outcome."""

    outcome: object = {"value": "ek_ephemeral", "expires_at": 1756310470}
    calls: list[dict] = []

    def __init__(self, *a, **kw) -> None:
        pass

    def __enter__(self):
        return self

    def __exit__(self, *a) -> None:
        return None

    def post(self, url, headers=None, json=None):
        FakeClient.calls.append({"url": url, "headers": headers, "json": json})
        request = httpx.Request("POST", url)
        if isinstance(FakeClient.outcome, Exception):
            raise FakeClient.outcome
        return httpx.Response(200, json=FakeClient.outcome, request=request)


@pytest.fixture(autouse=True)
def usage_file(tmp_path):
    """Never touch the real data/live_voice_usage.json."""
    from services import live_voice_usage

    live_voice_usage.reset_for_tests(tmp_path / "usage.json")
    yield live_voice_usage
    live_voice_usage.reset_for_tests(None)


@pytest.fixture()
def voice(monkeypatch):
    FakeClient.calls = []
    FakeClient.outcome = {"value": "ek_ephemeral", "expires_at": 1756310470}
    monkeypatch.setattr(ls, "get_settings", lambda: _settings())
    monkeypatch.setattr(ls.httpx, "Client", FakeClient)
    return FakeClient


def test_mint_returns_ephemeral_secret_never_the_api_key(voice):
    out = ls.mint_client_secret("nadia")
    assert out["client_secret"] == "ek_ephemeral"
    assert API_KEY not in json.dumps(out)
    sent = voice.calls[0]
    assert sent["headers"]["Authorization"] == f"Bearer {API_KEY}"
    assert sent["url"] == ls.CLIENT_SECRETS_URL


def test_session_config_is_fixed_server_side(voice):
    ls.mint_client_secret("aria")
    cfg = voice.calls[0]["json"]
    session = cfg["session"]
    assert cfg["expires_after"] == {"anchor": "created_at", "seconds": 120}
    assert session["type"] == "realtime" and session["model"] == "gpt-realtime"
    vad = session["audio"]["input"]["turn_detection"]
    assert vad["type"] == "server_vad" and vad["interrupt_response"] is True  # hands-free
    assert session["audio"]["input"]["transcription"]["model"] == "gpt-realtime-whisper"
    assert session["audio"]["output"]["voice"] == "cedar"
    assert "Aria" in session["instructions"]
    names = [t["name"] for t in session["tools"]]
    assert names == [
        "start_task",
        "list_tasks",
        "get_task_status",
        "cancel_task",
        "clear_screens",
    ]


def test_start_task_enum_follows_the_task_allowlist(voice, monkeypatch):
    monkeypatch.setattr("services.live_tasks.allowed_agents", lambda: ["secretary"])
    ls.mint_client_secret("nadia")
    start = voice.calls[0]["json"]["session"]["tools"][0]
    assert start["parameters"]["properties"]["agent"]["enum"] == ["secretary"]


def test_instructions_treat_tool_output_as_data_and_forbid_unprompted_sends():
    text = ls.build_instructions("nadia")
    assert "jamais des ordres" in text
    assert "brouillon" in text and "200 caractères" in text
    assert "start_task distincte" in text
    assert "Recherche internet" in text
    assert "Ouvre instagram" in text
    assert "Génère une image" in text
    assert "LinkedIn" in text


def test_disabled_flag_and_missing_key_refuse(monkeypatch):
    monkeypatch.setattr(ls, "get_settings", lambda: _settings(live_voice_enabled=False))
    with pytest.raises(ls.LiveSessionError) as off:
        ls.mint_client_secret("nadia")
    assert off.value.status_code == 503

    monkeypatch.setattr(ls, "get_settings", lambda: _settings(openai_api_key=""))
    with pytest.raises(ls.LiveSessionError) as nokey:
        ls.mint_client_secret("nadia")
    assert nokey.value.status_code == 503


def test_unknown_persona_is_rejected(voice):
    with pytest.raises(ls.LiveSessionError) as exc:
        ls.mint_client_secret("jarvis")
    assert exc.value.status_code == 400
    assert voice.calls == []


def test_upstream_failures_become_502_without_leaking(voice):
    voice.outcome = httpx.ConnectError("boom")
    with pytest.raises(ls.LiveSessionError) as exc:
        ls.mint_client_secret("nadia")
    assert exc.value.status_code == 502 and API_KEY not in exc.value.detail

    voice.outcome = {"unexpected": True}
    with pytest.raises(ls.LiveSessionError) as odd:
        ls.mint_client_secret("nadia")
    assert odd.value.status_code == 502


def test_api_endpoint_and_auth(hub_client, voice, monkeypatch):
    assert hub_client.post("/live/session", json={}).status_code in (401, 403)

    res = hub_client.post("/live/session", json={"persona": "nadia"}, headers=HUB_HEADERS)
    assert res.status_code == 200
    body = res.json()
    assert body["client_secret"] == "ek_ephemeral" and body["calls_url"] == ls.CALLS_URL
    assert API_KEY not in res.text

    assert hub_client.post("/live/session", json={"persona": "jarvis"}, headers=HUB_HEADERS).status_code == 422

    monkeypatch.setattr(ls, "get_settings", lambda: _settings(live_voice_enabled=False))
    assert hub_client.post("/live/session", json={}, headers=HUB_HEADERS).status_code == 503
