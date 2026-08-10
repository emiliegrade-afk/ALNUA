"""Vague 4 — HTTP surface budgets / fiscal (ratio tests ↔ surface Vague 3)."""

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

    from api.app import app

    return TestClient(app)


def test_budgets_crud_http(client: TestClient) -> None:
    created = client.post(
        "/finances/budgets",
        headers=HUB_HEADERS,
        json={"department": "app", "period": "2026-08", "amount": 100},
    )
    assert created.status_code == 200
    bid = created.json()["id"]

    listed = client.get("/finances/budgets", headers=HUB_HEADERS)
    assert listed.status_code == 200
    body = listed.json()
    assert body["summary"]["count"] >= 1
    assert any(b["id"] == bid for b in body["budgets"])

    patched = client.patch(
        f"/finances/budgets/{bid}",
        headers=HUB_HEADERS,
        json={"spent": 25},
    )
    assert patched.status_code == 200
    assert patched.json()["spent"] == 25.0
    assert patched.json()["spent_manual"] == 25.0


def test_budget_alerts_http(client: TestClient) -> None:
    period = "2026-08"
    client.post(
        "/finances/budgets",
        headers=HUB_HEADERS,
        json={"department": "rnd", "period": period, "amount": 100},
    )
    bid = client.get(f"/finances/budgets?period={period}", headers=HUB_HEADERS).json()["budgets"][0]["id"]
    client.patch(
        f"/finances/budgets/{bid}",
        headers=HUB_HEADERS,
        json={"spent": 90},
    )
    res = client.get(f"/finances/budget-alerts?period={period}", headers=HUB_HEADERS)
    assert res.status_code == 200
    body = res.json()
    assert body["period"] == period
    rnd = next(a for a in body["alerts"] if a["department"] == "rnd")
    assert rnd["severity"] == "warning"
    assert rnd["remaining"] == 10.0


def test_fiscal_obligations_http(client: TestClient) -> None:
    created = client.post(
        "/finances/fiscal-obligations",
        headers=HUB_HEADERS,
        json={"title": "URSSAF test", "amount": 200, "kind": "urssaf", "status": "due"},
    )
    assert created.status_code == 200
    oid = created.json()["id"]

    listed = client.get("/finances/fiscal-obligations", headers=HUB_HEADERS)
    assert listed.status_code == 200
    assert listed.json()["summary"]["open_count"] >= 1

    paid = client.patch(
        f"/finances/fiscal-obligations/{oid}",
        headers=HUB_HEADERS,
        json={"status": "paid_externally"},
    )
    assert paid.status_code == 200
    assert paid.json()["status"] == "paid_externally"
