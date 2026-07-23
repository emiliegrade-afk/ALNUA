"""Tests for tenant-scoped Supabase helpers."""

from __future__ import annotations

from database.tenant_scope import (
    TENANT_SCOPED_TABLES,
    get_current_tenant_id,
    scope_filters,
    scope_row,
    set_current_tenant_id,
)


def test_agent_logs_scoped_on_insert() -> None:
    set_current_tenant_id("tenant_a")
    row = scope_row("agent_logs", {"agent_name": "coo", "action": "test"})
    assert row["tenant_id"] == "tenant_a"


def test_projects_filter_injected() -> None:
    set_current_tenant_id("tenant_b")
    f = scope_filters("projects", {"status": "active"})
    assert f == {"status": "active", "tenant_id": "tenant_b"}


def test_non_scoped_table_unchanged() -> None:
    set_current_tenant_id("tenant_c")
    assert scope_filters("rnd_ideas", {"status": "raw"}) == {"status": "raw"}
    row = scope_row("rnd_ideas", {"title": "Test"})
    assert "tenant_id" not in row


def test_agent_feedback_in_scoped_tables() -> None:
    assert "agent_feedback" in TENANT_SCOPED_TABLES


def test_context_var_roundtrip() -> None:
    set_current_tenant_id("acme")
    assert get_current_tenant_id() == "acme"
