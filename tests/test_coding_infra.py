"""Tests for coding error journal + academy sync."""

from __future__ import annotations

from pathlib import Path

from services.coding_error_journal import (
    build_lessons_block,
    count_resolved,
    record_coding_error,
    resolve_matching_errors,
)
from services.nuaway_gate import _lounge_product_ready


def test_record_and_resolve_coding_error(tmp_path: Path, monkeypatch) -> None:
    journal_path = tmp_path / "coding_errors.json"
    monkeypatch.setenv("CODING_ERRORS_PATH", str(journal_path))

    record_coding_error(
        agent_name="dev_app",
        task_id="GH-9",
        repo_slug="academy",
        error_type="QAError",
        error_message="Fichier vide : app/login.tsx",
        qa_errors=["Fichier vide : app/login.tsx"],
    )
    assert count_resolved() == 0

    n = resolve_matching_errors("GH-9", None, "PR merged OK")
    assert n == 1
    assert count_resolved() == 1

    block = build_lessons_block()
    assert block


def test_lounge_product_gate_flag() -> None:
    assert _lounge_product_ready() is True
