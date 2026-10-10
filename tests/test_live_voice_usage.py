"""Nadia Live Lot 4 — daily voice minutes (SPEC_JARVIS_LIVE §7)."""

from __future__ import annotations

import pytest

from services import live_session as ls
from services import live_voice_usage as usage
from tests.conftest import HUB_HEADERS
from tests.test_live_session import FakeClient, _settings


@pytest.fixture(autouse=True)
def isolated(tmp_path):
    usage.reset_for_tests(tmp_path / "usage.json")
    yield
    usage.reset_for_tests(None)


def test_reported_duration_cannot_exceed_the_wall_clock():
    sid = usage.open_session(now=100.0)
    assert usage.close_session(sid, 9_999, now=110.0)
    # elapsed 10 s + 5 s slack
    assert usage.used_seconds() == pytest.approx(15.0)


def test_unknown_or_double_close_is_rejected():
    sid = usage.open_session(now=1.0)
    assert usage.close_session(sid, 2, now=4.0)
    assert usage.close_session(sid, 2, now=5.0) is False
    assert usage.close_session("inconnu", 2, now=5.0) is False


def test_forgotten_session_is_charged_at_the_next_mint():
    usage.open_session(now=0.0)
    usage.open_session(now=10_000.0)
    assert usage.used_seconds() == pytest.approx(usage.UNREPORTED_CHARGE_SECONDS)


def test_cap_refuses_a_new_session(monkeypatch):
    monkeypatch.setattr(ls, "get_settings", lambda: _settings(live_voice_max_minutes_per_day=1))
    sid = usage.open_session(now=1.0)
    usage.close_session(sid, 60, now=80.0)
    with pytest.raises(ls.LiveSessionError) as exc:
        ls.mint_client_secret("nadia")
    assert exc.value.status_code == 429
    assert "clavier" in exc.value.detail


def test_end_session_records_duration_without_inventing_a_price(monkeypatch):
    recorded: list[dict] = []
    monkeypatch.setattr(ls, "get_settings", lambda: _settings())
    monkeypatch.setattr(
        "services.cost_monitor.record_call",
        lambda *a, **kw: recorded.append({"args": a, "kw": kw}) or 0.0,
    )
    sid = usage.open_session(now=1.0)
    assert ls.end_session(sid, 12.0)
    assert recorded[0]["kw"]["native_cost_usd"] == 0.0
    assert "seconds=12" in recorded[0]["kw"]["note"]


def test_usage_api(hub_client, monkeypatch):
    FakeClient.calls = []
    FakeClient.outcome = {"value": "ek_ephemeral", "expires_at": 1}
    monkeypatch.setattr(ls, "get_settings", lambda: _settings())
    monkeypatch.setattr(ls.httpx, "Client", FakeClient)

    minted = hub_client.post("/live/session", json={"persona": "nadia"}, headers=HUB_HEADERS)
    assert minted.status_code == 200
    session_id = minted.json()["session_id"]

    ended = hub_client.post(
        "/live/session/end",
        json={"session_id": session_id, "seconds": 3},
        headers=HUB_HEADERS,
    )
    assert ended.status_code == 200
    assert ended.json()["used_seconds"] >= 0

    again = hub_client.post(
        "/live/session/end",
        json={"session_id": session_id, "seconds": 3},
        headers=HUB_HEADERS,
    )
    assert again.status_code == 404
    assert hub_client.get("/live/usage", headers=HUB_HEADERS).status_code == 200
    assert hub_client.get("/live/usage").status_code in (401, 403)
