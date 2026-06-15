"""Hub API routers (split from main.py)."""

from __future__ import annotations

from fastapi import FastAPI

from api.routers.health import router as health_router
from api.routers.pipeline import router as pipeline_router
from api.routers.dashboard import router as dashboard_router
from api.routers.core import router as core_router
from api.routers.briefing import router as briefing_router
from api.routers.releases import router as releases_router
from api.routers.competition import router as competition_router
from api.routers.agents_pole import router as agents_pole_router
from api.routers.brand import router as brand_router
from api.routers.beta import router as beta_router
from api.routers.waitlist import router as waitlist_router
from api.routers.partnerships import router as partnerships_router
from api.routers.finances import router as finances_router
from api.routers.rnd import router as rnd_router
from api.routers.composio import router as composio_router
from api.routers.scanner import router as scanner_router
from api.routers.settings import router as settings_router
from api.routers.advanced_services import router as advanced_services_router
from api.routers.orchestration import router as orchestration_router
from api.routers.admin import router as admin_router
from api.routers.gdd import router as gdd_router
from api.routers.creatorflow import router as creatorflow_router
from api.routers.academy import router as academy_router
from api.routers.ops import router as ops_router
from api.routers.autonomy import router as autonomy_router


ALL_ROUTERS = [
    health_router,
    pipeline_router,
    dashboard_router,
    core_router,
    briefing_router,
    releases_router,
    competition_router,
    agents_pole_router,
    brand_router,
    beta_router,
    waitlist_router,
    partnerships_router,
    finances_router,
    rnd_router,
    composio_router,
    scanner_router,
    settings_router,
    advanced_services_router,
    orchestration_router,
    admin_router,
    creatorflow_router,
    academy_router,
    ops_router,
    autonomy_router,
]


def register_routers(app: FastAPI) -> None:
    from config.settings import get_settings

    for router in ALL_ROUTERS:
        app.include_router(router)

    if get_settings().gdd_manager_enabled:
        app.include_router(gdd_router)
