"""Secretary agent — ops NL handlers (research, wake, Aria, conversation)."""
from __future__ import annotations

import logging

from skills.skill_agent_learning import inject_learning_context

logger = logging.getLogger(__name__)


class SecretaryHandlersOpsMixin:
    """Requires ``SecretaryInstructionMixin._finish_instruction`` and ``AgentBase``."""

    @staticmethod
    def _telegram_chat_id(session_id: str) -> int | None:
        if not session_id.startswith("tg:"):
            return None
        try:
            return int(session_id.split(":", 1)[1])
        except (ValueError, IndexError):
            return None

    def _handle_research(self, instruction: str, *, session_id: str = "hub") -> str:
        from agents.coo_agent import _detect_research_intent, _extract_research_topic
        from services.bureau_library import generate_ceo_report, run_bureau_research
        from services.secretary_intents import extract_research_query

        chat_id = self._telegram_chat_id(session_id)
        is_telegram = chat_id is not None

        query = extract_research_query(instruction)
        if query == "__report__":
            report = generate_ceo_report(days=7)
            out = report.get("markdown") or report.get("executive_summary", "Rapport généré.")
            self._finish_instruction(instruction, out[:200])
            return out

        is_research, research_agent = _detect_research_intent(instruction)
        if is_research and research_agent == "rnd_agent":
            topic = _extract_research_topic(instruction, research_agent) or query
            if topic and len(topic) >= 4:
                from services.coo_telegram_intents import launch_rnd_investigation

                out = launch_rnd_investigation(topic, chat_id=chat_id)
                self._finish_instruction(instruction, out[:200])
                return out

        result = run_bureau_research(
            query,
            requested_by="nadia",
            blocking=not is_telegram,
            notify_chat_id=chat_id,
        )
        if not is_telegram and result.get("entries_saved") is not None:
            n = result.get("entries_saved", 0)
            out = (
                f"📚 **Recherche terminée** — « {query} »\n\n"
                f"**{n}** fiche(s) archivée(s) dans la bibliothèque.\n"
                "Rien n'a été supprimé — consulte **Bibliothèque** dans le Hub."
            )
        else:
            out = (
                f"📚 **Recherche lancée** — « {query} »\n\n"
                f"{result.get('message', '')}\n\n"
                + (
                    "Je t'enverrai le bilan ici dès que c'est prêt (~1-3 min)."
                    if is_telegram
                    else "Tout est archivé dans la bibliothèque. "
                    "Demande « rapport bibliothèque » pour un résumé CEO."
                )
            )
        self._finish_instruction(instruction, out[:200])
        return out

    def _handle_wake_ops(self, instruction: str) -> str:
        from services.agent_wake import wake_agents

        result = wake_agents(notify=False, retry_failed=True)
        summary = result.get("summary", "")
        out = (
            "✅ **Pipeline Academy relancé** — Théo (dev_app) reprend les exercices en file.\n\n"
            f"{summary}"
        )
        self._finish_instruction(instruction, out[:200])
        return out

    def _handle_aria_delegation(self, instruction: str) -> str:
        from agents.coo_agent import COOAgent
        from services.secretary_intents import extract_aria_delegation_message

        payload = extract_aria_delegation_message(instruction)
        try:
            response = COOAgent(self.db).handle_instruction(payload)
        except Exception:
            response = (
                "Aria est indisponible pour l'instant — vérifie que le bot COO tourne "
                "(@Alnua_coo_bot) ou que le Hub API est démarré."
            )
        out = f"📨 **Transmis à Aria** :\n\n{response}"
        self._finish_instruction(instruction, out[:200])
        return out

    def _handle_conversation(
        self,
        instruction: str,
        *,
        chat_id: int | str | None = None,
    ) -> str:
        from services.secretary_intents import build_academy_status_brief
        from services.telegram_chat_memory import get_context_block
        from services.telegram_presence import CANNOT_DO_NADIA, hub_online

        context = build_academy_status_brief()
        history = get_context_block(chat_id)
        hub_line = "Hub en ligne." if hub_online() else "Hub ARRÊTÉ — pas de pipeline ni actions lourdes."

        prompt = inject_learning_context(
            f"""Emilie t'écrit en langage naturel :
{instruction}

{history}

Contexte ALNUA :
{context}
État technique : {hub_line}

Réponds comme Nadia Faure, secrétaire personnelle d'Emilie (CEO) chez ALNUA.
Français, professionnel et chaleureux, 3 à 8 phrases max.
Tu tutoies Emilie. C'est SON agenda, SES mails.

Si la demande est hors de ton périmètre (ops lourdes, R&D, pipeline) :
dis-le clairement et propose de transmettre à Aria ou une alternative concrète.
Si tu ne comprends pas : demande une précision au lieu de rester vague.
Pas de JSON — texte direct.""",
            self.AGENT_NAME,
            instruction[:80],
        )
        try:
            raw = self._complete(prompt, temperature=0.5)
            text = (raw or "").strip()
            if not text:
                text = CANNOT_DO_NADIA
        except Exception as exc:
            logger.warning("secretary conversation failed: %s", exc)
            text = (
                "Je n'ai pas pu formuler une réponse (connexion IA ou Hub).\n\n"
                + CANNOT_DO_NADIA
            )
        self._finish_instruction(instruction, text)
        return text
