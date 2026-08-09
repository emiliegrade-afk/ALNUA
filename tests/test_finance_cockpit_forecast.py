"""Vague C — cockpit forecast + HTTP surface."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

HUB_HEADERS = {"X-Hub-Key": "test-hub-key-for-ci"}


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("HUB_API_KEY", "test-hub-key-for-ci")
    from config.settings import get_settings

    get_settings.cache_clear()
    monkeypatch.setattr("database.supabase_client.get_supabase", lambda: MagicMock())

    from services import finance_budgets, finance_fiscal

    monkeypatch.setattr(finance_budgets, "_PATH", tmp_path / "budgets.json")
    monkeypatch.setattr(finance_fiscal, "_PATH", tmp_path / "fiscal.json")
    monkeypatch.setattr(
        "services.saas_spend.build_saas_spend_report",
        lambda days=30: {"total_tracked_usd": 42.0},
    )

    from api.app import app

    return TestClient(app)


def test_cockpit_forecast_from_ledgers(client: TestClient) -> None:
    client.post(
        "/finances/budgets",
        headers=HUB_HEADERS,
        json={"department": "marketing", "period": "2026-08", "amount": 500},
    )
    bid = client.get("/finances/budgets", headers=HUB_HEADERS).json()["budgets"][0]["id"]
    client.patch(
        f"/finances/budgets/{bid}",
        headers=HUB_HEADERS,
        json={"spent": 100},
    )
    client.post(
        "/finances/fiscal-obligations",
        headers=HUB_HEADERS,
        json={
            "title": "TVA",
            "amount": 200,
            "kind": "tva",
            "status": "upcoming",
            "due_date": "2026-09-15",
        },
    )

    res = client.get(
        "/finances/cockpit-forecast?period=2026-08&horizon_months=3",
        headers=HUB_HEADERS,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["budgets"]["period_allocated"] == 500.0
    assert body["budgets"]["period_spent"] == 100.0
    assert body["fiscal"]["summary"]["open_total"] == 200.0
    assert body["saas"]["monthly_estimate"] == 42.0
    assert len(body["projection"]["monthly_forecast"]) == 3
    assert "Pas de transfert" in body["assumptions_for_llm"] or "DEC-016" in body["assumptions_for_llm"]


def test_build_cockpit_service_unit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from services import finance_budgets, finance_fiscal
    from services.finance_cockpit_forecast import build_cockpit_forecast

    monkeypatch.setattr(finance_budgets, "_PATH", tmp_path / "b.json")
    monkeypatch.setattr(finance_fiscal, "_PATH", tmp_path / "f.json")
    monkeypatch.setattr(
        "services.saas_spend.build_saas_spend_report",
        lambda days=30: {"total_tracked_usd": 10.0},
    )
    finance_budgets.create_budget(department="app", period="2026-08", amount=300)
    out = build_cockpit_forecast(period="2026-08", horizon_months=2)
    assert out["ok"] is True
    assert out["budgets"]["period_allocated"] == 300.0
