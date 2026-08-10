"""R&D dossier agent — promote, submit, validate, and CRUD workflow."""
from __future__ import annotations

import logging
from typing import Any

from agents.base import log_agent_action
from agents.rnd_center import get_vision
from services.rnd_schemas import RndDossierOut
from skills.skill_langfuse import trace_agent

logger = logging.getLogger(__name__)


class RndDossierWorkflowMixin:
    """Requires ``self.repo``, enrich mixin, and status sync helpers."""

    @trace_agent("rnd_dossier")
    def promote_idea(
        self,
        idea_id: str,
        *,
        actor: str = "emilie",
        enrich: bool = False,
    ) -> dict[str, Any]:
        """Promote idea → dossier skeleton; optional sync enrich (phase 2)."""
        vision = get_vision()
        competitive = self.repo.load_competitive_context()
        dossier, idea = self.repo.promote_idea_to_dossier(
            idea_id,
            vision_snapshot=vision,
            competitive_context=competitive,
            actor=actor,
        )

        enriching = False
        if enrich:
            try:
                dossier = self.enrich_dossier(str(dossier.id), actor=actor)
                enriching = False
            except Exception as exc:
                logger.exception("rnd_dossier: enrich failed after promote %s: %s", dossier.id, exc)
                enriching = True
            refreshed = self.repo.get_idea_by_id(idea_id)
            if refreshed:
                idea = refreshed

        logger.info(
            "rnd_dossier_agent: promoted %s -> dossier %s (%s)",
            idea_id,
            dossier.id,
            dossier.slug,
        )
        if enrich and not enriching:
            message = (
                f"Dossier R&D « {dossier.title} » créé et enrichi — "
                f"{dossier.sections_total_count} sections."
            )
        elif enrich:
            message = (
                f"Dossier R&D « {dossier.title} » créé — enrichissement partiel, "
                f"relancez depuis l'onglet Dossiers."
            )
        else:
            message = (
                f"Dossier R&D « {dossier.title} » créé — "
                f"{dossier.sections_total_count} sections squelette."
            )
        log_agent_action(
            self.db, self.AGENT_NAME, "promote_idea",
            input_summary=f"idea_id={idea_id} enrich={enrich}",
            output_summary=f"dossier={dossier.id} ({dossier.slug})",
        )
        return {
            "dossier": dossier.model_dump(),
            "idea": idea.model_dump(),
            "message": message,
            "enriching": enriching,
        }

    @trace_agent("rnd_dossier")
    def validate_section(
        self,
        dossier_id: str,
        section_key: str,
        *,
        actor: str = "emilie",
        note: str | None = None,
    ) -> RndDossierOut:
        dossier = self.repo.validate_section(dossier_id, section_key, actor, note)
        if not dossier:
            raise ValueError("Validation impossible")
        self._sync_dossier_status(dossier_id)
        log_agent_action(
            self.db, self.AGENT_NAME, "validate_section",
            input_summary=f"dossier_id={dossier_id} section={section_key}",
            output_summary="section validée",
        )
        return self.repo.get_dossier(dossier_id) or dossier

    @trace_agent("rnd_dossier")
    def request_section_revision(
        self,
        dossier_id: str,
        section_key: str,
        revision_note: str,
        *,
        actor: str = "emilie",
    ) -> RndDossierOut:
        dossier = self.repo.request_section_revision(
            dossier_id, section_key, revision_note, actor
        )
        if not dossier:
            raise ValueError("Révision impossible")
        log_agent_action(
            self.db, self.AGENT_NAME, "request_section_revision",
            input_summary=f"dossier_id={dossier_id} section={section_key}",
            output_summary="révision demandée",
        )
        return dossier

    def list_dossiers(
        self,
        status: str | None = None,
        domain: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        items = self.repo.list_dossiers(status=status, domain=domain, limit=limit)
        return [i.model_dump() for i in items]

    @trace_agent("rnd_dossier")
    def create_dossier(
        self,
        idea_id: str,
        *,
        actor: str = "emilie",
        enrich: bool = False,
    ) -> dict[str, Any]:
        """Create dossier from idea (alias promote — POST /rnd/dossiers)."""
        return self.promote_idea(idea_id, actor=actor, enrich=enrich)

    @trace_agent("rnd_dossier")
    def submit_user_dossier(
        self,
        payload: dict[str, Any],
        *,
        actor: str = "emilie",
    ) -> dict[str, Any]:
        """Create idea + dossier from Emilie's structured proposal."""
        from agents.rnd_center import submit_user_proposal
        from services.rnd_schemas import RndUserSubmitBody

        body = RndUserSubmitBody.model_validate(payload)
        idea = submit_user_proposal(
            body.title,
            tagline=body.tagline,
            domain=body.domain,
            why_now=body.why_now,
            sections=body.sections,
            source=body.source,
        )

        section_seed = dict(body.sections)
        if body.why_now and body.why_now.strip():
            market = section_seed.get("market", "")
            why_block = f"**Pourquoi maintenant**\n\n{body.why_now.strip()}"
            section_seed["market"] = f"{market}\n\n{why_block}".strip() if market else why_block

        vision = get_vision()
        competitive = self.repo.load_competitive_context()
        dossier, idea_out = self.repo.promote_idea_to_dossier(
            idea["id"],
            vision_snapshot=vision,
            competitive_context=competitive,
            actor=actor,
            seed_content_override=section_seed,
            tagline=body.tagline,
        )

        self.repo.log_event(
            str(dossier.id),
            "user_proposal_submitted",
            actor,
            {"title": body.title, "domain": body.domain, "sections_filled": list(section_seed.keys())},
        )

        enriching = False
        if body.enrich:
            try:
                dossier = self.enrich_dossier(str(dossier.id), actor=actor)
            except Exception as exc:
                logger.exception("rnd_dossier: enrich after user submit failed: %s", exc)
                enriching = True
            refreshed = self.repo.get_idea_by_id(idea["id"])
            if refreshed:
                idea_out = refreshed

        message = (
            f"Dossier « {dossier.title} » soumis au pôle R&D — "
            f"{len(section_seed)} section(s) rédigées par toi."
        )
        if body.enrich and not enriching:
            message += " Enrichissement agents terminé."
        elif body.enrich:
            message += " Enrichissement agents en cours (30–60 s)."

        log_agent_action(
            self.db, self.AGENT_NAME, "submit_user_dossier",
            input_summary=f"title={body.title} domain={body.domain}",
            output_summary=f"dossier={dossier.id}",
        )
        return {
            "dossier": dossier.model_dump(),
            "idea": idea_out.model_dump(),
            "message": message,
            "enriching": enriching,
        }

    @trace_agent("rnd_dossier")
    def update_section(
        self,
        dossier_id: str,
        section_key: str,
        content_md: str,
        *,
        actor: str = "emilie",
    ) -> RndDossierOut:
        dossier = self.repo.get_dossier(dossier_id)
        if not dossier:
            raise ValueError("Dossier introuvable")
        if not any(s.section_key == section_key for s in dossier.sections):
            raise ValueError(f"Section introuvable : {section_key}")
        self.repo.update_section_content(
            dossier_id,
            section_key,
            content_md.strip(),
            status="draft",
        )
        self.repo.log_event(
            dossier_id,
            "section_edited",
            actor,
            {"section_key": section_key},
        )
        updated = self.repo.get_dossier(dossier_id)
        if not updated:
            raise RuntimeError("Mise à jour section échouée")
        log_agent_action(
            self.db, self.AGENT_NAME, "update_section",
            input_summary=f"dossier_id={dossier_id} section={section_key}",
            output_summary="section mise à jour",
        )
        return updated
