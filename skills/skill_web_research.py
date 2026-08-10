"""
skill_web_research.py — Veille web autonome par domaine.

Chaque agent a ses topics de recherche.
Toutes les semaines (ou sur demande du COO), il cherche sur le web,
distille les infos clés et les écrit dans sa propre Mem0.

Usage :
    from skills.skill_web_research import research_domain, teach_agent
    research_domain("marketing_agent")
    teach_agent("marketing_agent", "Les Reels courtes < 30s ont +40% de reach en 2026")
    research_domain("hardware_agent", topic="RISC-V 2026")
"""

from __future__ import annotations

import logging
import threading
import time
from datetime import datetime

from skills.skill_web_research_search import distill_research, search
from skills.skill_web_research_topics import AGENT_RESEARCH_TOPICS  # noqa: F401 — re-export

logger = logging.getLogger(__name__)

# Backward-compatible alias for internal callers
_search = search


def research_domain(
    agent_id: str,
    topic: str | None = None,
    blocking: bool = False,
) -> None:
    """
    Lance la veille web d'un agent sur son domaine.
    Si topic est fourni, recherche ce topic spécifique.
    Sinon, parcourt tous les topics configurés pour cet agent.

    Non-bloquant par défaut — tourne en daemon thread.
    """

    def _run():
        topics = [topic] if topic else AGENT_RESEARCH_TOPICS.get(agent_id, [])
        if not topics:
            logger.info("research_domain: aucun topic configuré pour %s", agent_id)
            return

        from skills.skill_mem0 import remember

        date = datetime.now().strftime("%Y-%m-%d")
        total_learned = 0

        for t in topics:
            logger.info("research_domain: %s recherche '%s'", agent_id, t)
            results = search(t, max_results=5)
            if not results:
                continue

            lesson = distill_research(agent_id, t, results)
            if not lesson:
                lesson = f"• Source archivée — à relire plus tard ({t})"

            memory_entry = f"[Recherche {date}] {t} :\n{lesson}"
            remember(memory_entry, agent_id=agent_id)

            try:
                from services.bureau_library import add_entry, bureau_for_agent

                short = lesson if len(lesson) <= 400 else (lesson[:397] + "...")
                add_entry(
                    bureau=bureau_for_agent(agent_id),
                    title=t[:200],
                    summary=short,
                    digest=lesson,
                    timing="later",
                    source_url=str(results[0].get("url") or ""),
                    source_title=str(results[0].get("title") or t),
                    topics=[t],
                    agent_id=agent_id,
                    requested_by="scheduler",
                    query=t,
                )
            except Exception:
                pass

            total_learned += 1
            logger.info("research_domain: %s — leçon enregistrée pour '%s'", agent_id, t)

        if total_learned > 0:
            logger.info(
                "research_domain: %s — %d leçon(s) enregistrée(s) ce cycle",
                agent_id,
                total_learned,
            )

    if blocking:
        _run()
    else:
        threading.Thread(target=_run, daemon=True).start()


def teach_agent(agent_id: str, content: str, source: str = "manual") -> None:
    """
    Pousse une leçon directement dans la mémoire d'un agent.
    Utilisé par : toi (via COO), ou par un autre agent qui partage une découverte.
    """
    try:
        from skills.skill_mem0 import remember

        date = datetime.now().strftime("%Y-%m-%d")
        entry = f"[Leçon externe {date} — source: {source}] {content}"
        remember(entry, agent_id=agent_id)
        logger.info("teach_agent: leçon injectée pour %s", agent_id)
    except Exception as exc:
        logger.warning("teach_agent failed for %s: %s", agent_id, exc)


def research_all_agents(blocking: bool = False) -> None:
    """
    Lance la veille pour tous les agents configurés.
    Appelé par le scheduler hebdomadaire.
    """

    def _run():
        for agent_id in AGENT_RESEARCH_TOPICS:
            research_domain(agent_id, blocking=True)
            time.sleep(2)

    if blocking:
        _run()
    else:
        threading.Thread(target=_run, daemon=True).start()
