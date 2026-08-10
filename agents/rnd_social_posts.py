"""R&D social agent — post generation and queue integration."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from agents.base import parse_json_response
from agents.content_agent import PLATFORM_RULES, VALID_CONTENT_TYPES, VALID_PLATFORMS
from agents.rnd_social_helpers import (
    USE_LLM,
    _dossier_context,
    _parse_planned_at,
    _template_for_milestone,
    _template_post,
    ensure_project_for_dossier,
)
from agents.rnd_social_prompts import SOCIAL_POST_SYSTEM
from services.rnd_schemas import RndDossierOut, RndSocialCalendarItemOut
from services.rnd_social import assert_social_pipeline_unlocked, is_social_pipeline_unlocked

logger = logging.getLogger(__name__)


class RndSocialPostsMixin:
    """Requires ``self.repo``, ``self.social``, ``self.db``, ``self._complete``."""

    def generate_post_for_item(
        self,
        dossier_id: str,
        item_id: str,
        *,
        platforms: list[str] | None = None,
        actor: str = "rnd_social_agent",
    ) -> dict[str, Any]:
        dossier = self.repo.get_dossier(dossier_id)
        if not dossier:
            raise ValueError("Dossier introuvable")

        assert_social_pipeline_unlocked(dossier)

        item_row = self.social.get_calendar_item(item_id)
        if not item_row or str(item_row.get("dossier_id")) != dossier.id:
            raise ValueError("Jalon calendrier introuvable")

        if item_row.get("post_id"):
            posts = self.db.select("posts_queue", filters={"id": item_row["post_id"]}, limit=1)
            if posts:
                return {
                    "post": posts[0],
                    "calendar_item_id": item_id,
                    "message": "Post déjà généré pour ce jalon",
                }

        phase = item_row.get("phase", "")
        if phase == "internal":
            raise ValueError(
                "Jalon interne — pas de post public. Passe aux jalons teaser / pre-launch."
            )

        tpl = _template_for_milestone(item_row.get("milestone", ""), phase)
        target_platforms = platforms or tpl.get("platforms") or []
        if tpl.get("skip_post") or not target_platforms:
            raise ValueError("Ce jalon ne génère pas de post public.")

        project_id = ensure_project_for_dossier(dossier, self.db)

        posts_created: list[dict[str, Any]] = []
        primary_post: dict[str, Any] | None = None

        for i, platform in enumerate(target_platforms):
            if platform not in VALID_PLATFORMS:
                continue
            content_type = tpl.get("content_type", "teaser")
            if content_type not in VALID_CONTENT_TYPES:
                content_type = "teaser"

            post_data = self._generate_post_content(
                dossier,
                item_row,
                platform=platform,
                content_type=content_type,
            )
            scheduled = _parse_planned_at(item_row.get("planned_at")) + timedelta(hours=i * 2)

            row = self.db.insert(
                "posts_queue",
                {
                    "project_id": project_id,
                    "platform": platform,
                    "content_type": content_type,
                    "text_content": post_data["text_content"],
                    "image_prompt": post_data.get("image_prompt"),
                    "video_script": post_data.get("video_script"),
                    "hashtags": post_data.get("hashtags", []),
                    "scheduled_at": scheduled.isoformat(),
                    "status": "pending_approval",
                    "rnd_dossier_id": dossier.id,
                    "rnd_social_calendar_id": item_id,
                },
            )
            posts_created.append(row)
            if primary_post is None:
                primary_post = row

        if not posts_created or not primary_post:
            raise ValueError("Aucun post généré")

        self.social.update_calendar_item(
            item_id,
            {"post_id": primary_post["id"], "status": "generated"},
        )

        self.repo.log_event(
            dossier.id,
            "social_post_generated",
            actor,
            {"calendar_item_id": item_id, "posts": len(posts_created)},
        )

        return {
            "post": primary_post,
            "posts": posts_created,
            "calendar_item_id": item_id,
            "message": f"{len(posts_created)} post(s) en file d'approbation",
        }

    def generate_all_posts(
        self,
        dossier_id: str,
        *,
        actor: str = "rnd_social_agent",
    ) -> dict[str, Any]:
        dossier = self.repo.get_dossier(dossier_id)
        if not dossier:
            raise ValueError("Dossier introuvable")
        assert_social_pipeline_unlocked(dossier)

        calendar = self.social.list_calendar(dossier_id)
        if not calendar:
            cal = self.generate_calendar(dossier_id, actor=actor)
            calendar = [
                RndSocialCalendarItemOut.model_validate(i) for i in cal["calendar"]
            ]

        results: list[dict[str, Any]] = []
        for item in calendar:
            if item.status in ("published", "cancelled"):
                continue
            if item.post_id:
                continue
            try:
                r = self.generate_post_for_item(
                    dossier_id,
                    item.id,
                    actor=actor,
                )
                results.append(r)
            except Exception as exc:
                logger.warning("social generate_all skip %s: %s", item.id, exc)
                results.append({"calendar_item_id": item.id, "error": str(exc)})

        return {
            "generated_count": sum(1 for r in results if r.get("post")),
            "results": results,
            "message": f"{sum(1 for r in results if r.get('post'))} jalons avec posts générés",
        }

    def social_status(self, dossier_id: str) -> dict[str, Any]:
        dossier = self.repo.get_dossier(dossier_id)
        if not dossier:
            raise ValueError("Dossier introuvable")
        unlocked = is_social_pipeline_unlocked(dossier.status, dossier.ceo_status)
        return {
            "unlocked": unlocked,
            "dossier_status": dossier.status,
            "ceo_status": dossier.ceo_status,
            "message": (
                "Pipeline social actif — validation CEO obtenue."
                if unlocked
                else "Verrouillé jusqu'à validation CEO du dossier R&D."
            ),
        }

    def list_posts(self, dossier_id: str) -> list[dict[str, Any]]:
        dossier = self.repo.get_dossier(dossier_id)
        if not dossier:
            raise ValueError("Dossier introuvable")
        return self.social.list_dossier_posts(dossier.id)

    def _generate_post_content(
        self,
        dossier: RndDossierOut,
        item: dict[str, Any],
        *,
        platform: str,
        content_type: str,
    ) -> dict[str, Any]:
        context = _dossier_context(dossier)
        milestone = item.get("milestone", "")
        phase = item.get("phase", "")

        if USE_LLM:
            user = f"""Projet R&D : {dossier.title}
Tagline : {dossier.tagline or '—'}
Domaine : {dossier.domain}

Phase calendrier : {phase}
Jalon : {milestone}
Notes : {item.get('notes') or '—'}

Contexte dossier :
{context}

Plateforme cible : {platform}
Type : {content_type}
Règles plateforme : {PLATFORM_RULES.get(platform, platform)}

Génère exactement 1 post."""
            try:
                raw = self._complete(
                    user,
                    system_prompt=SOCIAL_POST_SYSTEM,
                    agent_id="content",
                    temperature=0.85,
                )
                parsed = parse_json_response(raw)
                text = (parsed.get("text_content") or "").strip()
                if text:
                    return {
                        "text_content": text,
                        "image_prompt": parsed.get("image_prompt"),
                        "video_script": parsed.get("video_script"),
                        "hashtags": parsed.get("hashtags") or [],
                    }
            except Exception as exc:
                logger.warning("rnd_social LLM post failed: %s", exc)

        return _template_post(dossier, item, platform=platform, content_type=content_type)
