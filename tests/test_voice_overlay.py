"""Voice overlay — facts vs spoken quip (Phase 47 Lot 1 / DEC-033)."""

from __future__ import annotations

from services.voice_overlay import (
    fallback_overlay,
    generate_overlay,
    leaks_facts,
    sensitive_tokens,
    should_speak_overlay,
    spoken_overlay,
)

AGENDA_FACTS = """12h30 — déjeuner Camille
15h — bloc R&D
2 mails urgents (Jules, Solène)
"""
AGENDA_VOICE = (
    "Journée dense. Je te laisse le bloc R&D — je m'occupe de Camille et des deux mails."
)

MAIL_FACTS = (
    "Brouillon à Jules, objet « Facture août ».\n\n"
    "Bonjour Jules,\n\nVoici la facture d'août.\nCordialement,\nEmilie"
)
MAIL_VOICE = "Brouillon prêt pour Jules. Tu valides, j'envoie."

CONTACT_FACTS = "Camille Rousseau — camille@alnua.dev — +33 6 12 34 56 78"
CONTACT_VOICE = "Je te l'affiche. Dis-moi si je dois lui écrire."

WEATHER_FACTS = "San Francisco — 18 °C, ciel dégagé, pas de pluie."
WEATHER_VOICE = "Beau temps. Pas besoin de parapluie."

ARIA_FACTS = "Théo bloqué sur le merge Hub. Pipeline Academy : 2 PRs ouvertes."
ARIA_VOICE = "Je relance Théo sur le merge. Toi tu regardes les deux PRs si tu veux."


def test_gold_overlays_do_not_leak_facts() -> None:
    assert not leaks_facts(AGENDA_VOICE, AGENDA_FACTS)
    assert not leaks_facts(MAIL_VOICE, MAIL_FACTS)
    assert not leaks_facts(CONTACT_VOICE, CONTACT_FACTS)
    assert not leaks_facts(WEATHER_VOICE, WEATHER_FACTS)
    assert not leaks_facts(ARIA_VOICE, ARIA_FACTS)


def test_leaks_email_phone_time_url_and_sir() -> None:
    assert leaks_facts("camille@alnua.dev voilà", CONTACT_FACTS)
    assert leaks_facts("son 06 12 34 56 78", CONTACT_FACTS)
    assert leaks_facts("RDV 12h30 avec Camille", AGENDA_FACTS)
    assert leaks_facts("vois https://alnua.dev", "voir https://alnua.dev/x")
    assert leaks_facts("Here's what you requested sir", AGENDA_FACTS)
    assert leaks_facts('{"slots":[]}', AGENDA_FACTS)
    assert leaks_facts("Il fait 18 degrés", WEATHER_FACTS)


def test_sensitive_tokens_catch_schedule_and_contact() -> None:
    tokens = sensitive_tokens(CONTACT_FACTS)
    assert any("@" in t for t in tokens)
    agenda = sensitive_tokens(AGENDA_FACTS)
    assert any("12h30" in t.replace(" ", "").lower() or "12h30" in t.lower() for t in agenda)


def test_nadia_speaks_aria_only_on_action() -> None:
    assert should_speak_overlay("secretary", AGENDA_FACTS)
    assert should_speak_overlay("coo", ARIA_FACTS)
    assert not should_speak_overlay("coo", "Pipeline Academy : 2 PRs ouvertes.")
    assert not should_speak_overlay("secretary", "")
    assert not should_speak_overlay("secretary", "❌ Souci technique")


def test_generate_overlay_returns_gold_when_llm_ok(monkeypatch) -> None:
    monkeypatch.setattr(
        "agents.base_llm.LLMClient.complete",
        lambda self, *a, **k: AGENDA_VOICE,
    )
    out = generate_overlay(AGENDA_FACTS, agent_id="secretary")
    assert out == AGENDA_VOICE


def test_generate_overlay_drops_leaks(monkeypatch) -> None:
    monkeypatch.setattr(
        "agents.base_llm.LLMClient.complete",
        lambda self, *a, **k: "12h30 déjeuner Camille, 15h R&D, mails Jules.",
    )
    assert generate_overlay(AGENDA_FACTS, agent_id="secretary") is None


def test_generate_overlay_none_on_llm_error(monkeypatch) -> None:
    def _boom(self, *a, **k):
        raise RuntimeError("no llm")

    monkeypatch.setattr("agents.base_llm.LLMClient.complete", _boom)
    assert generate_overlay(AGENDA_FACTS, agent_id="secretary") is None


def test_generate_overlay_aria_skips_status_only() -> None:
    assert generate_overlay("Pipeline Academy : 2 PRs ouvertes.", agent_id="coo") is None


def test_fallback_overlay_never_leaks_gold_facts() -> None:
    for facts in (AGENDA_FACTS, MAIL_FACTS, CONTACT_FACTS, WEATHER_FACTS, ARIA_FACTS):
        line = fallback_overlay(facts, agent_id="secretary")
        assert line
        assert not leaks_facts(line, facts)


def test_fallback_overlay_weather_and_brief() -> None:
    assert fallback_overlay(WEATHER_FACTS, agent_id="secretary") == (
        "Beau temps. Pas besoin de parapluie."
    )
    rain = "Lyon — 12 °C, averses, pluie possible."
    assert fallback_overlay(rain, agent_id="secretary") == "Prends un parapluie."
    brief = "☀️ Bonjour Emilie — Nadia ici.\n\nPriorité 1 pipeline"
    line = fallback_overlay(brief, agent_id="secretary")
    assert line == "Le brief est prêt. Le détail est à l'écran."
    research = "📚 **Recherche lancée** — « agents IA »"
    assert fallback_overlay(research, agent_id="secretary") == (
        "Recherche lancée. Le détail est à l'écran."
    )


def test_aria_fallback_only_on_action() -> None:
    assert fallback_overlay(ARIA_FACTS, agent_id="coo") == (
        "J'agis. Le détail est à l'écran."
    )
    assert fallback_overlay("Pipeline Academy : 2 PRs ouvertes.", agent_id="coo") is None
    assert not leaks_facts("J'agis. Le détail est à l'écran.", ARIA_FACTS)


def test_spoken_overlay_uses_fallback_when_llm_off(
    monkeypatch,
) -> None:
    monkeypatch.setenv("VOICE_OVERLAY_LLM", "0")
    from config.settings import get_settings

    get_settings.cache_clear()

    def _should_not_run(*a, **k):
        raise RuntimeError("should not call llm")

    monkeypatch.setattr("services.voice_overlay.generate_overlay", _should_not_run)
    line = spoken_overlay(AGENDA_FACTS, agent_id="secretary")
    get_settings.cache_clear()
    assert line
    assert not leaks_facts(line, AGENDA_FACTS)


def test_spoken_overlay_prefers_llm_when_ok(monkeypatch) -> None:
    monkeypatch.setenv("VOICE_OVERLAY_LLM", "1")
    from config.settings import get_settings

    get_settings.cache_clear()
    monkeypatch.setattr(
        "services.voice_overlay.generate_overlay",
        lambda facts, agent_id="secretary": AGENDA_VOICE,
    )
    assert spoken_overlay(AGENDA_FACTS, agent_id="secretary") == AGENDA_VOICE
    get_settings.cache_clear()
