"""Persistent agent memory via Mem0."""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

MEMORY_KEYWORDS = ("décide", "objectif", "priorité", "strategie", "stratégie")


def get_mem0():
    try:
        from mem0 import MemoryClient

        api_key = os.getenv("MEM0_API_KEY")
        if not api_key:
            return None
        return MemoryClient(api_key=api_key)
    except Exception as exc:
        logger.debug("Mem0 unavailable: %s", exc)
        return None


def remember(content: str, agent_id: str = "coo", user_id: str = "emilie") -> None:
    """Store a fact in long-term memory.

    Mem0 v3 sépare agent_id et user_id en namespaces distincts.
    On utilise agent_id uniquement — plus simple et filtrage fiable.
    """
    from config.agent_models import memory_agent_id

    m = get_mem0()
    if m:
        m.add(content, agent_id=memory_agent_id(agent_id))


def recall(query: str, agent_id: str = "coo", user_id: str = "emilie") -> str:
    """Retrieve relevant memories for a query."""
    from config.agent_models import memory_agent_id

    m = get_mem0()
    if not m:
        return ""
    canonical_id = memory_agent_id(agent_id)
    try:
        results = m.search(
            query, filters={"agent_id": canonical_id}, limit=5
        )
    except Exception as exc:
        # Mem0 must never block the COO — API shape changes are common.
        logger.warning("Mem0 recall failed: %s", exc)
        return ""
    if not results:
        return ""
    items = results if isinstance(results, list) else results.get("results", [])
    parts = []
    for r in items:
        if isinstance(r, str):
            parts.append(f"- {r}")
        elif isinstance(r, dict):
            parts.append(f"- {r.get('memory') or r.get('text') or str(r)}")
    return "\n".join(parts)


def should_remember(message: str) -> bool:
    """True when the message looks like a durable decision or preference."""
    lowered = message.lower()
    return any(kw in lowered for kw in MEMORY_KEYWORDS)
