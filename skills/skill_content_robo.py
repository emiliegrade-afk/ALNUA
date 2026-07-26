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
    """Stub — live milestone scan from hardware tracker."""
    return {
        "project": project,
        "milestones": [],
        "last_prototype_image": None,
        "scanned_at": "",
        "note": "live hardware tracker integration pending",
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