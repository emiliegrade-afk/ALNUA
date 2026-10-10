"""
skill_content_robo.py — Build-in-public content for the Robotics pole (all existing/future robots).

Agents: Mira Solberg (content_robo)
Transforms hardware milestones into build-in-public narratives
across LinkedIn, X, YouTube, Instagram, blog.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

PLATFORMS = frozenset({"linkedin", "x", "youtube", "instagram", "blog"})


def fetch_robo_milestones(project: str = "eve") -> dict[str, Any]:
    """Lab tests and robotics builds already stored by the Hub.

    ``last_prototype_image`` stays null: those tables have no image column.
    ``project`` labels the brief; rows are not filtered by slug.
    """
    from datetime import datetime, timezone

    from skills.skill_robo_lab import get_builds_context, get_lab_context

    scanned_at = datetime.now(timezone.utc).isoformat()
    lab = get_lab_context(limit=10)
    builds = get_builds_context(limit=5)
    if not lab.get("ok") and not builds.get("ok"):
        return {
            "ok": False,
            "available": False,
            "project": project,
            "source": "robo_lab",
            "milestones": [],
            "last_prototype_image": None,
            "scanned_at": scanned_at,
            "note": "Bancs et builds robotique illisibles.",
        }

    milestones: list[dict[str, Any]] = []
    for item in lab.get("items") or []:
        milestones.append(
            {
                "kind": "lab",
                "name": item.get("name"),
                "status": item.get("status"),
                "measured_value": item.get("measured_value"),
                "created_at": item.get("created_at"),
            }
        )
    for item in builds.get("items") or []:
        milestones.append(
            {
                "kind": "build",
                "version": item.get("version"),
                "stage": item.get("stage"),
                "firmware_version": item.get("firmware_version"),
                "tests_passed_pct": item.get("tests_passed_pct"),
            }
        )
    return {
        "ok": True,
        "available": True,
        "empty": not milestones,
        "project": project,
        "source": "robo_lab",
        "milestones": milestones,
        "last_prototype_image": None,
        "scanned_at": scanned_at,
        "note": (
            "Aucun essai ni build enregistré. Pas de photo prototype dans ces tables."
            if not milestones
            else "Essais et builds lus. Pas de photo prototype dans ces tables."
        ),
    }


def gen_build_in_public_post(
    milestone: str,
    challenge: str = "",
    media_url: str = "",
    platforms: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Create build-in-public posts from a hardware milestone."""
    target = [p for p in (platforms or []) if p in PLATFORMS] or ["linkedin", "x"]
    posts: list[dict[str, Any]] = []
    for plat in target:
        body = f"🛠️ {milestone}"
        if challenge:
            body += f"\n\nDéfi du jour : {challenge}"
        posts.append({
            "platform": plat,
            "content_type": "build_in_public",
            "text": body,
            "media_url": media_url,
            "hashtags": ["#BuildInPublic", "#Robotics", "#EveRobot", "#ALNUA"],
        })
    return posts


def build_robo_story_arc(project: str = "eve") -> dict[str, Any]:
    """Define the narrative arc for a robotics project (build-in-public)."""
    return {
        "project": project,
        "arc": [
            {"chapter": 1, "title": "The Why", "content": "Pourquoi ce robot existe"},
            {"chapter": 2, "title": "First Spark", "content": "Premier allumage, premières erreurs"},
            {"chapter": 3, "title": "Iterate", "content": "Itérations, capteurs, premiers mouvements"},
            {"chapter": 4, "title": "Personality", "content": "Le robot prend vie — comportements, voix"},
            {"chapter": 5, "title": "Reveal", "content": "Présentation publique, specs, disponibilité"},
        ],
    }