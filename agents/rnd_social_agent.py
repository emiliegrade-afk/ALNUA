"""
rnd_social_agent.py — Social teaser pipeline for R&D dossiers (phase 5).

Calendar → posts_queue with rnd_dossier_id / rnd_social_calendar_id links.
"""

from __future__ import annotations

from agents.agent_base import AgentBase

import logging
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any

from agents.base import parse_json_response
from agents.content_agent import PLATFORM_RULES, VALID_CONTENT_TYPES, VALID_PLATFORMS
from agents.rnd_social_prompts import SOCIAL_POST_SYSTEM, SOCIAL_STRATEGY_SYSTEM
from services.rnd_repository import get_rnd_repository
from services.rnd_schemas import RndDossierOut, RndSocialCalendarItemOut
from services.rnd_social import (
    assert_social_pipeline_unlocked,
    build_template_calendar,
    default_launch_anchor,
    get_rnd_social_repository,
    is_social_pipeline_unlocked,
)

logger = logging.getLogger(__name__)

USE_LLM = os.getenv("RND_DOSSIER_USE_LLM", "true").lower() not in ("0", "false", "no")


class RndSocialAgent(AgentBase):
    AGENT_NAME = "rnd_social_agent"

    def __init__(self) -> None:
        super().__init__()
        self.repo = get_rnd_repository()
        self.social = get_rnd_social_repository()

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

    def list_calendar(self, dossier_id: str) -> list[dict[str, Any]]:
        dossier = self.repo.get_dossier(dossier_id)
        if not dossier:
            raise ValueError("Dossier introuvable")
        items = [i.model_dump() for i in self.social.list_calendar(dossier.id)]
        return items

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
        updated = self.social.update_calendar_item(item_id, payload)
        return updated

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


def ensure_project_for_dossier(dossier: RndDossierOut, db) -> str:
    """
    Link dossier → dedicated Hub project (never Naïa/Eve by fallback).
    Creates project row named after the dossier if missing.
    """
    if dossier.project_id:
        return dossier.project_id

    rows = db.select("rnd_dossiers", filters={"id": dossier.id}, limit=1)
    if rows and rows[0].get("project_id"):
        return str(rows[0]["project_id"])

    slug_n = _normalize_name(dossier.slug)
    title_n = _normalize_name(dossier.title)

    for p in db.select("projects", order_by="name", ascending=True, limit=200):
        pn = _normalize_name(p.get("name", ""))
        if pn == slug_n or pn == title_n:
            db.update("rnd_dossiers", dossier.id, {"project_id": p["id"]})
            return str(p["id"])

    branch = dossier.branch or "other"
    if branch not in ("app", "gaming", "robotics", "hub"):
        branch = "other"

    created = db.insert(
        "projects",
        {
            "name": dossier.title,
            "branch": branch,
            "description": (dossier.tagline or f"Produit R&D — {dossier.title}")[:500],
            "status": "dev",
        },
    )
    project_id = str(created["id"] if isinstance(created, dict) else created[0]["id"])
    db.update("rnd_dossiers", dossier.id, {"project_id": project_id})
    logger.info("rnd_social: created project %s for dossier %s", project_id, dossier.slug)
    return project_id


def _normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def _section_excerpt(dossier: RndDossierOut, key: str, max_len: int = 220) -> str:
    for sec in dossier.sections:
        if sec.section_key != key:
            continue
        md = (sec.content_md or "").strip()
        if len(md) < 20 or md.startswith("_"):
            continue
        # First substantive line (skip markdown headers)
        for line in md.splitlines():
            t = re.sub(r"^#+\s*", "", line).strip()
            if len(t) > 30 and not t.startswith("_"):
                return t[:max_len]
        return md[:max_len]
    return ""


def _extract_product_pitch(dossier: RndDossierOut) -> dict[str, str]:
    problem = _section_excerpt(dossier, "problem", 200)
    solution = _section_excerpt(dossier, "solution", 200)
    tagline = (dossier.tagline or "").strip()
    title = dossier.title

    value = solution or tagline or problem or title
    if "proposition" in value.lower() and len(solution) > 40:
        value = solution

    return {
        "title": title,
        "tagline": tagline,
        "problem": problem,
        "solution": solution,
        "value": value,
    }


