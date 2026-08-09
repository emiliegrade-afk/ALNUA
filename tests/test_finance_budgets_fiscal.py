"""Budgets + fiscal obligations — JSON ledger, no auto-pay (Vague 3 / Phase 34)."""

from __future__ import annotations

from pathlib import Path

import pytest

from services import finance_budgets, finance_fiscal


@pytest.fixture(autouse=True)
def _tmp_ledgers(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(finance_budgets, "_PATH", tmp_path / "budgets.json")
    monkeypatch.setattr(finance_fiscal, "_PATH", tmp_path / "fiscal.json")


def test_budget_create_list_summary() -> None:
    row = finance_budgets.create_budget(
        department="marketing",
        period="2026-08",
        amount=500.0,
        label="Ads Q3",
    )
    assert row["id"]
    assert row["department"] == "marketing"
    listed = finance_budgets.list_budgets(department="marketing")
    assert len(listed) == 1
    summary = finance_budgets.budget_summary()
    assert summary["total_allocated"] == 500.0
    assert "transfert" in summary["transfer_policy"].lower() or "Manuel" in summary["transfer_policy"]


def test_budget_rejects_bad_department() -> None:
    with pytest.raises(ValueError):
        finance_budgets.create_budget(department="spaceships", period="2026-08", amount=10)


def test_fiscal_lifecycle_external_pay() -> None:
    row = finance_fiscal.create_obligation(
        title="TVA T2",
        amount=1200.0,
        kind="tva",
        status="due",
    )
    assert row["status"] == "due"
    updated = finance_fiscal.update_obligation(row["id"], status="paid_externally")
    assert updated["status"] == "paid_externally"
    assert updated["paid_at"]
    summary = finance_fiscal.fiscal_summary()
    assert summary["open_count"] == 0
