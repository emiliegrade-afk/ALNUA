"""R&D Dossier Hub — string literals and lookup tables."""

from __future__ import annotations

from typing import Any, Literal

LifecycleStatus = Literal[
    "raw", "dossier_draft", "in_committee", "sections_review",
    "ceo_review", "approved", "rejected", "in_conception", "shipped", "archived",
]

DossierStatus = Literal[
    "draft", "committee_active", "partial_validated", "ready_for_ceo",
    "ceo_approved", "ceo_rejected", "in_conception", "published", "archived",
]

CeoStatus = Literal["pending", "approved", "rejected", "pivot_requested"]

SectionStatus = Literal["draft", "under_review", "validated", "needs_revision", "skipped"]

SectionKey = Literal[
    "problem", "solution", "market", "mvp", "feasibility", "business_case",
    "manufacturing", "lore", "visual_identity", "social_strategy", "risks", "decision",
]

Branch = Literal["app", "gaming", "robotics", "hub", "other"]

IncubatorStage = Literal["idee", "prototype", "validation", "mvp", "projet", "departement"]

SocialPhase = Literal[
    "internal", "behind_scenes", "teaser", "pre_launch", "launch", "post_launch",
]

SocialCalendarStatus = Literal[
    "planned", "generated", "approved", "published", "cancelled",
]

CouncilSessionKind = Literal["strategic", "evaluation"]

SECTION_DEFINITIONS: dict[str, dict[str, Any]] = {
    "problem": {"title": "Problème & opportunité", "sort_order": 10},
    "solution": {"title": "Solution produit", "sort_order": 20},
    "market": {"title": "Marché & concurrence", "sort_order": 30},
    "mvp": {"title": "MVP & roadmap", "sort_order": 40},
    "feasibility": {"title": "Faisabilité technique", "sort_order": 50},
    "business_case": {"title": "Business case & coûts", "sort_order": 60},
    "manufacturing": {"title": "Fabrication & BOM", "sort_order": 70},
    "lore": {"title": "Univers & narration", "sort_order": 75},
    "visual_identity": {"title": "Identité visuelle", "sort_order": 80},
    "social_strategy": {"title": "Stratégie réseaux sociaux", "sort_order": 90},
    "risks": {"title": "Risques & mitigations", "sort_order": 100},
    "decision": {"title": "Recommandation & décision", "sort_order": 110},
}

DOMAIN_TO_BRANCH: dict[str, str] = {
    "app": "app",
    "saas": "app",
    "ia": "app",
    "jeu": "gaming",
    "game": "gaming",
    "gaming": "gaming",
    "hardware": "robotics",
    "robotique": "robotics",
    "robotics": "robotics",
    "hub": "hub",
    "plateforme": "hub",
    "platform": "hub",
    "infra": "hub",
    "interne": "hub",
    "alnua hub": "hub",
    "company os": "hub",
}
