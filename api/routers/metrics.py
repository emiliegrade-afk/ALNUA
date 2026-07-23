"""Prometheus metrics + platform stats endpoints."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

from typing import Any

from services.llm_cache import llm_cache
from services.telemetry import metrics

router = APIRouter()


@router.get("/metrics")
def prometheus_metrics():
    """Prometheus text exposition format."""
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(metrics.render_prometheus(), media_type="text/plain; version=0.0.4")


@router.get("/platform/stats")
def platform_stats() -> dict[str, Any]:
    """Aggregated platform health for admin dashboard."""
    from services.analytics import get_all_metrics

    return {
        "metrics_snapshot": metrics.snapshot(),
        "llm_cache": llm_cache.stats(),
        "agent_metrics": {
            k: {
                "success_rate": v.success_rate,
                "avg_cost_per_task": v.avg_cost_per_task,
                "avg_latency_ms": v.avg_latency_ms,
                "user_satisfaction": v.user_satisfaction,
            }
            for k, v in get_all_metrics().items()
        },
    }
