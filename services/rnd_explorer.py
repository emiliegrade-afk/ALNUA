"""R&D Explorer — external signals for /rnd-v2 Phase 28 (Vague E).

Wraps trend_monitor with R&D defaults and a brainstorm/rnd synthesis
(not Camille marketing angles). Honest empty when sources fail.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# Default watch topics for ALNUA labs — not fabricated metrics.
DEFAULT_RND_TOPICS: list[str] = [
    "AI agents",
    "robotics",
    "Unreal Engine",
    "LLM",
    "edge AI",
]

DEFAULT_SOURCES: list[str] = ["hn", "reddit", "github"]


def scan_signals(
    topics: list[str] | None = None,
    sources: list[str] | None = None,
    limit: int = 40,
) -> dict[str, Any]:
    """Raw external signals — no LLM. Safe for frequent UI refresh."""
    from services.trend_monitor import aggregate_trends

    topics_use = list(topics) if topics else list(DEFAULT_RND_TOPICS)
    sources_use = list(sources) if sources else list(DEFAULT_SOURCES)
    # When topics are set, aggregate_trends filters titles — too aggressive
    # for a watch board. Fetch all, then soft-rank by topic hit.
    items = aggregate_trends(sources=sources_use, topics=None)
    ranked = _rank_for_topics(items, topics_use)
    sliced = ranked[: max(1, min(limit, 80))]
    return {
        "ok": True,
        "mode": "signals",
        "topics": topics_use,
        "sources": sources_use,
        "total": len(ranked),
        "items": [i.to_dict() for i in sliced],
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "empty_reason": None if sliced else "Aucune source n'a renvoyé de signal (réseau ou rate-limit).",
    }


def brief_explorer(
    topics: list[str] | None = None,
    sources: list[str] | None = None,
    agent_id: str = "brainstorm",
    limit: int = 25,
) -> dict[str, Any]:
    """Signals + R&D-oriented LLM brief (Idris/Alex)."""
    from services.input_sanitizer import sanitize_user_input
    from services.trend_monitor import aggregate_trends

    topics_use = list(topics) if topics else list(DEFAULT_RND_TOPICS)
    sources_use = list(sources) if sources else list(DEFAULT_SOURCES)
    agent = (agent_id or "brainstorm").strip()
    if agent not in ("brainstorm", "rnd_agent", "analyst_business"):
        agent = "brainstorm"

    items = aggregate_trends(sources=sources_use, topics=None)
    ranked = _rank_for_topics(items, topics_use)[: max(1, min(limit, 40))]
    if not ranked:
        return {
            "ok": False,
            "mode": "brief",
            "topics": topics_use,
            "sources_used": sources_use,
            "items": [],
            "synthesis": "",
            "rnd_signals": [],
            "dossier_hooks": [],
            "error": "Aucune tendance trouvée",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    synth = _synthesize_rnd(ranked, topics_use, agent)
    return {
        "ok": True,
        "mode": "brief",
        "topics": topics_use,
        "sources_used": sources_use,
        "total_items": len(ranked),
        "items": [i.to_dict() for i in ranked[:12]],
        "synthesis": sanitize_user_input(str(synth.get("synthesis") or ""), max_length=2000),
        "rnd_signals": [
            sanitize_user_input(str(s), max_length=200)
            for s in (synth.get("rnd_signals") or [])[:6]
            if str(s).strip()
        ],
        "dossier_hooks": [
            sanitize_user_input(str(h), max_length=300)
            for h in (synth.get("dossier_hooks") or [])[:5]
            if str(h).strip()
        ],
        "agent_id": agent,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def _rank_for_topics(items: list[Any], topics: list[str]) -> list[Any]:
    keywords = [t.lower().strip() for t in topics if t.strip()]
    if not keywords:
        return sorted(items, key=lambda x: x.score, reverse=True)

    def rank_key(item: Any) -> tuple[int, int]:
        title = (item.title or "").lower()
        hits = sum(1 for kw in keywords if kw in title)
        return (hits, item.score)

    # Prefer topic hits, keep high-score non-hits after
    return sorted(items, key=rank_key, reverse=True)


def _synthesize_rnd(items: list[Any], topics: list[str], agent_id: str) -> dict[str, Any]:
    try:
        from agents.base import LLMClient, parse_json_response
        from services.input_sanitizer import sanitize_user_input

        llm = LLMClient()
        top_text = "\n".join(
            [
                f"- [{item.source.upper()}] "
                f"{sanitize_user_input(item.title, max_length=300)} "
                f"(score: {item.score})"
                for item in items[:20]
            ]
        )
        topics_str = ", ".join(topics) if topics else "R&D général"
        system = (
            "Tu es un analyste R&D ALNUA (laboratoire). "
            "Tu identifies signaux technologiques et hooks de dossier, "
            "pas des angles marketing. JSON uniquement."
        )
        prompt = f"""Analyse ces signaux externes pour topics R&D : {topics_str}

SIGNAUX :
{top_text}

JSON :
- synthesis (string): 2-3 phrases pour le labo
- rnd_signals (list[string]): 3-5 signaux tech à surveiller
- dossier_hooks (list[string]): 2-4 idées de dossier / investigation (pas de posts social)
"""
        raw = llm.complete(system, prompt, agent_id=agent_id, temperature=0.3)
        parsed = parse_json_response(raw)
        if isinstance(parsed, dict):
            return parsed
    except Exception as exc:
        logger.warning("rnd explorer synthesis failed: %s", exc)
    return {
        "synthesis": "Synthèse LLM indisponible — signaux bruts ci-dessous.",
        "rnd_signals": [i.title for i in items[:3]],
        "dossier_hooks": [],
    }
