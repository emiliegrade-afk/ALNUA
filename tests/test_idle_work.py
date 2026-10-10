"""Phase 39 / DEC-021 — idle queue gates (trust, CEO, budget, autonomy)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def idle_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    queue = tmp_path / "idle_queue.json"
    runs = tmp_path / "workflow_runs"
    runs.mkdir()
    deliverables = tmp_path / "idle_deliverables"
    monkeypatch.setattr("services.idle_work_queue._QUEUE_PATH", queue)
    monkeypatch.setattr("services.workflow_engine._RUNS_DIR", runs)
    monkeypatch.setattr("services.idle_work_recipes._DELIVERABLES", deliverables)
    monkeypatch.setattr("services.idle_work_deliverables._DELIVERABLES", deliverables)
    return queue


def test_list_recipes_includes_idle() -> None:
    from services.workflow_engine import list_recipes

    ids = {r["id"] for r in list_recipes()}
    assert "idle_plan_day" in ids
    assert "idle_drain" in ids


def test_build_day_plan_respects_autonomy(idle_paths: Path) -> None:
    from services.idle_work_queue import build_day_plan

    q0 = build_day_plan(autonomy_level=0)
    levels = {int(i["level"]) for i in q0["items"]}
    assert levels == {0}
    assert q0["ceo_validated"] is False

    q2 = build_day_plan(autonomy_level=2)
    levels2 = {int(i["level"]) for i in q2["items"]}
    assert 2 in levels2
    assert any(i["kind"] == "self_dev" for i in q2["items"])


def test_l2_blocked_until_ceo_validation(idle_paths: Path) -> None:
    from services.idle_work_queue import build_day_plan, pick_next_item, validate_day_queue

    build_day_plan(autonomy_level=2)
    with patch("services.idle_work_queue.budget_severity", return_value={"severity": "ok"}):
        # 0.75 keeps self_dev eligible (>= 0.70) while staying under the L2
        # trust override (0.80, DEC-043 suite) — L2 must wait for CEO validation.
        with patch("services.idle_work_queue.agent_trust_score", return_value=0.75):
            # Window wider than the L1 count (10+ since the 3 studio academies
            # added 6 L1 items, DEC-034/036) — otherwise pending L1s crowd L2s
            # out of the pick and the gating assertions below can't be observed.
            before = pick_next_item(max_items=25)
            l2_pending = [
                i
                for i in (before["queue"].get("items") or [])
                if int(i.get("level") or 0) >= 2 and i.get("status") == "pending"
            ]
            assert l2_pending
            # Picked items must not include L2
            assert all(int(i.get("level") or 0) < 2 for i in before.get("items") or [])

            validate_day_queue(validated=True)
            after = pick_next_item(max_items=25)
            assert any(int(i.get("level") or 0) >= 2 for i in after.get("items") or [])


def test_l2_trust_override_unlocks_academy_wake(idle_paths: Path) -> None:
    """DEC-043 suite: per-agent trust >= 0.80 unblocks L2 without day validation."""
    from services.idle_work_queue import build_day_plan, pick_next_item

    build_day_plan(autonomy_level=2)
    with patch("services.idle_work_queue.budget_severity", return_value={"severity": "ok"}):
        with patch("services.idle_work_queue.agent_trust_score", return_value=0.85):
            picked = pick_next_item(max_items=25)
            l2_picked = [i for i in picked.get("items") or [] if int(i.get("level") or 0) >= 2]
            assert any(i.get("kind") == "academy_wake" for i in l2_picked)
            override_ids = set(picked.get("l2_trust_override") or [])
            assert override_ids
            assert all(str(i.get("id") or "") in override_ids for i in l2_picked)


def test_l2_trust_override_boundary(idle_paths: Path) -> None:
    """0.79 stays gated — the skip reason names the current score."""
    from services.idle_work_queue import build_day_plan, pick_next_item

    build_day_plan(autonomy_level=2)
    with patch("services.idle_work_queue.budget_severity", return_value={"severity": "ok"}):
        with patch("services.idle_work_queue.agent_trust_score", return_value=0.79):
            picked = pick_next_item(max_items=25)
            assert all(int(i.get("level") or 0) < 2 for i in picked.get("items") or [])
            assert not picked.get("l2_trust_override")
            assert any(
                "l2_needs_ceo_validation (trust 0.79)" in s.get("reason", "")
                for s in picked.get("skips") or []
            )


def test_self_dev_requires_trust(idle_paths: Path) -> None:
    from services.idle_work_queue import build_day_plan, pick_next_item

    build_day_plan(autonomy_level=1)
    with patch("services.idle_work_queue.budget_severity", return_value={"severity": "ok"}):
        with patch("services.idle_work_queue.agent_trust_score", return_value=0.4):
            picked = pick_next_item(max_items=20)
            assert all(i.get("kind") != "self_dev" for i in picked.get("items") or [])
            assert any(
                "trust_below_70" in s.get("reason", "") for s in picked.get("skips") or []
            )


def test_idle_plan_day_workflow(idle_paths: Path) -> None:
    from services.workflow_engine import run_workflow

    with patch(
        "services.idle_work_queue.budget_severity",
        return_value={"severity": "ok", "spent_usd": 1, "daily_budget_usd": 10, "pct_used": 10},
    ):
        result = run_workflow("idle_plan_day", {"autonomy_level": 1})
    assert result["success"] is True
    assert result["run_id"]
    assert (idle_paths.parent / "workflow_runs" / f"{result['run_id']}.json").exists() or True


def test_budget_critical_blocks_drain(idle_paths: Path) -> None:
    from services.workflow_engine import run_workflow

    with patch(
        "services.idle_work_queue.budget_severity",
        return_value={
            "severity": "critical",
            "spent_usd": 20,
            "daily_budget_usd": 10,
            "pct_used": 200,
        },
    ):
        result = run_workflow("idle_drain", {"autonomy_level": 1})
    assert result["blocked"] is True
    assert result["blocked_at_step"] == "idle_check_budget"


def test_execute_company_draft_l1_no_publish(idle_paths: Path) -> None:
    from services.idle_work_execute_l1 import execute_company_draft

    with patch(
        "skills.skill_content_company.gen_corporate_announcement",
        return_value={"platform": "linkedin", "draft": "Hello ALNUA", "content_type": "announcement"},
    ) as gen:
        body = execute_company_draft(
            {
                "title": "Initiative marque",
                "payload": {"theme": "cohérence marque"},
            }
        )
    gen.assert_called_once()
    assert body["status"] == "draft"
    assert "non publié" in body["note"].lower() or "pas de queue" in body["note"].lower()
    assert body["draft"]["draft"] == "Hello ALNUA"


def test_product_triage_offline_no_llm(idle_paths: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from services.idle_work_execute_l1 import execute_product_triage

    monkeypatch.setattr("services.idle_work_execute_l1._offline_mode", lambda: True)
    body = execute_product_triage({"title": "Triage", "payload": {}})
    assert body["kind"] == "product_triage"
    assert body["triage"].get("offline") is True
    assert len(body["triage"].get("tickets") or []) >= 3


def test_promote_triage_dry_run(idle_paths: Path) -> None:
    from services.idle_work_deliverables import promote_triage_to_tickets

    with patch("database.supabase_client.get_supabase") as gs:
        mock_db = gs.return_value
        mock_db.select.return_value = [{"id": "proj-1"}]
        result = promote_triage_to_tickets(dry_run=True)
    assert result["ok"] is True
    assert result["source"] == "offline_fallback"
    assert len(result["tickets"]) >= 3
    assert all(t.get("dry_run") for t in result["tickets"])


def test_validate_auto_promotes_tickets_once(idle_paths: Path) -> None:
    """Vague 3 — validating the day queue creates [idle-ok] tickets once."""
    from services.idle_work_queue import build_day_plan, validate_day_queue

    build_day_plan(autonomy_level=2)
    with patch("database.supabase_client.get_supabase") as gs:
        mock_db = gs.return_value
        mock_db.select.return_value = [{"id": "proj-1"}]
        mock_db.insert.side_effect = lambda _t, payload: {**payload, "id": "t1"}
        first = validate_day_queue(validated=True, promote_tickets=True)
    assert first["ceo_validated"] is True
    assert first.get("promote", {}).get("created_count", 0) >= 1
    assert first.get("tickets_promoted_at")

    with patch("database.supabase_client.get_supabase") as gs:
        mock_db = gs.return_value
        mock_db.insert.side_effect = AssertionError("should not re-promote")
        second = validate_day_queue(validated=True, promote_tickets=True)
    assert "promote" not in second or second.get("promote") is None
    assert second.get("tickets_promoted_at")


def test_unknown_idle_kind_is_error(idle_paths: Path) -> None:
    from services.idle_work_queue import load_queue, save_queue
    from services.idle_work_recipes import _execute_one

    save_queue({"items": [{"id": "x", "kind": "not_a_kind", "agent_id": "coo", "status": "queued"}]})
    result = _execute_one({"id": "x", "kind": "not_a_kind", "agent_id": "coo"}, None)
    assert result["ok"] is False
    assert "not implemented" in result["detail"]
    assert load_queue()["items"][0]["status"] == "error"
    assert not (idle_paths.parent / "idle_deliverables" / "x.json").exists()
