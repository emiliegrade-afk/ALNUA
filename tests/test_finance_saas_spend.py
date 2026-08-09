"""Tests saas spend + invoices + gmail status wiring."""

from __future__ import annotations

from pathlib import Path


def test_saas_catalog_loads() -> None:
    from services.saas_spend import catalog_for_agents, load_saas_catalog

    cat = load_saas_catalog()
    assert any(t.get("id") == "openrouter" for t in cat.get("tools") or [])
    brief = catalog_for_agents()
    assert "OpenRouter" in brief
    assert "Cursor" in brief


def test_saas_spend_report_includes_live_openrouter() -> None:
    from services.saas_spend import build_saas_spend_report

    report = build_saas_spend_report(days=30)
    ids = {s["id"] for s in report["sources"]}
    assert "openrouter" in ids
    assert "catalog_recurring" in ids
    assert "revolut" in ids
    assert "gmail_ops" in report
    assert report["gmail_ops"].get("expected") == "alnua.global@gmail.com"


def test_invoices_lifecycle() -> None:
    from services.finance_invoices import (
        create_invoice,
        invoice_summary,
        list_invoices,
        update_invoice,
    )

    row = create_invoice(
        vendor="Test Vendor SaaS",
        amount=12.5,
        description="test invoice",
        status="received",
    )
    assert row["id"]
    assert row["status"] == "received"
    updated = update_invoice(row["id"], status="to_pay")
    assert updated["status"] == "to_pay"
    paid = update_invoice(row["id"], status="paid_externally")
    assert paid["status"] == "paid_externally"
    assert paid.get("paid_at")
    listed = list_invoices(vendor="Test Vendor")
    assert any(r["id"] == row["id"] for r in listed)
    summary = invoice_summary()
    assert summary["count"] >= 1
    assert "payment_policy" in summary


def test_revolut_unconfigured_is_explicit() -> None:
    from services.revolut_business import fetch_expenses_summary, is_configured

    # Without token in env (default), must not pretend to work
    if not is_configured():
        out = fetch_expenses_summary(days=7)
        assert out["configured"] is False
        assert "REVOLUT_ACCESS_TOKEN" in out.get("reason", "")


def test_catalogue_doc_exists_for_accounting() -> None:
    path = Path("docs/CATALOGUE_ABONNEMENTS_ALNUA.md")
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "OpenRouter" in text
    assert "Supabase" in text
