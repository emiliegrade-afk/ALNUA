"""Smoke test for Centre R&D cycle."""
from __future__ import annotations

import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

from agents.rnd_center import (  # noqa: E402
    _evaluate_idea,
    _generate_ideas,
    _llm,
    get_top_ideas,
    get_vision,
    inject_idea,
    run_rnd_cycle,
)


def main() -> None:
    print("=== LLM ping ===")
    sample = _llm("Reponds en une phrase.", "Test R&D ALNUA", max_tokens=200)
    print(sample[:200])

    print("\n=== Evaluate one idea ===")
    idea = {
        "id": "smoke_eval",
        "title": "App van offline-first",
        "domain": "app",
        "description": "Gestion van nomade offline",
        "why_now": "2026",
        "effort": "M",
        "status": "pending_evaluation",
    }
    evaluated = _evaluate_idea(idea, get_vision())
    print(
        "verdict=", evaluated.get("verdict"),
        "score=", evaluated.get("score"),
        "status=", evaluated.get("status"),
    )

    print("\n=== Generate ideas (mini) ===")
    generated = _generate_ideas("trends nomades 2026", "", get_vision(), [])
    print("generated count:", len(generated))
    if generated:
        print("first:", generated[0].get("title"))

    print("\n=== Inject + cycle ===")
    inject_idea("Capteur IoT batterie van low-cost", source="test_script")
    result = run_rnd_cycle(blocking=True)
    print("cycle result:", {k: result.get(k) for k in ("ideas_generated", "ideas_evaluated", "go_count", "prototyped")})

    print("\n=== Top ideas ===")
    for item in get_top_ideas(limit=5):
        print(
            f"- {item.get('title', '')[:50]} | {item.get('verdict')} | "
            f"score={item.get('score')} | {item.get('status')}"
        )


if __name__ == "__main__":
    main()
