"""Nadia Live — vocal clear, HTML sandbox, Sofia LinkedIn, session context."""

from __future__ import annotations

from types import SimpleNamespace

from services import live_html_app as html
from services import live_session as session
from services import live_session_context as ctx
from services import live_social_drafts as social
from services.live_tasks_store import STATUS_DONE, LiveTask


def test_clear_screens_tool_declared():
    names = [t["name"] for t in session.build_tools(["secretary", "coo", "plan"])]
    assert "clear_screens" in names
    assert "Tout effacer" in session._RULES or "clear_screens" in session._RULES


def test_html_app_writes_and_opens(tmp_path, monkeypatch):
    opened: list[str] = []
    monkeypatch.setattr(html, "OUT_DIR", tmp_path)
    monkeypatch.setattr(html, "get_settings", lambda: SimpleNamespace(live_pc_actions_enabled=True))
    monkeypatch.setattr(html, "_reveal", lambda p: opened.append(p.name))
    assert html.wants_html_app("crée une appli HTML chrono") is True
    assert html.maybe_html("bonjour") is None
    out = html.run_html_app("crée une appli HTML chrono")
    assert "Chrono" in out or "timer" in out.lower()
    assert opened and opened[0].startswith("timer-")
    written = tmp_path / opened[0]
    assert written.is_file()
    body = written.read_text(encoding="utf-8")
    assert "<script" in body
    assert "fetch(" not in body


def test_html_disabled(monkeypatch):
    monkeypatch.setattr(html, "get_settings", lambda: SimpleNamespace(live_pc_actions_enabled=False))
    out = html.run_html_app("crée une appli HTML notes")
    assert "LIVE_PC_ACTIONS_ENABLED" in out


def test_sofia_draft_then_card(monkeypatch):
    class Fake:
        def _complete(self, *a, **k):
            return "Chez ALNUA on construit des agents utiles. #ALNUA"

    monkeypatch.setattr("agents.content_agent.ContentAgent", Fake)
    social.reset_for_tests()
    raw = social.draft_linkedin_sofia("agents IA")
    assert "ALNUA" in raw
    card = social.format_linkedin_draft(raw)
    assert "```draft" in card


def test_session_context_from_done_tasks(monkeypatch):
    class Store:
        def list_tasks(self, status=None, limit=20):
            return [
                LiveTask(
                    id="a",
                    agent_id="secretary",
                    instruction="Recherche internet : IA",
                    status=STATUS_DONE,
                    session_id="live-voice",
                    result="Sources : https://example.com/ia",
                    finished_at="2026-10-10T20:00:00+00:00",
                    updated_at="2026-10-10T20:00:00+00:00",
                )
            ]

    monkeypatch.setattr(ctx, "get_store", lambda: Store(), raising=False)
    monkeypatch.setattr("services.live_tasks.get_store", lambda: Store())
    out = ctx.with_session_context("quelle est la source ?", "live-voice")
    assert "example.com" in out
    assert "quelle est la source" in out