def _template_post(
    dossier: RndDossierOut,
    item: dict[str, Any],
    *,
    platform: str,
    content_type: str,
) -> dict[str, Any]:
    pitch = _extract_product_pitch(dossier)
    title = pitch["title"]
    phase = item.get("phase", "teaser")

    problem = pitch["problem"] or "Tu passes plus de temps à gérer tes posts qu'à créer ?"
    tagline = pitch["tagline"] or pitch["value"]
    solution = pitch["solution"] or tagline

    if phase == "behind_scenes":
        text = (
            f"{problem}\n\n"
            "On prépare quelque chose pour ça. Tu veux être prévenu(e) en premier ? 👇"
        )
    elif phase == "teaser":
        text = f"{tagline}\n\nBientôt plus de détails sur {title}."
    elif phase == "pre_launch":
        text = (
            f"{title} arrive bientôt.\n\n"
            f"{solution[:140]}\n\n"
            "Liste d'attente bientôt ouverte — commente « intéressé » si tu veux un accès early."
        )
    elif phase == "launch":
        text = (
            f"🚀 {title} est disponible (beta).\n\n"
            f"{tagline}\n\n"
            "Lien en bio — dis-moi ce que tu en penses."
        )
    elif phase == "post_launch":
        text = (
            f"Comment démarrer avec {title} en 3 étapes :\n"
            f"1) {solution[:80]}\n"
            "2) Configure ton profil\n"
            "3) Publie ton premier contenu\n\n"
            "Des questions ? Réponds à ce post."
        )
    else:
        text = f"{tagline} — {title}"

    text = re.sub(r"\s+", " ", text).strip()
    if platform == "x":
        # Single punchy tweet from tagline + hook
        if phase == "teaser":
            text = f"{tagline[:180]} — {title} arrive bientôt."
        text = text[:280]

    slug_tag = re.sub(r"[^a-zA-Z0-9]", "", title)
    domain_tags: list[str] = []
    dom = (dossier.domain or "").lower()
    if dom in ("saas", "app", "ia"):
        domain_tags = ["creators", "contentcreation", "productivity"]
    elif dom in ("jeu", "game", "gaming"):
        domain_tags = ["indiegame", "gaming"]
    else:
        domain_tags = ["startup"]

    hashtags = [f"#{slug_tag}"] + [f"#{t}" for t in domain_tags[:3]]

    return {
        "text_content": text,
        "image_prompt": f"Social promo card for {title}, product benefit focused, modern SaaS aesthetic",
        "video_script": None,
        "hashtags": hashtags[:6],
    }


def resolve_project_for_dossier(dossier: RndDossierOut, db) -> str:
    """Deprecated alias — use ensure_project_for_dossier."""
    return ensure_project_for_dossier(dossier, db)


def _dossier_context(dossier: RndDossierOut, max_chars: int = 2500) -> str:
    parts: list[str] = []
    for sec in dossier.sections:
        md = (sec.content_md or "").strip()
        if len(md) < 25 or md.startswith("_"):
            continue
        parts.append(f"### {sec.title}\n{md[:600]}")
    text = "\n\n".join(parts)
    if dossier.finance_json:
        rev = dossier.finance_json.get("revenue_hypothesis", {})
        pm = rev.get("pricing_model", {})
        if pm.get("blended_arpu_eur"):
            text += f"\n\nPricing indicatif : {pm.get('blended_arpu_eur')} € ARPU"
    return text[:max_chars] or dossier.tagline or dossier.title


def _template_for_milestone(milestone: str, phase: str) -> dict[str, Any]:
    from services.rnd_social import SOCIAL_PHASE_TEMPLATES

    for tpl in SOCIAL_PHASE_TEMPLATES:
        if tpl["milestone"] == milestone:
            return tpl
    for tpl in SOCIAL_PHASE_TEMPLATES:
        if tpl["phase"] == phase:
            return tpl
    return SOCIAL_PHASE_TEMPLATES[2]


def _parse_launch_date(value: str) -> datetime:
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError as exc:
        raise ValueError(f"Date launch invalide : {value}") from exc


def _parse_planned_at(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc) + timedelta(days=1)
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return datetime.now(timezone.utc) + timedelta(days=1)
