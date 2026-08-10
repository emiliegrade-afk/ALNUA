"""
skill_library_memory.py — Scan library topics + deep-learn on demand into Mem0 / vault digests.

Usage:
    from skills.skill_library_memory import scan_library_topics, learn_topic, ensure_topic_digest

    scan_library_topics("fastapi", bureau="app")
    learn_topic("dev_app", "fastapi")
"""

from __future__ import annotations

import logging
from typing import Any

from skills.skill_library_memory_digest import build_topic_digest

logger = logging.getLogger(__name__)

PROMOTE_LEARN_THRESHOLD = 3


def scan_library_topics(
    query: str = "",
    *,
    bureau: str | None = None,
    timing_now_only: bool = False,
    limit: int = 20,
) -> dict[str, Any]:
    """Return scannable topic catalog hits for agents."""
    from services.topic_catalog import list_topics

    return list_topics(
        query=query,
        bureau=bureau,
        timing_now_only=timing_now_only,
        limit=limit,
    )


def ensure_topic_digest(
    slug: str,
    *,
    force: bool = False,
    max_entries: int = 12,
) -> dict[str, Any]:
    """Build or refresh a vault digest note synthesizing library entries for a topic."""
    return build_topic_digest(slug, force=force, max_entries=max_entries)


def learn_topic(
    agent_id: str,
    topic_slug: str,
    *,
    force_digest: bool = False,
    promote: bool = True,
) -> dict[str, Any]:
    """
    Deep-learn a topic: load/create digest, distill into Mem0 for the agent,
    export a memory note, mark distribution receipts, optionally promote to skill.
    """
    from config.agent_models import memory_agent_id
    from services.library_distribution import record_learned
    from services.obsidian_vault import ensure_vault_layout, get_vault_path
    from services.topic_catalog import get_topic, increment_learn_count
    from skills.skill_agent_learning import auto_compress_if_needed
    from skills.skill_library_memory_digest import utc_now

    topic = get_topic(topic_slug)
    if not topic:
        return {"ok": False, "error": "topic_not_found", "slug": topic_slug}

    digest = ensure_topic_digest(topic_slug, force=force_digest)
    if not digest.get("ok"):
        return digest

    digest_text = str(digest.get("content") or "")
    body = digest_text
    if body.startswith("---"):
        end = body.find("\n---", 3)
        if end > 0:
            body = body[end + 4 :].lstrip()

    lesson = _distill_lesson(agent_id, topic.get("slug") or topic_slug, body)
    mem_ok = False
    try:
        from skills.skill_mem0 import remember

        aid = memory_agent_id(agent_id)
        fact = (
            f"[LIBRARY TOPIC {topic.get('slug')}] {lesson}"
            if lesson
            else f"[LIBRARY TOPIC {topic.get('slug')}] {body[:1500]}"
        )
        remember(fact[:4000], agent_id=aid, user_id="emilie")
        mem_ok = True
    except Exception as exc:
        logger.warning("learn_topic Mem0 failed: %s", exc)

    learned_ids: list[str] = []
    for eid in topic.get("entry_ids") or []:
        try:
            record_learned(str(eid), agent_id)
            learned_ids.append(str(eid))
        except Exception:
            pass

    vault = get_vault_path()
    ensure_vault_layout(vault)
    agent_dir = vault / "memory" / "agents" / memory_agent_id(agent_id)
    agent_dir.mkdir(parents=True, exist_ok=True)
    note_name = f"{topic.get('slug')}-{utc_now()[:10]}.md"
    note_path = agent_dir / note_name
    note_path.write_text(
        "\n".join(
            [
                "---",
                "type: agent_memory",
                f"agent_id: {memory_agent_id(agent_id)}",
                f"topic: {topic.get('slug')}",
                f'learned_at: "{utc_now()}"',
                "---",
                "",
                f"# Apprentissage — {topic.get('slug')}",
                "",
                lesson or body[:3000],
                "",
            ]
        ),
        encoding="utf-8",
    )

    count_res = increment_learn_count(str(topic.get("slug")))
    try:
        auto_compress_if_needed(agent_id)
    except Exception:
        pass

    promoted = None
    if promote:
        try:
            from agents.knowledge_skill_promoter import maybe_promote_topic_skill

            promoted = maybe_promote_topic_skill(str(topic.get("slug")))
        except Exception as exc:
            logger.debug("skill promotion skipped: %s", exc)

    return {
        "ok": True,
        "agent_id": memory_agent_id(agent_id),
        "slug": topic.get("slug"),
        "digest_path": digest.get("path"),
        "memory_note": str(note_path.relative_to(vault)).replace("\\", "/"),
        "mem0": mem_ok,
        "lesson": lesson,
        "entries_learned": learned_ids,
        "learn_count": count_res.get("learn_count"),
        "promoted_skill": promoted,
    }


def _distill_lesson(agent_id: str, slug: str, digest_body: str) -> str:
    try:
        from agents.base import LLMClient
        from config.agent_models import memory_agent_id
        from skills.skill_agent_learning import LEARNING_LENS

        lens = LEARNING_LENS.get(
            memory_agent_id(agent_id),
            "Tu es un agent ALNUA. Retiens ce qui est actionnable pour ton rôle.",
        )
        system = (
            f"{lens}\n"
            "Distille 3-6 leçons concrètes depuis ce digest bibliothèque. "
            "Puces courtes. Pas d'intro."
        )
        user = f"Sujet: {slug}\n\n{digest_body[:6000]}"
        llm = LLMClient()
        raw = llm.complete(system, user, agent_id=agent_id, temperature=0.2, max_tokens=800)
        return (raw or "").strip()
    except Exception as exc:
        logger.debug("distill lesson failed: %s", exc)
        lines = [ln.strip() for ln in digest_body.splitlines() if ln.strip() and not ln.startswith("#")]
        return "\n".join(f"- {ln}" for ln in lines[:8])
