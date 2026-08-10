"""Budgets + fiscal obligations — JSON ledger, no auto-pay (Vague 3 / Phase 34)."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from services import finance_budgets, finance_fiscal
from services.finance_budget_spent import (
    enrich_budget_row,
    period_date_bounds,
    resolve_tx_department,
    severity_for_utilization,
    tx_in_period,
)


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
    assert row["spent_manual"] == 0.0
    listed = finance_budgets.list_budgets(department="marketing")
    assert len(listed) == 1
    assert "remaining" in listed[0]
    summary = finance_budgets.budget_summary()
    assert summary["total_allocated"] == 500.0
    assert "transfert" in summary["transfer_policy"].lower() or "Manuel" in summary["transfer_policy"]


def test_budget_rejects_bad_department() -> None:
    with pytest.raises(ValueError):
        finance_budgets.create_budget(department="spaceships", period="2026-08", amount=10)


def test_budget_alerts_warning_and_critical() -> None:
    period = date.today().strftime("%Y-%m")
    finance_budgets.create_budget(department="marketing", period=period, amount=100.0)
    finance_budgets.create_budget(department="app", period=period, amount=100.0)
    bid = finance_budgets.list_budgets(department="marketing")[0]["id"]
    finance_budgets.update_budget(bid, spent=85.0)
    bid2 = finance_budgets.list_budgets(department="app")[0]["id"]
    finance_budgets.update_budget(bid2, spent=110.0)

    out = finance_budgets.budget_alerts(period=period)
    by_dept = {a["department"]: a for a in out["alerts"]}
    assert by_dept["marketing"]["severity"] == "warning"
    assert by_dept["marketing"]["remaining"] == 15.0
    assert by_dept["app"]["severity"] == "critical"
    assert out["critical_count"] == 1
    assert out["warning_count"] == 1


def test_spent_heuristics_branch_and_category() -> None:
    assert resolve_tx_department({"project_id": "p1", "category": "autre"}, {"p1": "robotics"}) == "robo"
    assert resolve_tx_department({"project_id": None, "category": "marketing"}, {}) == "marketing"
    assert tx_in_period("2026-08-15", "2026-08")
    assert not tx_in_period("2026-07-31", "2026-08")
    start, end = period_date_bounds("2026-Q3")
    assert start == date(2026, 7, 1)
    assert end == date(2026, 9, 30)


def test_enrich_prefers_computed_when_available() -> None:
    row = {"department": "marketing", "period": "2026-08", "amount": 200.0, "spent": 10.0}
    computed = {("marketing", "2026-08"): 50.0}
    enriched = enrich_budget_row(row, computed)
    assert enriched["spent_manual"] == 10.0
    assert enriched["spent_computed"] == 50.0
    assert enriched["spent"] == 50.0
    assert enriched["utilization_pct"] == 25.0


def test_severity_thresholds() -> None:
    assert severity_for_utilization(50) == "ok"
    assert severity_for_utilization(80) == "warning"
    assert severity_for_utilization(100) == "critical"


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


def test_fiscal_promotes_upcoming_to_due(monkeypatch: pytest.MonkeyPatch) -> None:
    past = (date.today() - timedelta(days=3)).isoformat()
    row = finance_fiscal.create_obligation(
        title="URSSAF passé",
        amount=400.0,
        kind="urssaf",
        status="upcoming",
        due_date=past,
    )
    assert row["status"] == "upcoming"
    listed = finance_fiscal.list_obligations()
    match = next(r for r in listed if r["id"] == row["id"])
    assert match["status"] == "due"
    summary = finance_fiscal.fiscal_summary()
    assert summary["open_count"] >= 1
    assert summary["next_due"] == past


def test_fiscal_get_obligation_promotes() -> None:
    past = (date.today() - timedelta(days=1)).isoformat()
    row = finance_fiscal.create_obligation(
        title="CFE",
        amount=100.0,
        kind="cfe",
        status="upcoming",
        due_date=past,
    )
    got = finance_fiscal.get_obligation(row["id"])
    assert got["status"] == "due"


def test_computed_spent_from_mock_supabase(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.finance_budget_spent import computed_spent_by_dept_period

    db = MagicMock()
    db.select.side_effect = lambda table: (
        [
            {
                "id": "t1",
                "date": "2026-08-10",
                "type": "expense",
                "amount": 30.0,
                "category": "marketing",
                "project_id": None,
            }
        ]
        if table == "transactions"
        else []
    )
    monkeypatch.setattr("database.supabase_client.get_supabase", lambda: db)
    totals = computed_spent_by_dept_period(period="2026-08")
    assert totals is not None
    assert totals.get(("marketing", "2026-08")) == 30.0
