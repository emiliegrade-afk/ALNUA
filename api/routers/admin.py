"""Admin tooling routes — feature flags and gated UI surfaces (Phase 1)."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter()


@router.get("/admin/flags")
def admin_flags() -> dict[str, Any]:
    """
    Feature flags for admin pages — frontend gates links and page access.
    Safe to call from lobby; returns only non-secret toggles.
    """
    from config.settings import get_settings

    s = get_settings()
    env = s.environment.strip().lower()
    return {
        "environment": env,
        "admin_costs_page_enabled": s.admin_costs_page_enabled,
        "admin_events_page_enabled": s.admin_events_page_enabled,
        "admin_ab_test_page_enabled": s.admin_ab_test_page_enabled,
        "briefing_coo_section_enabled": s.briefing_coo_section_enabled,
        "briefing_unified_generate": s.briefing_unified_generate,
        "costs_unified_read": s.costs_unified_read,
        "costs_shadow_compare": s.costs_shadow_compare,
        "gdd_manager_enabled": s.gdd_manager_enabled,
        "preview_allowed": env == "development",
    }
