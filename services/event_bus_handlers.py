"""Pre-wired event bus handlers and extension loading."""

from __future__ import annotations

import logging

from services.event_bus import Event, subscribe

logger = logging.getLogger(__name__)


@subscribe("feature_shipped")
def _on_feature_shipped(event: Event) -> None:
    """Quand une feature est livrée → pipeline contenu automatique."""
    try:
        feature = event.payload.get("feature", "nouvelle feature")
        from services.competition import add_points

        source = event.source_agent or "dev_app"
        add_points(source, "feature_shipped", note=f"Event: {feature[:40]}")
    except Exception:
        pass


@subscribe("budget_alert")
def _on_budget_alert(event: Event) -> None:
    """Quand le budget est dépassé → log pour Rémi (controller)."""
    severity = event.payload.get("severity", "warning")
    spent = event.payload.get("spent_usd", 0)
    logger.warning(f"BUDGET ALERT [{severity}]: ${spent} spent today")


@subscribe("task_failed")
def _on_task_failed(event: Event) -> None:
    """Log des échecs pour monitoring."""
    agent = event.payload.get("agent_id", "unknown")
    error = event.payload.get("error", "")
    logger.error(f"task_failed event: agent={agent} error={error[:100]}")


def load_extension_handlers() -> None:
    """Phase 36 cross-dept handlers — separate module to keep event_bus lean."""
    try:
        import services.cross_dept_handlers  # noqa: F401
    except Exception as exc:
        logger.debug("cross_dept_handlers not loaded: %s", exc)
