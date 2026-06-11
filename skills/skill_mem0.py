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
    """Store a fact in long-term memory."""
    m = get_mem0()
    if m:
        m.add(content, agent_id=agent_id, user_id=user_id)


def recall(query: str, agent_id: str = "coo", user_id: str = "emilie") -> str:
    """Retrieve relevant memories for a query."""
    m = get_mem0()
    if not m:
        return ""
    results = m.search(query, agent_id=agent_id, user_id=user_id, limit=5)
    if not results:
        return ""
    return "\n".join(f"- {r['memory']}" for r in results)


def should_remember(message: str) -> bool:
    """True when the message looks like a durable decision or preference."""
    lowered = message.lower()
    return any(kw in lowered for kw in MEMORY_KEYWORDS)
