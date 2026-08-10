"""Session compression — distill many Mem0 lessons into durable digests."""
from __future__ import annotations

import json
import logging
import threading
import urllib.request
from datetime import datetime

from config.agent_models import memory_agent_id

from skills.skill_agent_learning_constants import (
    COMPRESS_SYSTEM,
    LEARN_MODEL,
    OPENROUTER_BASE,
    openrouter_api_key,
)

logger = logging.getLogger(__name__)


def compress_agent_memory(
    agent_id: str,
    raw_memories: list[str],
    blocking: bool = True,
) -> str | None:
    """
    Compresse une liste de mémoires brutes en un digest synthétique.
    Écrit le digest compressé dans Mem0 sous un tag spécial [DIGEST].
    """
    if not raw_memories:
        return None

    canonical_id = memory_agent_id(agent_id)
    memories_text = "\n".join(f"- {m}" for m in raw_memories[:50])

    payload = json.dumps({
        "model": LEARN_MODEL or "anthropic/claude-haiku-4-5",
        "messages": [
            {"role": "system", "content": COMPRESS_SYSTEM},
            {
                "role": "user",
                "content": (
                    f"Agent : {canonical_id}\n"
                    f"Nombre de leçons : {len(raw_memories)}\n\n"
                    f"Leçons à synthétiser :\n{memories_text}"
                ),
            },
        ],
        "temperature": 0.2,
        "max_tokens": 300,
    }).encode()

    req = urllib.request.Request(
        OPENROUTER_BASE,
        data=payload,
        headers={
            "Authorization": f"Bearer {openrouter_api_key()}",
            "Content-Type": "application/json",
        },
    )

    def _run() -> str | None:
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read())
                digest = data["choices"][0]["message"].get("content", "").strip()

            if not digest:
                return None

            try:
                from skills.skill_mem0 import remember

                date = datetime.now().strftime("%Y-%m-%d")
                remember(
                    f"[DIGEST {date}] Règles durables {canonical_id} :\n{digest}",
                    agent_id=canonical_id,
                )
                logger.info(
                    "skill_agent_learning: digest écrit pour %s (%d leçons → digest)",
                    canonical_id, len(raw_memories),
                )
            except Exception as exc:
                logger.warning("compress_agent_memory: Mem0 write failed: %s", exc)

            return digest
        except Exception as exc:
            logger.warning("compress_agent_memory: LLM call failed: %s", exc)
            return None

    if blocking:
        return _run()
    threading.Thread(target=_run, daemon=True).start()
    return None


def auto_compress_if_needed(
    agent_id: str,
    threshold: int = 20,
    blocking: bool = False,
) -> bool:
    """
    Vérifie si l'agent a trop de mémoires et compresse si nécessaire.

    Returns:
        True si compression lancée, False si pas nécessaire.
    """
    try:
        from skills.skill_mem0 import recall

        canonical_id = memory_agent_id(agent_id)
        raw = recall(query="leçons apprises", agent_id=canonical_id)
        if not raw:
            return False

        if len(str(raw)) < threshold * 80:
            return False

        memories = str(raw).split("\n") if isinstance(raw, str) else [str(raw)]
        compress_agent_memory(canonical_id, memories, blocking=blocking)
        return True

    except Exception as exc:
        logger.debug("auto_compress_if_needed failed for %s: %s", agent_id, exc)
        return False
