"""R&D social agent — calendar generation and strategy markdown."""

from __future__ import annotations

import logging
from typing import Any

from agents.base import parse_json_response
from agents.rnd_social_helpers import USE_LLM, _dossier_context, _parse_launch_date
from agents.rnd_social_prompts import SOCIAL_STRATEGY_SYSTEM
from services.rnd_schemas import RndDossierOut, RndSocialCalendarItemOut
from services.rnd_social import (
    assert_social_pipeline_unlocked,
    build_template_calendar,
    default_launch_anchor,
)

logger = logging.getLogger(__name__)


class RndSocialCalendarMixin:
    """Requires ``self.repo``, ``self.social``, ``self._complete``."""

    def generate_calendar(
        self,
        dossier_id: str,
        *,
        force: bool = False,
        launch_date: str | None = None,
        actor: str = "rnd_social_agent",
    ) -> dict[str, Any]:
        dossier = self.repo.get_dossier(dossier_id)
        if not dossier:
            raise ValueError("Dossier introuvable")

        assert_social_pipeline_unlocked(dossier)

        existing = self.social.list_calendar(dossier.id)
        if existing and not force:
            return {
                "calendar": [i.model_dump() for i in existing],
                "created": 0,
                "message": "Calendrier déjà existant (force=true pour regénérer)",
            }

        if force:
            self.social.delete_planned_calendar(dossier.id)

        anchor = _parse_launch_date(launch_date) if launch_date else default_launch_anchor()
        templates = build_template_calendar(dossier.id, launch_date=anchor)

        if USE_LLM:
            templates = self._enrich_calendar_with_llm(dossier, templates)

        created_items: list[RndSocialCalendarItemOut] = []
        local_rows: list[dict[str, Any]] = []

        for tpl in templates:
            row = self.social.create_calendar_item(
                dossier.id,
                phase=tpl["phase"],
                milestone=tpl["milestone"],
                planned_at=tpl["planned_at"],
                notes=tpl.get("notes"),
            )
            local_rows.append({
                "id": row["id"],
                "phase": row["phase"],
                "milestone": row.get("milestone"),
                "planned_at": row.get("planned_at"),
            })
            created_items.append(
                RndSocialCalendarItemOut(
                    id=str(row["id"]),
                    dossier_id=dossier.id,
                    phase=row["phase"],
                    milestone=row.get("milestone"),
                    planned_at=row.get("planned_at"),
                    status="planned",
                    notes=row.get("notes"),
                    platforms=tpl.get("_platforms", []),
                    content_type=tpl.get("_content_type"),
                )
            )

        strategy_md = self._build_social_strategy_md(dossier, created_items)
        self.repo.update_section_content(
            dossier.id,
            "social_strategy",
            strategy_md,
            status="under_review",
        )
        self.social.write_local_calendar(dossier.slug, local_rows)

        self.repo.log_event(
            dossier.id,
            "social_calendar_generated",
            actor,
            {"items": len(created_items), "launch_at": anchor.isoformat()},
        )

        return {
            "calendar": [i.model_dump() for i in created_items],
            "created": len(created_items),
            "social_strategy_md": strategy_md,
            "message": f"{len(created_items)} jalons social planifiés",
        }

    def list_calendar(self, dossier_id: str) -> list[dict[str, Any]]:
        dossier = self.repo.get_dossier(dossier_id)
        if not dossier:
            raise ValueError("Dossier introuvable")
        return [i.model_dump() for i in self.social.list_calendar(dossier.id)]

    def patch_calendar_item(
        self,
        dossier_id: str,
        item_id: str,
        values: dict[str, Any],
    ) -> dict[str, Any]:
        dossier = self.repo.get_dossier(dossier_id)
        if not dossier:
            raise ValueError("Dossier introuvable")
        item = self.social.get_calendar_item(item_id)
        if not item or str(item.get("dossier_id")) != dossier.id:
            raise ValueError("Jalon introuvable")
        allowed = {"milestone", "planned_at", "status", "notes"}
        payload = {k: v for k, v in values.items() if k in allowed and v is not None}
        if not payload:
            raise ValueError("Aucun champ à mettre à jour")
        return self.social.update_calendar_item(item_id, payload)

    def _enrich_calendar_with_llm(
        self,
        dossier: RndDossierOut,
        templates: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Optionally tweak milestones/notes via LLM — keep structure."""
        try:
            context = _dossier_context(dossier)
            milestones = "\n".join(
                f"- {t['phase']}: {t['milestone']}" for t in templates
            )
            user = f"""Projet : {dossier.title}
{context}

Jalons template :
{milestones}

Réponds en JSON : {{ "items": [ {{ "phase": "...", "milestone": "...", "notes": "..." }} ] }}
Adapte les milestones au projet (concret, pas de fluff). Garde les mêmes phases et dates."""
            raw = self._complete(
                user,
                system_prompt=SOCIAL_STRATEGY_SYSTEM,
                agent_id="content",
                temperature=0.7,
            )
            parsed = parse_json_response(raw)
            by_phase: dict[str, dict[str, str]] = {}
            for it in parsed.get("items", []):
                by_phase[it.get("phase", "")] = it
            for tpl in templates:
                override = by_phase.get(tpl["phase"], {})
                if override.get("milestone"):
                    tpl["milestone"] = override["milestone"][:200]
                if override.get("notes"):
                    tpl["notes"] = override["notes"][:500]
        except Exception as exc:
            logger.warning("rnd_social calendar LLM enrich skipped: %s", exc)
        return templates

    def _build_social_strategy_md(
        self,
        dossier: RndDossierOut,
        items: list[RndSocialCalendarItemOut],
    ) -> str:
        lines = [
            f"# Stratégie social — {dossier.title}",
            "",
            f"**Domaine :** {dossier.domain} · **Pipeline :** internal → launch → post-launch",
            "",
            "## Calendrier teaser",
            "",
        ]
        for item in items:
            date = (item.planned_at or "")[:10]
            lines.append(f"- **{date}** — `{item.phase}` — {item.milestone}")
            if item.notes:
                lines.append(f"  - {item.notes}")
        lines.extend([
            "",
            "## Approbation",
            "",
            "Les posts générés passent par **Content** (`/content`) en `pending_approval` avant publication.",
            "",
            "## KPIs (solo + IA)",
            "",
            "- Taux d'engagement par phase (teaser vs launch)",
            "- Clics waitlist / DM si pre-launch",
            "- Coût temps contenu < 2h/semaine",
        ])
        return "\n".join(lines)
