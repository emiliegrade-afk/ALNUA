"""Tenant-scoped Supabase helpers — inject tenant_id on all reads/writes."""

from __future__ import annotations

from contextvars import ContextVar
from typing import Any

from models.tenant import DEFAULT_TENANT_ID, tenant_filter, with_tenant

_current_tenant: ContextVar[str] = ContextVar("tenant_id", default=DEFAULT_TENANT_ID)

# Tables that support tenant_id column (post-migration)
TENANT_SCOPED_TABLES: frozenset[str] = frozenset({
    "projects",
    "tickets",
    "agent_logs",
    "beta_testers",
    "beta_feedback",
    "daily_briefings",
    "composio_connections",
    "brand_kits",
    "agent_feedback",
    "tenant_personality",
})


def get_current_tenant_id() -> str:
    return _current_tenant.get()


def set_current_tenant_id(tenant_id: str) -> None:
    _current_tenant.set(tenant_id)


def scope_filters(table: str, filters: dict[str, Any] | None) -> dict[str, Any] | None:
    """Auto-inject tenant_id filter for scoped tables."""
    if table not in TENANT_SCOPED_TABLES:
        return filters
    return tenant_filter(filters, get_current_tenant_id())


def scope_row(table: str, row: dict[str, Any]) -> dict[str, Any]:
    """Auto-inject tenant_id on insert for scoped tables."""
    if table not in TENANT_SCOPED_TABLES:
        return row
    if "tenant_id" in row:
        return row
    return with_tenant(row, get_current_tenant_id())
