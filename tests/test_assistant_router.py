"""Tests — assistant router Aria vs Nadia (H4)."""

from __future__ import annotations

from services.assistant_router import resolve_assistant_agent, strip_explicit_prefix


def test_explicit_aria_prefix():
    forced, cleaned = strip_explicit_prefix("@aria priorise les tickets")
    assert forced == "coo"
    assert "priorise" in cleaned.lower()


def test_explicit_nadia_prefix():
    forced, cleaned = strip_explicit_prefix("@nadia rédige un mail")
    assert forced == "secretary"
    assert "mail" in cleaned.lower()


def test_priorites_du_jour_goes_to_nadia():
    assert resolve_assistant_agent("Priorités du jour") == "secretary"


def test_mail_goes_to_nadia():
    assert resolve_assistant_agent("Rédige un mail de relance partenaire") == "secretary"


def test_rnd_goes_to_aria():
    assert resolve_assistant_agent("Lance une investigation R&D sur les agents") == "coo"


def test_academy_goes_to_nadia():
    assert resolve_assistant_agent("Rapport de la nuit Academy") == "secretary"


def test_bonjour_defaults_to_nadia():
    assert resolve_assistant_agent("bonjour") == "secretary"


def test_preferred_force():
    assert resolve_assistant_agent("hello world", preferred="secretary") == "secretary"
    assert resolve_assistant_agent("hello world", preferred="coo") == "coo"


def test_tie_prefers_secretary():
    # "nadia" and "aria" both present → secretary on tie
    assert resolve_assistant_agent("dis à nadia et aria") == "secretary"
