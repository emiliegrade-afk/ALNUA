"""CreatorFlow — dedicated Supabase client (separate project from ALNUA Hub)."""

from __future__ import annotations

from functools import lru_cache

from fastapi import HTTPException
from supabase import Client, create_client

from config.settings import get_settings
from database.supabase_client import SupabaseClient

_CF_DB_MSG = (
    "CreatorFlow Supabase non configuré. "
    "Définir CREATORFLOW_SUPABASE_URL et CREATORFLOW_SUPABASE_SERVICE_ROLE_KEY "
    "dans .env Hub, ou activer NEXT_PUBLIC_CF_LOCAL_DATA=1 côté app."
)


def cf_supabase_configured() -> bool:
    cfg = get_settings()
    return bool(cfg.creatorflow_supabase_url.strip() and cfg.creatorflow_supabase_service_role_key.strip())


@lru_cache
def _cached_cf_client(url: str, key: str) -> SupabaseClient:
    client: Client = create_client(url, key)
    return SupabaseClient(client)


def get_cf_supabase() -> SupabaseClient:
    cfg = get_settings()
    url = cfg.creatorflow_supabase_url.strip()
    key = cfg.creatorflow_supabase_service_role_key.strip()
    if not url or not key:
        raise HTTPException(status_code=503, detail=_CF_DB_MSG)
    return _cached_cf_client(url, key)


def get_cf_supabase_or_none() -> SupabaseClient | None:
    if not cf_supabase_configured():
        return None
    cfg = get_settings()
    return _cached_cf_client(cfg.creatorflow_supabase_url.strip(), cfg.creatorflow_supabase_service_role_key.strip())
