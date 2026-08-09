"""Tests company_errors unified queue."""

from __future__ import annotations

from unittest.mock import patch



def test_record_company_error_local_and_supabase() -> None:
    from services.company_errors import record_company_error

    with (
        patch("services.coding_error_journal.record_coding_error") as rec_local,
        patch("skills.skill_error_journal.log_error", return_value="uuid-1") as rec_sb,
    ):
        rec_local.return_value = {"id": "00001", "status": "open"}
        out = record_company_error(
            agent_name="dev_app",
            error_type="TestError",
            error_message="boom",
            repo_slug="hub",
        )
    assert out["local"]["id"] == "00001"
    assert out["supabase_id"] == "uuid-1"
    rec_sb.assert_called_once()


def test_list_open_merges_sources() -> None:
    from services.company_errors import list_open_errors

    journal = {
        "entries": [
            {
                "id": "1",
                "status": "open",
                "repo_slug": "nomad",
                "error_type": "X",
                "error_message": "only local",
                "created_at": "2026-06-17",
            }
        ],
        "patterns": {},
    }

    with (
        patch("services.coding_error_journal.load_journal", return_value=journal),
        patch("services.company_errors._list_supabase_open", return_value=[
            {
                "id": "sb-1",
                "source": "supabase",
                "agent_name": "dev_app",
                "repo_slug": None,
                "error_type": "Y",
                "error_message": "from supabase",
                "status": "open",
                "created_at": "2026-06-18",
                "attempts": 0,
                "dedupe_key": "abc",
            }
        ]),
    ):
        items = list_open_errors(limit=10)

    assert len(items) >= 2


def test_workflow_run_ops_has_remediate_step() -> None:
    from services.workflow_engine import get_recipe

    recipe = get_recipe("run_ops")
    assert recipe is not None
    ids = [s.id for s in recipe.steps]
    assert "remediate_errors" in ids


def test_workflow_semaine_recipe() -> None:
    from services.workflow_engine import get_recipe

    recipe = get_recipe("semaine")
    assert recipe is not None
    assert any(s.id == "ceo_queue_reminder" for s in recipe.steps)
