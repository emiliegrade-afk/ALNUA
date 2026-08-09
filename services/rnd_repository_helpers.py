"""Shared helpers/constants for RndRepository mixins."""
from __future__ import annotations

import logging
import re
import unicodedata
from datetime import datetime
from uuid import UUID

from config.paths import data_dir, get_hub_repo_path
from database.supabase_client import SupabaseClient

logger = logging.getLogger(__name__)

RND_IDEAS_FILE = get_hub_repo_path() / "data" / "rnd_ideas.json"
RND_DOSSIERS_ROOT = data_dir("rnd_dossiers")


def _slugify(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
    return slug or "dossier"


def _is_uuid(value: str) -> bool:
    try:
        UUID(value)
        return True
    except ValueError:
        return False


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def _db_available(db: SupabaseClient | None) -> bool:
    if db is None:
        return False
    try:
        db.select("rnd_ideas", limit=1)
        return True
    except Exception as exc:
        logger.warning("rnd_repository: Supabase rnd_ideas unavailable: %s", exc)
        return False
