import logging
from functools import lru_cache
from typing import Any

from supabase import Client, create_client

from config.settings import get_settings

logger = logging.getLogger(__name__)
_service_role_warned = False


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
        query = self.table(table).select(columns)
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        if is_null:
            for column in is_null:
                query = query.is_(column, "null")
        if order_by:
            query = query.order(order_by, desc=not ascending)
        if limit is not None:
            query = query.limit(limit)
        response = query.execute()
        return response.data or []

    def insert(self, table: str, row: dict[str, Any]) -> dict[str, Any]:
        response = self.table(table).insert(row).execute()
        if not response.data:
            raise RuntimeError(f"Insert into {table} returned no data")
        return response.data[0]

    def insert_many(self, table: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not rows:
            return []
        response = self.table(table).insert(rows).execute()
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
        response = (
            self.table(table)
            .update(values)
            .eq(id_column, row_id)
            .execute()
        )
        if not response.data:
            raise RuntimeError(f"Update on {table} id={row_id} returned no data")
        return response.data[0]

    def delete(self, table: str, row_id: str, id_column: str = "id") -> None:
        self.table(table).delete().eq(id_column, row_id).execute()


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
