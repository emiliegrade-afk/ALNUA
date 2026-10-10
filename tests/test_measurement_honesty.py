"""Lot 1 — measurements either come from a real store or say they are unavailable."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch


class _Resp:
    def __init__(self, payload: Any) -> None:
        self._payload = payload
        self.status_code = 200

    def raise_for_status(self) -> None:
        return None

    def json(self) -> Any:
        return self._payload


class _Client:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        del args, kwargs

    def __enter__(self) -> _Client:
        return self

    def __exit__(self, *args: Any) -> bool:
        del args
        return False

    def get(self, url: str, headers: dict | None = None, params: dict | None = None) -> _Resp:
        del headers, params
        if url.endswith("/commits"):
            return _Resp(
                [
                    {
                        "sha": "abc123def456",
                        "html_url": "https://github.com/acme/app/commit/abc",
                        "commit": {
                            "message": "fix login\nlonger body",
                            "author": {"date": "2026-10-09T12:00:00Z"},
                        },
                    }
                ]
            )
        return _Resp([])


def test_dev_activity_unconfigured(monkeypatch) -> None:
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setenv("GITHUB_REPO", "")
    monkeypatch.setattr("config.github_repos.get_repo_targets", lambda: ())
    from skills.skill_content_app import fetch_dev_activity

    result = fetch_dev_activity("ALNUA", days=7)
    assert result["available"] is False
    assert result["commits"] == []
    assert "pending" not in result["note"]


def test_dev_activity_reads_github(monkeypatch) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setenv("GITHUB_REPO", "acme/app")
    monkeypatch.setattr("skills.skill_github_activity.httpx.Client", _Client)
    from skills.skill_content_app import fetch_dev_activity

    result = fetch_dev_activity("ALNUA", days=7)
    assert result["available"] is True
    assert result["resolved_repo"] == "acme/app"
    assert result["commits"][0]["message"] == "fix login"
    assert result["commits"][0]["sha"] == "abc123def456"


def test_dev_activity_rejects_unsafe_repo(monkeypatch) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setenv("GITHUB_REPO", "acme/app")
    from skills.skill_content_app import fetch_dev_activity

    result = fetch_dev_activity("acme/app;rm", days=7)
    assert result["available"] is False
    assert result["resolved_repo"] is None


def test_campaign_report_uses_ledger_not_zeros() -> None:
    campaign = {
        "id": "c1",
        "budget_allocated_usd": 40,
        "reach": None,
        "engagements": None,
        "conversions": None,
        "revenue_generated_usd": 25,
    }
    expenses = [
        {"type": "expense", "campaign_id": "c1", "amount": 10},
        {"type": "expense", "campaign_id": "other", "amount": 99},
    ]

    class _Db:
        def select(self, table: str, filters: dict | None = None, **kwargs: Any) -> list[dict]:
            del kwargs
            if table == "campaigns":
                return [campaign] if filters and filters.get("id") == "c1" else []
            return expenses

    with patch("database.supabase_client.get_supabase", return_value=_Db()):
        from skills.skill_ads import campaign_roi_report

        found = campaign_roi_report("c1")
        missing = campaign_roi_report("nope")

    assert found["available"] is True
    assert found["platform_live"] is False
    assert found["spent_usd"] == 10
    assert found["roi_pct"] == 150.0
    assert found["reach"] is None
    assert "impressions" not in found
    assert "clicks" not in found
    assert missing["ok"] is False
    assert "spend" not in missing


def test_post_analytics_omits_counts() -> None:
    from skills.skill_social_scheduler import track_post_analytics

    result = track_post_analytics("p1", "instagram")
    assert result["available"] is False
    assert "impressions" not in result
    assert "likes" not in result


def test_gaming_milestones_read_builds() -> None:
    rows = [{"build_number": "12", "status": "success", "branch": "main", "notes": "ok", "created_at": "t"}]

    class _Db:
        def select(self, table: str, **kwargs: Any) -> list[dict]:
            assert table == "gaming_builds"
            del kwargs
            return rows

    with patch("database.supabase_client.get_supabase", return_value=_Db()):
        from skills.skill_content_gaming import fetch_gaming_milestones

        result = fetch_gaming_milestones("wyrdheim")
    assert result["available"] is True
    assert result["milestones"][0]["build_number"] == "12"
    assert result["last_playable_build"]["status"] == "success"


def test_robo_milestones_read_lab() -> None:
    lab = {"ok": True, "items": [{"name": "moteur", "status": "pass", "measured_value": "1", "created_at": "t"}]}
    builds = {"ok": True, "items": []}
    with (
        patch("skills.skill_robo_lab.get_lab_context", return_value=lab),
        patch("skills.skill_robo_lab.get_builds_context", return_value=builds),
    ):
        from skills.skill_content_robo import fetch_robo_milestones

        result = fetch_robo_milestones("eve")
    assert result["available"] is True
    assert result["milestones"][0]["name"] == "moteur"
    assert result["last_prototype_image"] is None
