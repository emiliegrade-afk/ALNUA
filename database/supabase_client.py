import logging
from functools import lru_cache
from typing import Any

import httpx
from supabase import Client, create_client

from config.settings import get_settings
from database.tenant_scope import scope_filters, scope_row

logger = logging.getLogger(__name__)
_service_role_warned = False


def _execute_with_retry(build_query: Any, *, retries: int = 1) -> Any:
    """Execute a fresh query, retrying once on a dropped HTTP/2 connection.

    `get_supabase()` is process-lifetime cached (`lru_cache`), so its
    underlying httpx connection pool can hold a connection Supabase closed
    server-side after being idle — httpx only discovers this when it tries
    to reuse it, raising `httpx.RemoteProtocolError: Server disconnected`.
    Seen intermittently across /projects, /tickets, /modules, /posts,
    /brand/kits (found during Phase 14 QA, 2026-07-30). `build_query` must
    construct the query builder from scratch each call — a builder object
    is single-use, so retrying `.execute()` on the same instance doesn't work.
    """
    attempt = 0
    while True:
        try:
            return build_query().execute()
        except httpx.RemoteProtocolError:
            attempt += 1
            if attempt > retries:
                raise


class SupabaseClient:
    """Wrapper around the Supabase Python client for typed table access."""

    def __init__(self, client: Client) -> None:
        self._client = client

    @property
    def raw(self) -> Client:
        return self._client

    def table(self, name: str) -> Any:
        return self._client.table(name)

    def select(
        self,
        table: str,
        columns: str = "*",
        filters: dict[str, Any] | None = None,
        is_null: list[str] | None = None,
        order_by: str | None = None,
        ascending: bool = True,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        def _build() -> Any:
            query = self.table(table).select(columns)
            scoped = scope_filters(table, filters)
            if scoped:
                for key, value in scoped.items():
                    query = query.eq(key, value)
            if is_null:
                for column in is_null:
                    query = query.is_(column, "null")
            if order_by:
                query = query.order(order_by, desc=not ascending)
            if limit is not None:
                query = query.limit(limit)
            return query

        response = _execute_with_retry(_build)
        return response.data or []

    def insert(self, table: str, row: dict[str, Any]) -> dict[str, Any]:
        scoped_row = scope_row(table, row)
        response = _execute_with_retry(lambda: self.table(table).insert(scoped_row))
        if not response.data:
            raise RuntimeError(f"Insert into {table} returned no data")
        return response.data[0]

    def insert_many(self, table: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not rows:
            return []
        scoped_rows = [scope_row(table, r) for r in rows]
        response = _execute_with_retry(lambda: self.table(table).insert(scoped_rows))
        if not response.data:
            raise RuntimeError(f"Insert into {table} returned no data")
        return response.data

    def update(
        self,
        table: str,
        row_id: str,
        values: dict[str, Any],
        id_column: str = "id",
    ) -> dict[str, Any]:
        response = _execute_with_retry(
            lambda: self.table(table).update(values).eq(id_column, row_id)
        )
        if not response.data:
            raise RuntimeError(f"Update on {table} id={row_id} returned no data")
        return response.data[0]

    def delete(self, table: str, row_id: str, id_column: str = "id") -> None:
        _execute_with_retry(lambda: self.table(table).delete().eq(id_column, row_id))


@lru_cache
def get_supabase() -> SupabaseClient:
    global _service_role_warned
    cfg = get_settings()
    # Backend writes (BOM, etc.) need service_role — anon key is read-only on several tables.
    if not cfg.supabase_service_role_key.strip():
        if not _service_role_warned:
            logger.warning(
                "SUPABASE_SERVICE_ROLE_KEY unset — using anon key; writes may fail under RLS"
            )
            _service_role_warned = True
        key = cfg.supabase_key
    else:
        key = cfg.supabase_service_role_key.strip()
    client = create_client(cfg.supabase_url, key)
    return SupabaseClient(client)
