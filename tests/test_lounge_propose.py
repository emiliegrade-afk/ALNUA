"""Tests Lounge propose + CN model default (Phase 46 V5)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from services import lounge_propose as lp
from services import lounge_runtime as rt
from services.lounge_llm import LOUNGE_DEFAULT_MODEL, get_lounge_model


def test_lounge_default_model_is_deepseek_cn(monkeypatch: pytest.MonkeyPatch) -> None:
    from config.settings import settings

    monkeypatch.setattr(settings, "lounge_model", "")
    assert get_lounge_model() == LOUNGE_DEFAULT_MODEL
    assert "deepseek" in LOUNGE_DEFAULT_MODEL


def test_propose_creates_ticket(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rt, "_SESSIONS_PATH", tmp_path / "lounge_sessions.json")
    monkeypatch.setattr(lp, "_PROPOSALS_PATH", tmp_path / "lounge_proposals.json")

    session = rt.start_puzzle_session("dev_app", "binary-sum")
    done = rt.complete_puzzle_session(session["id"], "16")
    assert done["status"] == "completed"

    fake_db = MagicMock()
    fake_db.select.return_value = [{"id": "proj-1", "name": "Hub"}]
    fake_db.insert.return_value = {"id": "tick-1", "title": "[lounge] test"}

    with patch("database.supabase_client.get_supabase", return_value=fake_db):
        result = lp.propose_to_department(
            session_id=session["id"],
            dept="rd",
            summary="Idée issue du puzzle binaire utile pour l'app.",
            agent_id="dev_app",
        )

    assert result["ok"] is True
    assert result["proposal"]["status"] == "ticket_created"
    assert result["proposal"]["ticket_id"] == "tick-1"
    fake_db.insert.assert_called_once()
    inserted = fake_db.insert.call_args[0][1]
    assert inserted["source"] == "lounge"
    assert inserted["type"] == "improvement"
    assert lp.contributions_transferred_count() == 1


def test_propose_unknown_dept_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rt, "_SESSIONS_PATH", tmp_path / "lounge_sessions.json")
    monkeypatch.setattr(lp, "_PROPOSALS_PATH", tmp_path / "lounge_proposals.json")
    session = rt.start_puzzle_session("qa", "aluna-acronym")
    with pytest.raises(ValueError, match="unknown dept"):
        lp.propose_to_department(
            session_id=session["id"],
            dept="spaceship",
            summary="Trop court? Non — insight assez long pour passer.",
        )
