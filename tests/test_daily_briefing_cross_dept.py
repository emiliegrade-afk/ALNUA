"""Vague 3 — daily briefing consumes cross-dept queue."""

from __future__ import annotations

from services.daily_briefing import _collect_cross_dept


def test_collect_cross_dept_shape(monkeypatch) -> None:
    monkeypatch.setattr(
        "services.cross_dept_handlers.list_cross_dept_queue",
        lambda limit=15, status=None: [
            {
                "status": "queued",
                "department": "marketing",
                "action": "launch_plan",
                "title": "Naïa",
                "event_type": "project_validated",
            },
            {
                "status": "done",
                "department": "finances",
                "action": "draft_budget_forecast",
                "title": "Naïa",
                "result_summary": "budget_forecast",
            },
        ],
    )
    out = _collect_cross_dept()
    assert out["queued_count"] == 1
    assert out["done_count"] == 1
    assert out["by_department"]["marketing"] == 1
    assert out["sample"][0]["title"] == "Naïa"
    assert out["recent_done"][0]["result_summary"] == "budget_forecast"
