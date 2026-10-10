"""Nadia Live — internet / Gmail / socials snapshot (no secrets)."""

from __future__ import annotations

import httpx
import pytest

from services import live_access as la
from tests.conftest import HUB_HEADERS


class _OkResponse:
    status_code = 200


class _OkClient:
    def __init__(self, *a, **kw) -> None:
        pass

    def __enter__(self):
        return self

    def __exit__(self, *a) -> None:
        return None

    def get(self, url: str):
        assert url == la.INTERNET_URL
        return _OkResponse()


def test_probe_internet_ok(monkeypatch):
    monkeypatch.setattr(la.httpx, "Client", _OkClient)
    assert la.probe_internet() == {"ok": True, "detail": "HTTP 200"}


def test_probe_internet_down(monkeypatch):
    class FailClient(_OkClient):
        def get(self, url: str):
            raise httpx.ConnectError(
                "nope",
                request=httpx.Request("GET", la.INTERNET_URL),
            )

    monkeypatch.setattr(la.httpx, "Client", FailClient)
    snap = la.probe_internet()
    assert snap["ok"] is False
    assert snap["detail"] == "ConnectError"


def test_probe_access_ready(monkeypatch):
    monkeypatch.setattr(la, "probe_internet", lambda: {"ok": True, "detail": "HTTP 200"})
    monkeypatch.setattr(
        la,
        "_composio_app",
        lambda name: {"ok": name == "gmail", "via": "composio"},
    )
    monkeypatch.delenv("DISCORD_BOT_TOKEN", raising=False)
    snap = la.probe_access()
    assert snap["ready"]["research"] is True
    assert snap["ready"]["mail"] is True
    assert snap["ready"]["discord"] is False


def test_discord_bot_is_not_private_inbox(monkeypatch):
    monkeypatch.setattr(la, "probe_internet", lambda: {"ok": False, "detail": "down"})
    monkeypatch.setattr(la, "_composio_app", lambda name: {"ok": False, "via": "composio"})
    monkeypatch.setenv("DISCORD_BOT_TOKEN", "not-a-real-token")
    snap = la.probe_access()
    assert snap["apps"]["discord"]["via"] == "bot"
    assert snap["ready"]["discord"] is True
    assert "privés" in snap["apps"]["discord"]["detail"]


def test_access_api_and_connect_allowlist(hub_client, monkeypatch):
    monkeypatch.setattr(
        la,
        "probe_access",
        lambda: {
            "internet": {"ok": True, "detail": "HTTP 200"},
            "apps": {},
            "ready": {
                "research": True,
                "mail": False,
                "calendar": False,
                "discord": False,
                "instagram": False,
            },
        },
    )
    monkeypatch.setattr(
        "services.secretary_composio.get_oauth_link_for_ceo",
        lambda app: "https://oauth.example/x",
    )
    assert hub_client.get("/live/access").status_code in (401, 403)
    res = hub_client.get("/live/access", headers=HUB_HEADERS)
    assert res.status_code == 200
    assert res.json()["ready"]["research"] is True

    denied = hub_client.post("/live/connect/github", headers=HUB_HEADERS)
    assert denied.status_code == 400
    ok = hub_client.post("/live/connect/discord", headers=HUB_HEADERS)
    assert ok.status_code == 200
    assert ok.json()["oauth_url"].startswith("https://")


@pytest.mark.parametrize(
    ("text", "slug"),
    [
        ("connecte instagram", "instagram"),
        ("connecte discord", "discord"),
        ("connecte mon calendrier", "googlecalendar"),
        ("connecte gmail", "gmail"),
        ("connecte linkedin", "linkedin"),
    ],
)
def test_connect_target(text, slug):
    from agents.secretary_handlers_comms import _connect_target

    found = _connect_target(text)
    assert found is not None
    assert found[0] == slug


def test_split_oauth_reply_unwraps_gmail_hint():
    from services.secretary_composio_oauth import split_oauth_reply

    url, hint = split_oauth_reply(
        "Connecte-toi avec **alnua.global@gmail.com**\nhttps://connect.composio.dev/link/abc"
    )
    assert url == "https://connect.composio.dev/link/abc"
    assert "alnua.global@gmail.com" in hint


def test_instagram_falls_back_to_business_toolkit(monkeypatch):
    calls: list[str] = []

    def fake_link(app: str, user_id: str = "") -> str:
        calls.append(app.lower())
        if app.lower() == "instagram":
            return "Erreur: toolkit instagram missing auth config"
        return "https://connect.composio.dev/ig-biz"

    monkeypatch.setattr(
        "services.secretary_composio_oauth.composio_user_id",
        lambda: "alnua_coo",
    )
    monkeypatch.setattr("skills.skill_composio.get_oauth_link", fake_link)
    from services.secretary_composio_oauth import get_oauth_link_for_ceo

    raw = get_oauth_link_for_ceo("instagram")
    assert calls == ["instagram", "instagram_business"]
    assert "https://connect.composio.dev/ig-biz" in raw
    assert "Professionnel" in raw


def test_instagram_already_connected_on_business(monkeypatch):
    def fake_active(user_id: str, toolkit: str) -> bool:
        return toolkit == "instagram_business"

    monkeypatch.setattr(
        "services.secretary_composio_oauth.composio_user_id",
        lambda: "alnua_coo",
    )
    monkeypatch.setattr("skills.skill_composio.has_active_connection", fake_active)
    from services.secretary_composio_oauth import is_connected

    assert is_connected("instagram") is True


def test_live_connect_strips_gmail_wrapper(hub_client, monkeypatch):
    monkeypatch.setattr(
        "services.secretary_composio.get_oauth_link_for_ceo",
        lambda app: "Connecte-toi avec **alnua.global@gmail.com**\nhttps://oauth.example/gmail",
    )
    res = hub_client.post("/live/connect/gmail", headers=HUB_HEADERS)
    assert res.status_code == 200
    assert res.json()["oauth_url"] == "https://oauth.example/gmail"
