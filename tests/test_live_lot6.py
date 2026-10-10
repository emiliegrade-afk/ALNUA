"""Nadia Live Lot 6 — cards, drafts, slots, media (no network)."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from tests.conftest import HUB_HEADERS

_PARIS = ZoneInfo("Europe/Paris")


def test_list_and_draft_fences():
    from services.live_cards_format import draft_card, list_card

    listed = list_card("Programme", ["10:00 — COO", "14:00 — R&D"])
    assert "```list" in listed and "Programme" in listed
    draft = draft_card(kind="linkedin", title="Post", body="Hello ALNUA", draft_id="abc123")
    assert "```draft" in draft and "abc123" in draft


def test_linkedin_draft_roundtrip(monkeypatch):
    from services import live_social_drafts as social

    social.reset_for_tests()
    out = social.format_linkedin_draft("Un post ALNUA")
    draft_id = social.latest_draft_id()
    assert draft_id and draft_id in out

    monkeypatch.setattr(
        "services.secretary_composio_oauth.is_connected",
        lambda name: name == "linkedin",
    )
    monkeypatch.setattr(
        "skills.skill_composio.composio_execute",
        lambda *a, **k: {"success": True},
    )
    result = social.publish_linkedin_draft(draft_id)
    assert result["success"] is True
    assert social.get_draft(draft_id) is None


def test_linkedin_publish_without_connection(monkeypatch):
    from services import live_social_drafts as social

    social.reset_for_tests()
    social.format_linkedin_draft("x")
    monkeypatch.setattr("services.secretary_composio_oauth.is_connected", lambda name: False)
    result = social.publish_linkedin_draft(social.latest_draft_id() or "")
    assert result["success"] is False
    assert "connecté" in result["message"]


def test_media_name_is_fenced(tmp_path, monkeypatch):
    from services import live_media as media

    monkeypatch.setattr(media, "artifacts_dir", lambda: tmp_path)
    assert media.resolve_media("../secret.png") is None
    assert media.resolve_media("not-hex.png") is None
    name = "a" * 32 + ".png"
    path = tmp_path / name
    path.write_bytes(b"png")
    assert media.resolve_media(name) == path.resolve()


def test_wants_image_vs_stock():
    from services.live_media import wants_generated_image, wants_stock_image

    assert wants_generated_image("Génère une image de robot")
    assert wants_stock_image("Trouve une image libre de drone")
    assert not wants_generated_image("Trouve une image libre de drone")


def test_free_slots_skips_busy(monkeypatch):
    from services import live_free_slots as slots

    now = datetime.now(_PARIS).replace(hour=8, minute=0, second=0, microsecond=0)
    busy_when = now.replace(hour=10, minute=0).isoformat()
    monkeypatch.setattr("services.secretary_composio.is_connected", lambda name: True)
    monkeypatch.setattr(
        "services.secretary_composio.fetch_calendar_events",
        lambda days_ahead=2: [{"when": busy_when, "title": "Standup"}],
    )
    out = slots.free_slots_brief(days=1, duration_minutes=30)
    assert "```list" in out
    assert "Créneaux" in out or "créneau" in out.lower() or "Aucun" in out


def test_confirm_api_linkedin(hub_client, monkeypatch):
    from services import live_social_drafts as social

    social.reset_for_tests()
    social.format_linkedin_draft("Hello")
    draft_id = social.latest_draft_id()
    monkeypatch.setattr(
        "services.live_social_drafts.publish_linkedin_draft",
        lambda did: {"success": True, "message": "Publié sur LinkedIn."},
    )
    denied = hub_client.post(
        "/live/confirm",
        json={"kind": "linkedin", "draft_id": draft_id},
    )
    assert denied.status_code in (401, 403)
    res = hub_client.post(
        "/live/confirm",
        json={"kind": "linkedin", "draft_id": draft_id},
        headers=HUB_HEADERS,
    )
    assert res.status_code == 200
    assert "LinkedIn" in res.json()["message"]


def test_connect_linkedin():
    from agents.secretary_handlers_comms import _connect_target

    found = _connect_target("connecte linkedin")
    assert found is not None and found[0] == "linkedin"


def test_media_api_404(hub_client):
    res = hub_client.get("/live/media/not-a-file.png", headers=HUB_HEADERS)
    assert res.status_code == 404
