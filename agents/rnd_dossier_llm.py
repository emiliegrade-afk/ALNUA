"""R&D dossier agent — LLM section drafting and revision."""
from __future__ import annotations

import logging
from typing import Any

from agents.base import parse_json_response
from agents.rnd_center import get_vision
from agents.rnd_dossier_constants import CORE_LLM_SECTIONS
from agents.rnd_dossier_prompts import (
    REVISE_SECTION_SYSTEM,
    SECTION_DRAFT_SYSTEM,
    build_section_draft_user_prompt,
)
from services.rnd_schemas import RndDossierOut, SECTION_DEFINITIONS

logger = logging.getLogger(__name__)


class RndDossierLlmMixin:
    """Requires ``self.repo`` and fluff helpers from ``RndDossierHelpersMixin``."""

    def _draft_sections_llm(
        self,
        dossier: RndDossierOut,
        idea_row: dict[str, Any],
    ) -> dict[str, str]:
        keys = [k for k in CORE_LLM_SECTIONS if k in {s.section_key for s in dossier.sections}]
        user = build_section_draft_user_prompt(
            title=dossier.title,
            description=idea_row.get("description") or dossier.tagline or "",
            domain=dossier.domain,
            effort=idea_row.get("effort") or "M",
            why_now=idea_row.get("why_now") or "",
            reasoning=idea_row.get("agent_reasoning") or "",
            vision=dossier.vision_snapshot or get_vision(),
            competitive_context=self.repo.load_competitive_context(),
            section_keys=keys,
        )
        try:
            raw = self._complete(
                user,
                system_prompt=SECTION_DRAFT_SYSTEM,
                agent_id="rnd_agent",
                temperature=0.45,
                max_tokens=6000,
            )
            data = parse_json_response(raw)
            sections = data.get("sections") or {}
            return {k: str(v).strip() for k, v in sections.items() if v}
        except Exception as exc:
            logger.warning("rnd_dossier: LLM draft failed: %s", exc)
            return {}

    def _revise_section_llm(
        self,
        dossier: RndDossierOut,
        section_key: str,
        revision_note: str | None,
    ) -> str:
        current = next((s for s in dossier.sections if s.section_key == section_key), None)
        title = SECTION_DEFINITIONS.get(section_key, {}).get("title", section_key)
        user = (
            f"Section : {title} ({section_key})\n"
            f"Dossier : {dossier.title}\n\n"
            f"CONTENU ACTUEL :\n{current.content_md if current else ''}\n\n"
            f"NOTE DE RÉVISION :\n{revision_note or 'Améliorer la qualité, plus concret.'}"
        )
        raw = self._complete(
            user,
            system_prompt=REVISE_SECTION_SYSTEM,
            agent_id="rnd_agent",
            temperature=0.4,
            max_tokens=2500,
        )
        data = parse_json_response(raw)
        return str(data.get("content_md", "")).strip()
