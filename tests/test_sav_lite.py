"""Tests SAV lite — product KB + Nadia triage."""

from __future__ import annotations

from unittest.mock import MagicMock, patch



def test_sensitive_pattern_forces_ceo() -> None:
    from services.sav_lite import _classify_and_draft

    with (
        patch("agents.base.LLMClient") as mock_llm_cls,
        patch("agents.base.parse_json_response") as parse,
    ):
        parse.return_value = {
            "category": "howto",
            "draft_reply": "Voici la procédure.",
            "confidence": 0.9,
            "needs_ceo": False,
        }
        result = _classify_and_draft(
            product_slug="hub",
            subject="Remboursement demandé",
            body="Je veux un refund immédiat",
            kb_context="FAQ",
        )
    assert result["needs_ceo"] is True


def test_process_sav_case_needs_ceo_when_low_confidence() -> None:
    from services.sav_lite import SavCaseIn, process_sav_case

    kb = MagicMock()
    kb.auto_reply_ok = True

    with (
        patch("services.sav_lite.ensure_kb", return_value=kb),
        patch("services.sav_lite.build_kb_context", return_value="ctx"),
        patch("services.sav_lite._classify_and_draft") as classify,
        patch("services.sav_lite._get_db") as get_db,
        patch("skills.skill_telegram_notify.notify_telegram"),
    ):
        classify.return_value = {
            "category": "howto",
            "draft_reply": "Réponse",
            "confidence": 0.5,
            "needs_ceo": False,
        }
        db = MagicMock()
        get_db.return_value = db
        db.insert.return_value = {"id": "case-1"}

        out = process_sav_case(
            SavCaseIn(product_slug="nomad", subject="Help", body="Comment faire ?")
        )

    assert out["success"] is True
    assert out["needs_ceo"] is True
    assert out["status"] == "awaiting_ceo"
    row = db.insert.call_args[0][1]
    assert row["needs_ceo"] is True


def test_approve_and_close_updates_status() -> None:
    from services.sav_lite import approve_and_close

    db = MagicMock()
    db.select.return_value = [
        {
            "id": "c1",
            "product_slug": "nomad",
            "subject": "Bug",
            "draft_reply": "Merci pour le signalement.",
        }
    ]

    with (
        patch("services.sav_lite._get_db", return_value=db),
        patch("skills.skill_mem0.remember"),
    ):
        out = approve_and_close("c1")

    assert out["success"] is True
    assert out["status"] == "replied"
    db.update.assert_called_once()


def test_sav_lite_recipe_registered() -> None:
    from services.workflow_engine import get_recipe

    recipe = get_recipe("sav_lite")
    assert recipe is not None
    assert recipe.head_agent == "secretary"
    step_ids = [s.id for s in recipe.steps]
    assert "sync_product_kb" in step_ids
    assert "sav_ceo_pending" in step_ids


def test_sync_kb_from_registry_skips_hub() -> None:
    from services.product_kb import sync_kb_from_registry

    app = MagicMock()
    app.slug = "lounge"
    app.name = "Lounge"
    app.branch = "app"
    app.stack = "next"
    app.prod_url = ""
    app.lifecycle_status = "beta"

    hub = MagicMock()
    hub.slug = "hub"

    db = MagicMock()
    db.select.return_value = []

    with (
        patch("services.app_registry.list_apps", return_value=[app, hub]),
        patch("services.product_kb._get_db", return_value=db),
    ):
        out = sync_kb_from_registry()

    assert out["synced"] == 1
    assert db.insert.call_count == 1
    assert db.insert.call_args[0][1]["slug"] == "lounge"
