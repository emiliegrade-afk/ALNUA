"""Nadia weather tool — wttr.in mocked, no network."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from services.secretary_weather import (
    extract_weather_place,
    format_weather_facts,
    weather_reply,
)
from services.secretary_intents import detect_weather_intent, keyword_fallback_intent

_SF_PAYLOAD = {
    "current_condition": [
        {
            "temp_C": "18",
            "precipMM": "0.0",
            "lang_fr": [{"value": "Ciel dégagé"}],
            "weatherDesc": [{"value": "Clear"}],
        }
    ]
}


def test_detect_weather() -> None:
    assert detect_weather_intent("quel temps à San Francisco")
    assert detect_weather_intent("météo Paris")
    assert not detect_weather_intent("briefing du jour")


def test_extract_place_defaults_paris() -> None:
    assert extract_weather_place("météo") == "Paris"
    assert extract_weather_place("quel temps à San Francisco") == "San Francisco"
    assert extract_weather_place("météo à Lyon demain") == "Lyon"


def test_extract_place_rejects_injection() -> None:
    assert extract_weather_place("météo à http://evil") == "Paris"
    assert extract_weather_place("météo à Paris;rm") == "Paris"


def test_format_facts_gold_shape() -> None:
    line = format_weather_facts("San Francisco", _SF_PAYLOAD)
    assert line == "San Francisco — 18 °C, ciel dégagé, pas de pluie."


def test_weather_reply_mocked(monkeypatch) -> None:
    monkeypatch.setattr(
        "services.secretary_weather.fetch_weather",
        lambda place: f"{place} — 18 °C, ciel dégagé, pas de pluie.",
    )
    out = weather_reply("quel temps à San Francisco")
    assert "San Francisco" in out
    assert "18 °C" in out


def test_keyword_fallback_weather_and_research() -> None:
    assert keyword_fallback_intent("météo à Paris") == "weather"
    assert keyword_fallback_intent("recherche sur les agents IA") == "research"
    assert keyword_fallback_intent("briefing du jour") == "briefing"
    assert keyword_fallback_intent("bonjour ça va") is None


def test_handle_instruction_weather_skips_llm() -> None:
    from agents.secretary_instruction import SecretaryInstructionMixin

    class _Agent(SecretaryInstructionMixin):
        AGENT_NAME = "secretary"
        db = MagicMock()

        def _handle_weather(self, instruction: str) -> str:
            return "San Francisco — 18 °C, ciel dégagé, pas de pluie."

    agent = _Agent()
    with patch(
        "services.secretary_intent_llm.classify_secretary_intent",
        side_effect=RuntimeError("no credits"),
    ):
        out = agent.handle_instruction("quel temps à San Francisco")
    assert "18 °C" in out
