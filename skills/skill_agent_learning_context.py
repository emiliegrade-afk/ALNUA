"""Inject Mem0 lessons and bureau library catalog into agent prompts."""
from __future__ import annotations

import logging

from config.agent_models import memory_agent_id

logger = logging.getLogger(__name__)


def get_learning_context(agent_id: str, task: str) -> str:
    """
    Relit les leçons Mem0 pertinentes AVANT une tâche.
    Retourne un bloc prêt à injecter dans un prompt (vide si aucune mémoire).
    """
    try:
        from skills.skill_mem0 import recall

        aid = memory_agent_id(agent_id)
        memories = recall(query=task[:300], agent_id=aid)
        if not memories:
            return ""
        return (
            "\n\n─── LEÇONS APPRISES (à appliquer) ───\n"
            f"{memories}\n"
            "─── Ne répète pas les erreurs déjà documentées ───"
        )
    except Exception as exc:
        logger.debug("get_learning_context failed for %s: %s", agent_id, exc)
        return ""


def get_library_context(agent_id: str, task: str = "") -> str:
    """
    Topic catalog hits relevant to this agent/task — scannable, not truncated bodies.

    Agents see which subjects exist in the library and can deep-learn on demand.
    Strong / ``now`` matches trigger a one-shot ``learn_topic`` and inject the digest.
    """
    try:
        from services.bureau_library import bureau_for_agent
        from services.topic_catalog import search_topics_for_task

        bureau = bureau_for_agent(agent_id)
        hits = search_topics_for_task(task or "", bureau=bureau, limit=5)
        if not hits:
            from services.bureau_library import list_entries

            res = list_entries(bureau=bureau, limit=8)
            entries = list(res.get("entries", []))
            if not entries and bureau != "hub":
                hub_res = list_entries(bureau="hub", timing="now", limit=4)
                entries = list(hub_res.get("entries", []))
            if not entries:
                return ""
            lines = [
                f"- [{e.get('timing', 'later')}] {e.get('title', '')} "
                f"(sujets: {', '.join(str(t) for t in (e.get('topics') or [])[:4]) or 'n/a'})"
                for e in entries[:5]
            ]
            return (
                "\n\n─── BIBLIOTHÈQUE DU BUREAU (catalogue) ───\n"
                + "\n".join(lines)
                + "\n─── Utilise learn_topic(slug) pour charger le digest complet ───"
            )

        lines: list[str] = []
        deep_block = ""
        for row in hits:
            slug = row.get("slug", "")
            n = len(row.get("entry_ids") or [])
            now_flag = "now" if row.get("has_now") else "later"
            titles = "; ".join((row.get("titles") or [])[:2])
            lines.append(
                f"- [{now_flag}] `{slug}` ({n} fiches) — {titles}"
            )

        top = hits[0]
        should_deep = bool(top.get("has_now")) or (
            task and top.get("slug") and str(top.get("slug")) in (task or "").lower().replace(" ", "-")
        )
        if should_deep and top.get("slug"):
            try:
                from skills.skill_library_memory import learn_topic

                learned = learn_topic(agent_id, str(top["slug"]), promote=True)
                if learned.get("ok") and learned.get("lesson"):
                    deep_block = (
                        f"\n─── DIGEST APPRIS (`{top.get('slug')}`) ───\n"
                        f"{str(learned['lesson'])[:2500]}\n"
                        "─── Fin digest ───"
                    )
                    try:
                        from skills.skill_agent_learning_compress import auto_compress_if_needed

                        auto_compress_if_needed(agent_id)
                    except Exception:
                        pass
            except Exception as exc:
                logger.debug("auto learn_topic skipped: %s", exc)

        return (
            "\n\n─── CATALOGUE BIBLIOTHÈQUE (sujets disponibles) ───\n"
            + "\n".join(lines)
            + "\n─── Charge un sujet via learn_topic si besoin ───"
            + deep_block
        )
    except Exception as exc:
        logger.debug("get_library_context failed for %s: %s", agent_id, exc)
        return ""


def inject_learning_context(prompt: str, agent_id: str, task: str) -> str:
    """Injecte leçons Mem0 + catalogue bibliothèque (et digest si deep-learn) dans un prompt."""
    block = get_learning_context(agent_id, task)
    library = get_library_context(agent_id, task)
    extra = block + library
    return prompt + extra if extra else prompt
