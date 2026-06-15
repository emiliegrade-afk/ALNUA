"""
rnd_dossier_agent.py — Promote R&D ideas into structured dossiers.

Phase 1: skeleton dossier + sections from idea data.
Phase 2: LLM section drafting, finance, anti-fluff, validate/revise.
"""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any

from agents.accountant_agent import AccountantAgent
from agents.base import LLMClient, parse_json_response
from agents.rnd_center import get_vision
from agents.rnd_dossier_prompts import (
    REVISE_SECTION_SYSTEM,
    SECTION_DRAFT_SYSTEM,
    build_section_draft_user_prompt,
)
from services.rnd_finance_estimate import finance_json_to_markdown
from services.rnd_repository import RndRepository, get_rnd_repository
from services.rnd_schemas import RndDossierOut, SECTION_DEFINITIONS

logger = logging.getLogger(__name__)

FLUFF_PATTERNS = re.compile(
    r"vont adorer|marché énorme|énorme marché|millennials vont|génération .+ va",
    re.IGNORECASE,
)

CORE_LLM_SECTIONS = (
    "problem", "solution", "market", "mvp", "feasibility", "risks", "decision",
)


class RndDossierAgent:
    AGENT_NAME = "rnd_dossier_agent"

    def __init__(self, repo: RndRepository | None = None) -> None:
        self.repo = repo or get_rnd_repository()
        self.llm = LLMClient()

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
        return {
            "dossier": dossier.model_dump(),
            "idea": idea.model_dump(),
            "message": message,
            "enriching": enriching,
        }

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
        return updated

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
        return updated

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
        return self.repo.get_dossier(dossier_id) or dossier

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
        return dossier

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

    def list_dossiers(
        self,
        status: str | None = None,
        domain: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        items = self.repo.list_dossiers(status=status, domain=domain, limit=limit)
        return [i.model_dump() for i in items]

    def _should_use_llm(self) -> bool:
        if os.getenv("RND_DOSSIER_USE_LLM", "true").lower() in ("0", "false", "no"):
            return False
        return bool(self.llm._settings.openrouter_api_key.strip())

    @staticmethod
    def _contains_fluff(text: str) -> bool:
        return bool(FLUFF_PATTERNS.search(text))

    @staticmethod
    def _is_section_placeholder(content_md: str) -> bool:
        """True when section has no user/agent content worth preserving."""
        t = (content_md or "").strip()
        if not t or len(t) < 25:
            return True
        placeholders = (
            "_À compléter",
            "_Business case à générer",
            "_Risques à identifier",
        )
        return any(t.startswith(p) for p in placeholders)

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
            raw = self.llm.complete(
                SECTION_DRAFT_SYSTEM,
                user,
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
        raw = self.llm.complete(
            REVISE_SECTION_SYSTEM,
            user,
            agent_id="rnd_agent",
            temperature=0.4,
            max_tokens=2500,
        )
        data = parse_json_response(raw)
        return str(data.get("content_md", "")).strip()

    def _sync_dossier_status(self, dossier_id: str) -> None:
        dossier = self.repo.get_dossier(dossier_id)
        if not dossier:
            return
        validated = dossier.sections_validated_count
        total = dossier.sections_total_count
        if validated == 0:
            status = "draft"
        elif validated < total:
            status = "partial_validated"
        else:
            status = "ready_for_ceo"
        self.repo.update_dossier(dossier_id, {"status": status})


    def create_dossier(
        self,
        idea_id: str,
        *,
        actor: str = "emilie",
        enrich: bool = False,
    ) -> dict[str, Any]:
        """Create dossier from idea (alias promote — POST /rnd/dossiers)."""
        return self.promote_idea(idea_id, actor=actor, enrich=enrich)

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

        return {
            "dossier": dossier.model_dump(),
            "idea": idea_out.model_dump(),
            "message": message,
            "enriching": enriching,
        }

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
        return updated


def promote_idea_to_dossier(
    idea_id: str,
    actor: str = "emilie",
    *,
    enrich: bool = False,
) -> dict[str, Any]:
    return RndDossierAgent().promote_idea(idea_id, actor=actor, enrich=enrich)
