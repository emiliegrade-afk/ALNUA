"""Local filesystem layout for brand kits."""

from __future__ import annotations

from pathlib import Path

from agents.brainstorm_agent import BrainstormAgent
from database.supabase_client import get_supabase

BRAND_KITS_ROOT = Path(__file__).resolve().parent.parent / "brand_kits"


def ensure_brand_kit_dirs() -> None:
    """Create uploads/ and one folder per Supabase project slug."""
    (BRAND_KITS_ROOT / "uploads").mkdir(parents=True, exist_ok=True)
    db = get_supabase()
    for project in db.select("projects", order_by="name"):
        slug = BrainstormAgent.project_folder_slug(project["name"], project["id"])
        (BRAND_KITS_ROOT / slug).mkdir(parents=True, exist_ok=True)
