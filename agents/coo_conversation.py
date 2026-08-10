"""COO fast chat path — Telegram-friendly responses without CrewAI."""
from __future__ import annotations

import logging

from agents.coo_constants import COO_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class COOConversationMixin:
    """Requires ``create_task_log``, ``AGENT_NAME``, and ``_trim_summary``."""

    def _handle_conversation(
        self,
        instruction: str,
        *,
        project_name: str | None = None,
        telegram_chat_id: int | None = None,
    ) -> str:
        """Réponse chat rapide — pas de CrewAI (évite les silences Telegram)."""
        from services.secretary_intents import build_academy_status_brief
        from services.telegram_chat_memory import get_context_block
        from services.telegram_presence import CANNOT_DO_ARIA, hub_online

        history = get_context_block(telegram_chat_id)
        academy = build_academy_status_brief()
        hub_line = "Hub en ligne." if hub_online() else "Hub ARRÊTÉ."

        memory_block = ""
        try:
            from skills.skill_agent_learning import get_learning_context

            memory_block = get_learning_context("coo", instruction)
        except Exception:
            pass

        prompt = f"""Emilie (CEO) t'écrit :
{instruction}

{history}

Projet indicatif : {project_name or "non précisé"}
État technique : {hub_line}

Contexte Academy / ops :
{academy[:1500]}

{memory_block}

Réponds comme Aria Voss, COO d'ALNUA — tutoiement, 3 à 8 phrases, français.
Sois directe et actionnable. Si tu ne peux pas exécuter : dis-le clairement et propose une alternative.
Si la demande concerne mails/agenda → renvoie vers Nadia.
Pas de markdown lourd — texte lisible sur Telegram."""

        try:
            from agents.base import LLMClient

            raw = LLMClient().complete(
                COO_SYSTEM_PROMPT,
                prompt,
                agent_id=self.AGENT_NAME,
                temperature=0.45,
            )
            text = (raw or "").strip()
            if not text:
                text = CANNOT_DO_ARIA
        except Exception as exc:
            logger.warning("coo conversation failed: %s", exc)
            text = (
                "Je n'ai pas pu répondre (IA ou Hub indisponible).\n\n"
                + CANNOT_DO_ARIA
            )

        try:
            self.create_task_log(
                self.AGENT_NAME, "handle_instruction", instruction, text[:300]
            )
        except Exception:
            pass
        return self._trim_summary(text)
