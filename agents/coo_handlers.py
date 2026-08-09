"""COO fast-path intents (R&D, academy, research, teach) before CrewAI."""
from __future__ import annotations

import logging
from typing import Any

from agents.coo_intents import (
    RND_KEYWORDS,
    _detect_research_intent,
    _detect_teach_intent,
    _extract_research_topic,
)

logger = logging.getLogger(__name__)


def try_fast_intents(
    coo: Any,
    instruction: str,
    telegram_chat_id: int | None = None,
) -> str | None:
    """Return a response if a fast path matched, else None."""
    msg_lower = instruction.lower()

    # Investigation R&D sur un sujet libre (Telegram NL)
    from services.coo_telegram_intents import (
        capture_idea,
        detect_idea_capture,
        detect_rnd_investigation,
        extract_investigation_query,
        launch_rnd_investigation,
    )

    if detect_rnd_investigation(instruction):
        topic = extract_investigation_query(instruction)
        if topic:
            ack = launch_rnd_investigation(topic, chat_id=telegram_chat_id)
            try:
                coo.create_task_log(
                    coo.AGENT_NAME, "rnd_investigation", instruction, ack[:200]
                )
            except Exception:
                logger.warning("coo: task log rnd_investigation failed", exc_info=True)
            return ack

    # Boîte à idées — capture NL sans formule magique
    if detect_idea_capture(instruction):
        try:
            idea = capture_idea(instruction, source="Emilie via COO")
            title = idea.get("title", instruction[:80])
            ack = (
                f"💡 Idée enregistrée dans le Centre R&D\n"
                f"{title[:100]}\n"
                f"Visible dans Propositions — brainstorm ou promote quand tu veux."
            )
            coo.create_task_log(coo.AGENT_NAME, "idea_capture", instruction, ack[:200])
            return ack
        except ValueError:
            return "❌ Idée vide — précise ce que tu veux garder."

    from services.secretary_intents import (
        build_academy_status_brief,
        detect_academy_intent,
        detect_wake_ops,
    )

    if detect_wake_ops(instruction):
        from services.agent_wake import wake_agents

        result = wake_agents(notify=False, retry_failed=True)
        ack = f"✅ Pipeline Academy relancé — Théo reprend le codage.\n{result.get('summary', '')}"
        try:
            coo.create_task_log(coo.AGENT_NAME, "wake_agents", instruction, ack[:200])
        except Exception:
            pass
        return ack

    if detect_academy_intent(instruction):
        brief = build_academy_status_brief()
        try:
            coo.create_task_log(coo.AGENT_NAME, "academy_status", instruction, brief[:200])
        except Exception:
            pass
        return brief

    # Commandes R&D
    if any(kw in msg_lower for kw in RND_KEYWORDS):
        from agents.rnd_center import run_rnd_cycle, inject_idea, set_vision, get_top_ideas
        if "explore l'idée" in msg_lower or "idée r&d" in msg_lower:
            from services.coo_telegram_intents import extract_idea_text

            body = extract_idea_text(instruction) or instruction
            inject_idea(body, source="Emilie via COO")
            return f"💡 Idée ajoutée au pipeline R&D : \"{body[:80]}...\" — sera évaluée au prochain cycle."
        elif "fil conducteur" in msg_lower or "focus r&d" in msg_lower:
            set_vision(instruction)
            return "🎯 Fil conducteur R&D mis à jour."
        elif "meilleures idées" in msg_lower or "rapport r&d" in msg_lower:
            top = get_top_ideas(limit=5)
            if not top:
                return "Aucune idée R&D évaluée pour l'instant. Lance un cycle : 'lance un cycle R&D'."
            lines = ["🏆 Top idées R&D ALNUA :"]
            for i, idea in enumerate(top, 1):
                lines.append(f"{i}. [{idea.get('domain','?').upper()}] {idea['title']} — score {idea.get('score','?')}/30 ({idea.get('verdict','?')})")
                lines.append(f"   {idea.get('description','')[:100]}")
            return "\n".join(lines)
        else:
            run_rnd_cycle(blocking=False)
            return "🧪 Cycle R&D lancé — rapport dans quelques minutes sur Telegram."

    # Recherche web → bibliothèque des bureaux
    is_research, research_agent = _detect_research_intent(instruction)
    if is_research:
        from services.bureau_library import bureau_for_agent, run_bureau_research

        topic = _extract_research_topic(instruction, research_agent)
        if research_agent == "rnd_agent" and topic and len(topic) >= 4:
            ack = launch_rnd_investigation(topic, chat_id=telegram_chat_id)
            try:
                coo.create_task_log(
                    coo.AGENT_NAME, "rnd_investigation", instruction, ack[:200]
                )
            except Exception:
                logger.warning("coo: task log rnd_investigation failed", exc_info=True)
            return ack
        query = topic or instruction.strip()[:400]
        bureaus = [bureau_for_agent(research_agent)] if research_agent else None
        result = run_bureau_research(
            query,
            bureaus=bureaus,
            requested_by="aria",
            blocking=telegram_chat_id is None,
            notify_chat_id=telegram_chat_id,
        )
        try:
            coo.create_task_log(
                coo.AGENT_NAME, "library_research", instruction, result.get("message", "")[:200]
            )
        except Exception:
            pass
        if telegram_chat_id is None and result.get("entries_saved") is not None:
            n = result.get("entries_saved", 0)
            return (
                f"📚 **Recherche terminée** — « {query} »\n\n"
                f"**{n}** fiche(s) rangée(s) dans la bibliothèque (rien supprimé)."
            )
        return f"📚 {result.get('message', 'Recherche lancée.')}"

    # Commande d'injection de leçon — "apprends au marketing_agent que les Reels < 30s performent mieux"
    is_teach, teach_agent_id, teach_content = _detect_teach_intent(instruction)
    if is_teach and teach_agent_id and teach_content:
        from skills.skill_web_research import teach_agent
        teach_agent(teach_agent_id, teach_content, source="COO/Emilie")
        return f"✅ Leçon injectée pour {teach_agent_id} : \"{teach_content[:100]}...\""

    return None
