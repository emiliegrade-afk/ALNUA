"""Live internet brief — sources on screen, never invented hits."""

from __future__ import annotations

from services.live_web_brief import web_brief


def test_web_brief_includes_sources_and_summary_fence(monkeypatch):
    monkeypatch.setattr(
        "services.live_web_brief._search",
        lambda q: [
            {
                "title": "Agents IA 2026",
                "url": "https://example.com/agents",
                "content": "Les agents autonomes progressent.",
            }
        ],
    )
    out = web_brief("agents IA")
    assert "```summary" in out
    assert "https://example.com/agents" in out
    assert "Agents IA 2026" in out


def test_web_brief_empty_does_not_invent(monkeypatch):
    monkeypatch.setattr("services.live_web_brief._search", lambda q: [])
    out = web_brief("sujet vide")
    assert "Aucune source" in out
    assert "n'invente pas" in out


def test_search_fast_returns_within_budget(monkeypatch):
    import time

    from services import live_web_search as search

    def hang(query: str, max_results: int = 6):
        time.sleep(30)
        return [{"title": "late", "url": "https://example.com", "content": ""}]

    monkeypatch.setattr(search, "_search_now", hang)
    monkeypatch.setattr(search, "BUDGET_SECONDS", 0.3)
    started = time.perf_counter()
    assert search.search_fast("x") == []
    assert time.perf_counter() - started < 2


def test_google_news_rss_parsed(monkeypatch):
    from services import live_web_search as search

    xml = """
    <rss><channel>
      <item><title>Actu IA</title><link>https://example.com/a</link>
      <description>Les agents progressent</description></item>
    </channel></rss>
    """
    monkeypatch.setattr(search, "_get_text", lambda url: xml if "news.google" in url else "")
    hits = search._google_news("agents IA")
    assert hits[0]["title"] == "Actu IA"
    assert hits[0]["url"] == "https://example.com/a"


def test_handle_research_live_skips_rnd(monkeypatch):
    from agents.secretary_handlers_ops import SecretaryHandlersOpsMixin

    class Agent(SecretaryHandlersOpsMixin):
        AGENT_NAME = "secretary"

        def _finish_instruction(self, instruction: str, output: str) -> None:
            return None

    monkeypatch.setattr(
        "services.live_web_brief.web_brief",
        lambda q: f"Recherche internet — « {q} »\n\n• source",
    )

    def boom(*_a, **_k):
        raise AssertionError("rnd investigation must not run on live")

    monkeypatch.setattr(
        "services.coo_telegram_intents.launch_rnd_investigation",
        boom,
        raising=False,
    )
    out = Agent()._handle_research("recherche sur les agents IA", session_id="live-voice")
    assert "Recherche internet" in out
