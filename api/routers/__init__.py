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
from api.routers.brand_system import router as brand_system_router
from api.routers.beta import router as beta_router
from api.routers.waitlist import router as waitlist_router
from api.routers.partnerships import router as partnerships_router
from api.routers.finances import router as finances_router
from api.routers.campaigns import router as campaigns_router
from api.routers.marketing_funnel import router as marketing_funnel_router
from api.routers.rnd import router as rnd_router
from api.routers.rnd_trees import router as rnd_trees_router
from api.routers.rnd_council import router as rnd_council_router
from api.routers.rnd_explorer import router as rnd_explorer_router
from api.routers.composio import router as composio_router
from api.routers.scanner import router as scanner_router
from api.routers.settings import router as settings_router
from api.routers.advanced_services import router as advanced_services_router
from api.routers.orchestration import router as orchestration_router
from api.routers.admin import router as admin_router
from api.routers.gdd import router as gdd_router
from api.routers.academy import router as academy_router
from api.routers.ops import router as ops_router
from api.routers.autonomy import router as autonomy_router
from api.routers.assistant import router as assistant_router
from api.routers.library import router as library_router
from api.routers.ide import router as ide_router
from api.routers.apps_registry import router as apps_registry_router
from api.routers.workflows import router as workflows_router
from api.routers.sav import router as sav_router
from api.routers.nadia_desktop import router as nadia_desktop_router
from api.routers.nomenclature import router as nomenclature_router
from api.routers.feedback import router as feedback_router
from api.routers.metrics import router as metrics_router
from api.routers.plugins import router as plugins_router
from api.routers.personality import router as personality_router
from api.routers.trust import router as trust_router
from api.routers.ue58_bridge import router as ue58_bridge_router
from api.routers.robo_phase21 import router as robo_phase21_router


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
    brand_system_router,
    beta_router,
    waitlist_router,
    partnerships_router,
    finances_router,
    campaigns_router,
    marketing_funnel_router,
    rnd_router,
    rnd_trees_router,
    rnd_council_router,
    rnd_explorer_router,
    composio_router,
    scanner_router,
    settings_router,
    advanced_services_router,
    orchestration_router,
    admin_router,
    academy_router,
    ops_router,
    autonomy_router,
    assistant_router,
    library_router,
    ide_router,
    apps_registry_router,
    workflows_router,
    sav_router,
    nadia_desktop_router,
    nomenclature_router,
    feedback_router,
    metrics_router,
    plugins_router,
    personality_router,
    trust_router,
    ue58_bridge_router,
    robo_phase21_router,
]


def register_routers(app: FastAPI) -> None:
    from config.settings import get_settings

    # Chaque router n'est monté qu'une fois : le monter aussi sous /v1 enregistrait
    # deux fois les mêmes fonctions handler, ce qui dupliquait les operation_id
    # dans le schéma OpenAPI et risquait des collisions d'outils côté fastapi-mcp.
    # Aucun consommateur actuel (web/, n8n/, bots/) n'utilise le préfixe /v1.
    for router in ALL_ROUTERS:
        app.include_router(router)

    if get_settings().gdd_manager_enabled:
        app.include_router(gdd_router)
