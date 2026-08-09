"""Eve sourcing — alternatives / assembly / infra roles (mocked LLM)."""

from __future__ import annotations

from unittest.mock import patch

from services import eve_sourcing


def test_suggest_alternatives_ok() -> None:
    fake = {
        "need": "caméra",
        "options": [{"name": "OAK-D Lite", "tier": "pro", "approx_price_eur": 120}],
        "recommendation": "pro pour depth",
        "disclaimer": "verify",
    }
    with (
        patch.object(eve_sourcing, "get_bom_context", return_value={"ok": True, "items": []}),
        patch.object(eve_sourcing, "LLMClient") as mock_llm,
        patch.object(eve_sourcing, "parse_json_response", return_value=fake),
    ):
        mock_llm.return_value.complete.return_value = "{}"
        out = eve_sourcing.suggest_alternatives("caméra depth Pi")
    assert out["ok"] is True
    assert out["options"][0]["name"] == "OAK-D Lite"


def test_assembly_plan_ok() -> None:
    fake = {"title": "Plan", "steps": [{"order": 1, "title": "Alim"}]}
    with (
        patch.object(
            eve_sourcing,
            "get_bom_context",
            return_value={"ok": True, "items": [{"component": "Pi 5"}]},
        ),
        patch.object(eve_sourcing, "LLMClient") as mock_llm,
        patch.object(eve_sourcing, "parse_json_response", return_value=fake),
    ):
        mock_llm.return_value.complete.return_value = "{}"
        out = eve_sourcing.assembly_plan(goal="base Eve")
    assert out["ok"] is True
    assert out["steps"][0]["order"] == 1


def test_infra_blueprint_ok() -> None:
    fake = {
        "summary_for_emilie": "Robot vs app",
        "companion_app_stack": {"like_naia": True},
    }
    with (
        patch.object(eve_sourcing, "get_bom_context", return_value={"ok": True, "items": []}),
        patch.object(eve_sourcing, "LLMClient") as mock_llm,
        patch.object(eve_sourcing, "parse_json_response", return_value=fake),
    ):
        mock_llm.return_value.complete.return_value = "{}"
        out = eve_sourcing.infra_roles_blueprint()
    assert out["ok"] is True
    assert out["companion_app_stack"]["like_naia"] is True
