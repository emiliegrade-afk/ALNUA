"""Secretary — Live Lot 6 handlers (image, LinkedIn draft, free slots, HTML)."""

from __future__ import annotations

import logging
import re

from skills.skill_agent_learning import inject_learning_context

logger = logging.getLogger(__name__)

_LINKEDIN_RE = re.compile(r"\blinkedin\b|\bpost(?:e|er)?\b.{0,20}\blinkedin", re.I)
_SLOT_KEYS = ("créneau", "creneau", "créneaux", "creneaux", "dispo demain", "quand suis-je libre")
_PUBLISH_KEYS = (
    "publie le post",
    "publie sur linkedin",
    "valide le post",
    "valide linkedin",
    "poste maintenant",
)


def wants_linkedin_draft(text: str) -> bool:
    n = text.lower()
    if any(k in n for k in ("ouvre", "ouvrir", "connecte", "connecter")):
        return False
    return bool(_LINKEDIN_RE.search(text))


def wants_free_slots(text: str) -> bool:
    n = text.lower()
    return any(k in n for k in _SLOT_KEYS)


def wants_publish_confirm(text: str) -> bool:
    n = text.lower()
    return any(k in n for k in _PUBLISH_KEYS) or n.strip() in {"publie", "publie-le"}


class SecretaryHandlersLiveMixin:
    """Requires ``SecretaryInstructionMixin._finish_instruction`` and ``AgentBase``."""

    def _handle_image_nl(self, instruction: str) -> str:
        from services.live_media import handle_image_request

        out = handle_image_request(instruction)
        self._finish_instruction(instruction, out[:200])
        return out

    def _handle_slots_nl(self, instruction: str) -> str:
        from services.live_free_slots import free_slots_brief

        out = free_slots_brief()
        self._finish_instruction(instruction, out[:200])
        return out

    def _handle_pc_input_nl(self, instruction: str) -> str:
        from services.live_pc_input import maybe_pc_input, propose_input

        out = maybe_pc_input(instruction) or propose_input(instruction)
        self._finish_instruction(instruction, out[:200])
        return out

    def _handle_html_nl(self, instruction: str) -> str:
        from services.live_html_app import run_html_app

        out = run_html_app(instruction)
        self._finish_instruction(instruction, out[:200])
        return out

    def _handle_linkedin_nl(self, instruction: str) -> str:
        from services.live_social_drafts import draft_linkedin_sofia, format_linkedin_draft

        try:
            raw = draft_linkedin_sofia(instruction)
        except Exception as extra:
            logger.warning("linkedin sofia failed: %s", extra)
            raw = ""
        if not raw:
            prompt = inject_learning_context(
                "Emilie veut un post LinkedIn (brouillon seulement, jamais publié).\n"
                f"Demande : {instruction}\n"
                "Français, 120 à 900 caractères, sans hashtag spam, texte brut.",
                self.AGENT_NAME,
                instruction[:80],
            )
            try:
                raw = (self._complete(prompt, temperature=0.4, max_tokens=700) or "").strip()
            except Exception as extra:
                logger.warning("linkedin draft llm failed: %s", extra)
                raw = ""
        if not raw:
            out = "Je n'ai pas pu rédiger le post. Reformule en une phrase le message à publier."
            self._finish_instruction(instruction, out)
            return out
        out = format_linkedin_draft(raw)
        self._finish_instruction(instruction, out[:200])
        return out

    def _handle_publish_confirm(self, instruction: str) -> str:
        from services.live_social_drafts import latest_draft_id, publish_linkedin_draft

        draft_id = latest_draft_id()
        if not draft_id:
            out = "Aucun brouillon LinkedIn en attente. Demande d'abord « rédige un post LinkedIn »."
            self._finish_instruction(instruction, out)
            return out
        result = publish_linkedin_draft(draft_id)
        out = str(result.get("message") or "Publication impossible.")
        self._finish_instruction(instruction, out[:200])
        return out
