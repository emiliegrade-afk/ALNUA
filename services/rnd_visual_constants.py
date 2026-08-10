"""Constants for R&D dossier visual asset generation."""

from __future__ import annotations

from typing import Any

# ALNUA-inspired palette by branch
BRANCH_PALETTES: dict[str, dict[str, tuple[int, int, int]]] = {
    "app": {
        "bg": (18, 18, 22),
        "accent": (201, 149, 108),
        "text": (235, 232, 225),
        "muted": (140, 136, 128),
        "card": (32, 32, 38),
    },
    "gaming": {
        "bg": (14, 12, 28),
        "accent": (167, 139, 250),
        "text": (235, 232, 245),
        "muted": (130, 125, 150),
        "card": (28, 24, 48),
    },
    "robotics": {
        "bg": (12, 20, 24),
        "accent": (56, 189, 168),
        "text": (230, 240, 238),
        "muted": (120, 140, 135),
        "card": (20, 32, 36),
    },
    "hub": {
        "bg": (16, 14, 12),
        "accent": (212, 165, 116),
        "text": (240, 236, 228),
        "muted": (150, 145, 135),
        "card": (28, 26, 22),
    },
    "other": {
        "bg": (18, 18, 22),
        "accent": (201, 149, 108),
        "text": (235, 232, 225),
        "muted": (140, 136, 128),
        "card": (32, 32, 38),
    },
}

ASSET_SPECS: list[dict[str, Any]] = [
    {
        "asset_type": "hero",
        "filename": "hero.png",
        "size": (1920, 1080),
        "section_key": "solution",
        "label": "Hero — couverture dossier",
    },
    {
        "asset_type": "social_teaser",
        "filename": "social_teaser.png",
        "size": (1080, 1080),
        "section_key": "solution",
        "label": "Teaser réseaux sociaux",
    },
    {
        "asset_type": "mockup",
        "filename": "mockup.png",
        "size": (1280, 800),
        "section_key": "mvp",
        "label": "Mockup produit",
    },
    {
        "asset_type": "diagram",
        "filename": "diagram.png",
        "size": (1200, 720),
        "section_key": "mvp",
        "label": "Schéma MVP",
    },
    {
        "asset_type": "moodboard",
        "filename": "moodboard.png",
        "size": (1400, 900),
        "section_key": "visual_identity",
        "label": "Moodboard identité",
    },
    {
        "asset_type": "chart",
        "filename": "finance_chart.png",
        "size": (1200, 680),
        "section_key": "business_case",
        "label": "Synthèse finance",
        "requires_finance": True,
    },
]
