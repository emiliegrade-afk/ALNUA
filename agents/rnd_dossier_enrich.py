"""R&D dossier agent — enrichment, finance, and section regeneration."""
from __future__ import annotations

import logging
from typing import Any

from agents.accountant_agent import AccountantAgent
from agents.base import log_agent_action
from services.rnd_schemas import RndDossierOut
from skills.skill_langfuse import trace_agent

logger = logging.getLogger(__name__)


class RndDossierEnrichMixin:
    """Requires ``self.repo``, LLM + fluff helpers from sibling mixins."""

    @trace_agent("rnd_dossier")
    def enrich_dossier(self, dossier_id: str, *, actor: str = "rnd_dossier_agent") -> RndDossierOut:
        """Generate LLM sections + finance estimate for an existing dossier."""
        dossier = self.repo.get_dossier(dossier_id)
        if not dossier:
            raise ValueError(f"Dossier introuvable : {dossier_id}")

        idea_row = self.repo.get_idea_db_row(dossier.idea_id) or {}

        if self._should_use_llm():
            sections_md = self._draft_sections_llm(dossier, idea_row)
            existing_by_key = {s.section_key: s.content_md for s in dossier.sections}
            for key, content in sections_md.items():
                if not self._is_section_placeholder(existing_by_key.get(key, "")):
                    continue
                if content and not self._contains_fluff(content):
                    self.repo.update_section_content(
                        dossier_id, key, content, status="under_review"
                    )
                elif content:
                    logger.warning("rnd_dossier: fluff detected in %s, keeping draft", key)

        finance_result = AccountantAgent().estimate_for_dossier(
            dossier.model_dump(),
            idea_row,
            add_commentary=self._should_use_llm(),
        )
        self.repo.set_finance_json(dossier_id, finance_result["finance_json"])
        bc_existing = next(
            (s.content_md for s in dossier.sections if s.section_key == "business_case"),
            "",
        )
        if self._is_section_placeholder(bc_existing):
            self.repo.update_section_content(
                dossier_id,
                "business_case",
                finance_result["business_case_md"],
                status="under_review",
            )
        self.repo.log_event(
            dossier_id,
            "finance_estimated",
            "accountant_agent",
            {"verdict": finance_result["finance_json"].get("verdict_finance")},
        )
        self.repo.log_event(dossier_id, "sections_enriched", actor, {})

        updated = self.repo.get_dossier(dossier_id)
        if not updated:
            raise RuntimeError("Enrichissement échoué")
        log_agent_action(
            self.db, self.AGENT_NAME, "enrich_dossier",
            input_summary=f"dossier_id={dossier_id}",
            output_summary=f"verdict={finance_result['finance_json'].get('verdict_finance')}",
        )
        return updated

    @trace_agent("rnd_dossier")
    def regenerate_section(
        self,
        dossier_id: str,
        section_key: str,
        *,
        revision_note: str | None = None,
        actor: str = "emilie",
    ) -> RndDossierOut:
        """Regenerate or revise a single section."""
        dossier = self.repo.get_dossier(dossier_id)
        if not dossier:
            raise ValueError("Dossier introuvable")

        if section_key == "business_case":
            constraint = revision_note
            idea_row = self.repo.get_idea_db_row(dossier.idea_id) or {}
            result = AccountantAgent().estimate_for_dossier(
                dossier.model_dump(),
                idea_row,
                constraint=constraint,
                add_commentary=True,
            )
            self.repo.set_finance_json(dossier_id, result["finance_json"])
            self.repo.update_section_content(
                dossier_id,
                "business_case",
                result["business_case_md"],
                status="under_review",
                revision_note=revision_note,
            )
        elif self._should_use_llm():
            content = self._revise_section_llm(dossier, section_key, revision_note)
            if self._contains_fluff(content):
                raise ValueError("Contenu rejeté : formulations marketing non autorisées.")
            self.repo.update_section_content(
                dossier_id,
                section_key,
                content,
                status="under_review",
                revision_note=revision_note,
            )
        else:
            raise RuntimeError("OPENROUTER_API_KEY requise pour régénérer cette section")

        self.repo.log_event(
            dossier_id,
            "section_regenerated",
            actor,
            {"section_key": section_key, "note": revision_note},
        )
        updated = self.repo.get_dossier(dossier_id)
        if not updated:
            raise RuntimeError("Section régénérée mais lecture échouée")
        log_agent_action(
            self.db, self.AGENT_NAME, "regenerate_section",
            input_summary=f"dossier_id={dossier_id} section={section_key}",
            output_summary="section régénérée",
        )
        return updated

    @trace_agent("rnd_dossier")
    def estimate_finance(
        self,
        dossier_id: str,
        *,
        constraint: str | None = None,
    ) -> dict[str, Any]:
        dossier = self.repo.get_dossier(dossier_id)
        if not dossier:
            raise ValueError("Dossier introuvable")
        idea_row = self.repo.get_idea_db_row(dossier.idea_id) or {}
        result = AccountantAgent().estimate_for_dossier(
            dossier.model_dump(),
            idea_row,
            constraint=constraint,
            add_commentary=True,
        )
        self.repo.set_finance_json(dossier_id, result["finance_json"])
        self.repo.update_section_content(
            dossier_id,
            "business_case",
            result["business_case_md"],
            status="under_review",
        )
        log_agent_action(
            self.db, self.AGENT_NAME, "estimate_finance",
            input_summary=f"dossier_id={dossier_id}",
            output_summary=f"verdict={result['finance_json'].get('verdict_finance')}",
        )
        return result

    def get_dossier(
        self,
        dossier_id: str,
        *,
        refresh_stale_finance: bool = True,
    ) -> RndDossierOut | None:
        dossier = self.repo.get_dossier(dossier_id)
        if not dossier or not refresh_stale_finance:
            return dossier
        from services.rnd_finance_estimate import is_stale_finance

        if is_stale_finance(dossier.finance_json):
            try:
                logger.info("rnd_dossier: refreshing stale finance for %s", dossier_id)
                self.estimate_finance(dossier_id)
                return self.repo.get_dossier(dossier_id)
            except Exception as exc:
                logger.warning("rnd_dossier: stale finance refresh failed: %s", exc)
        return dossier
