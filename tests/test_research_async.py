"""Research routing — Telegram async, R&D investigation detection."""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch



def test_extract_rnd_research_robotique() -> None:
    from services.coo_telegram_intents import extract_investigation_query

    topic = extract_investigation_query("lance une recherche R&D robotique")
    assert topic == "robotique"


def test_secretary_routes_rnd_to_investigation() -> None:
    from agents.secretary_agent import SecretaryAgent

    agent = SecretaryAgent(db=MagicMock())
    with patch("services.coo_telegram_intents.launch_rnd_investigation") as launch:
        launch.return_value = "🌳 **Arbre R&D lancé**"
        out = agent._handle_research(
            "lance une recherche R&D robotique",
            session_id="tg:12345",
        )
    launch.assert_called_once_with("robotique", chat_id=12345)
    assert "Arbre R&D" in out


def test_run_bureau_research_async_notifies(monkeypatch) -> None:
    from services import bureau_library as bl

    notified: list[tuple[int, str, dict]] = []

    def fake_notify(chat_id: int, query: str, result: dict) -> None:
        notified.append((chat_id, query, result))

    monkeypatch.setattr(bl, "_notify_research_complete", fake_notify)

    with patch("skills.skill_web_research._search", return_value=[]):
        with patch("services.trend_monitor.aggregate_trends", return_value=[]):
            with patch(
                "services.bureau_library._extract_entries_from_research",
                return_value=[],
            ):
                with patch(
                    "agents.rnd_center.develop_library_entries_as_rnd",
                    return_value=[],
                ):
                    result = bl.run_bureau_research(
                        "robotique",
                        blocking=False,
                        notify_chat_id=99,
                    )

    assert result["status"] == "started"
    deadline = time.time() + 10.0
    while time.time() < deadline and not notified:
        time.sleep(0.05)
    assert notified
    assert notified[0][0] == 99
    assert notified[0][1] == "robotique"
