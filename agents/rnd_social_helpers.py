"""R&D social agent — project linking, templates, and date helpers."""

from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any

from services.rnd_schemas import RndDossierOut

logger = logging.getLogger(__name__)

USE_LLM = os.getenv("RND_DOSSIER_USE_LLM", "true").lower() not in ("0", "false", "no")


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


def resolve_project_for_dossier(dossier: RndDossierOut, db) -> str:
    """Deprecated alias — use ensure_project_for_dossier."""
    return ensure_project_for_dossier(dossier, db)


def _normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def _section_excerpt(dossier: RndDossierOut, key: str, max_len: int = 220) -> str:
    for sec in dossier.sections:
        if sec.section_key != key:
            continue
        md = (sec.content_md or "").strip()
        if len(md) < 20 or md.startswith("_"):
            continue
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
