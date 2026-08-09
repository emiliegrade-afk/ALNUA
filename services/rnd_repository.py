"""Supabase + JSON persistence for R&D ideas and dossiers — façade."""

from __future__ import annotations

from database.supabase_client import SupabaseClient, get_supabase
from services.rnd_repository_assets import RndAssetsMixin
from services.rnd_repository_dossiers import RndDossiersMixin
from services.rnd_repository_helpers import (  # noqa: F401 — re-export for patches
    RND_DOSSIERS_ROOT,
    RND_IDEAS_FILE,
    _db_available,
)
from services.rnd_repository_ideas import RndIdeasMixin
from services.rnd_repository_promote import RndPromoteMixin
from services.rnd_repository_sections import RndSectionsMixin


class RndRepository(
    RndPromoteMixin,
    RndAssetsMixin,
    RndSectionsMixin,
    RndDossiersMixin,
    RndIdeasMixin,
):
    """CRUD for rnd_ideas and rnd_dossiers with JSON fallback."""

    def __init__(self, db: SupabaseClient | None = None) -> None:
        self.db = db or get_supabase()
        self._use_db = _db_available(self.db)


def get_rnd_repository(db: SupabaseClient | None = None) -> RndRepository:
    return RndRepository(db)
