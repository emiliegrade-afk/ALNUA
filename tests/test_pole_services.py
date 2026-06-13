"""Tests for pole API endpoints and supporting services."""

from __future__ import annotations

import pytest

from services.eve_bom import BOM_CATEGORIES, BOM_STATUSES, bom_totals


def test_bom_categories_defined():
    assert "compute" in BOM_CATEGORIES
    assert "vision" in BOM_CATEGORIES


def test_bom_totals_empty():
    result = bom_totals([])
    assert result["count"] == 0
    assert result["total_eur"] == 0.0


def test_bom_totals_sums():
    items = [
        {"quantity": 2, "unit_price": 10.0, "category": "vision"},
        {"quantity": 1, "unit_price": 5.0, "category": "audio"},
    ]
    result = bom_totals(items)
    assert result["total_eur"] == 25.0
    assert result["count"] == 2
    assert result["by_category"]["vision"] == 20.0


def test_bom_statuses():
    assert "a_commander" in BOM_STATUSES
    assert "livre" in BOM_STATUSES


def test_brand_agent_import():
    from agents.brand_agent import BrandAgent

    agent = BrandAgent()
    assert agent.AGENT_NAME == "brand"


def test_reviews_bot_store_ids(monkeypatch):
    from bots.reviews_bot import _store_ids_for_project

    monkeypatch.setenv("APP_STORE_ID_NAIA", "123456")
    monkeypatch.setenv("GOOGLE_PLAY_PACKAGE_NAIA", "com.alnua.naia")
    app_id, pkg = _store_ids_for_project({"name": "Naïa App", "slug": "naia"})
    assert app_id == "123456"
    assert pkg == "com.alnua.naia"


def test_skill_synthesizer_should_not_one_shot():
    from agents.skill_synthesizer import _should_synthesize

    assert _should_synthesize("supprime le fichier config") is False
    assert _should_synthesize("chaque matin génère un rapport") is True
