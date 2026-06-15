"""CreatorFlow — export monitoring stats (Sprint 4)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from database.supabase_client import SupabaseClient
from database.creatorflow_supabase_client import get_cf_supabase


def get_cf_export_stats(user_id: str, db: SupabaseClient | None = None) -> dict[str, Any]:
    """Aggregate export success rate and recent activity for dashboard monitoring."""
    db = db or get_cf_supabase()
    rows = db.select(
        "cf_exports",
        filters={"user_id": user_id},
        order_by="created_at",
        ascending=False,
    )

    total = len(rows)
    by_status: dict[str, int] = {
        "pending": 0,
        "processing": 0,
        "success": 0,
        "failed": 0,
    }
    real_count = 0
    mock_count = 0
    last_7_days = 0
    week_cutoff = datetime.now(timezone.utc) - timedelta(days=7)

    for row in rows:
        status = row.get("status") or "pending"
        by_status[status] = by_status.get(status, 0) + 1

        meta = row.get("adapted_metadata") or {}
        mode = meta.get("publish_mode")
        if mode == "real":
            real_count += 1
        elif mode == "mock":
            mock_count += 1

        created = row.get("created_at") or ""
        try:
            ts = datetime.fromisoformat(created.replace("Z", "+00:00"))
            if ts >= week_cutoff:
                last_7_days += 1
        except ValueError:
            pass

    finished = by_status["success"] + by_status["failed"]
    success_rate = round(by_status["success"] / finished * 100, 1) if finished else 0.0

    by_platform: dict[str, dict[str, int]] = {}
    for row in rows:
        platform = row.get("platform") or "youtube"
        bucket = by_platform.setdefault(platform, {"total": 0, "success": 0, "failed": 0})
        bucket["total"] += 1
        status = row.get("status") or "pending"
        if status == "success":
            bucket["success"] += 1
        elif status == "failed":
            bucket["failed"] += 1

    return {
        "total": total,
        "success": by_status["success"],
        "failed": by_status["failed"],
        "pending": by_status["pending"] + by_status["processing"],
        "success_rate_pct": success_rate,
        "real_exports": real_count,
        "mock_exports": mock_count,
        "last_7_days": last_7_days,
        "by_platform": [
            {"platform": platform, **counts}
            for platform, counts in sorted(by_platform.items())
        ],
    }
