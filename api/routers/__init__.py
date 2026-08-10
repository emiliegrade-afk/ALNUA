"""Hub API routers (split from main.py)."""

from __future__ import annotations

from fastapi import FastAPI

from api.routers.health import router as health_router
from api.routers.pipeline_tasks import router as pipeline_tasks_router
from api.routers.pipeline_openroom import router as pipeline_openroom_router
from api.routers.pipeline_costs import router as pipeline_costs_router
from api.routers.dashboard import router as dashboard_router
from api.routers.core import router as core_router
from api.routers.projects import router as projects_router
from api.routers.tickets import router as tickets_router
from api.routers.robo_ops import router as robo_ops_router
from api.routers.gaming_ops import router as gaming_ops_router
from api.routers.roadmap import router as roadmap_router
from api.routers.posts import router as posts_router
from api.routers.analytics import router as analytics_router
from api.routers.faq import router as faq_router
from api.routers.briefing import router as briefing_router
from api.routers.releases import router as releases_router
from api.routers.competition import router as competition_router
from api.routers.agents_pole import router as agents_pole_router
from api.routers.agents_secretary import router as agents_secretary_router
from api.routers.agents_dev import router as agents_dev_router
from api.routers.agents_gaming_studio import router as agents_gaming_studio_router
from api.routers.agents_rnd_persona import router as agents_rnd_persona_router
from api.routers.agents_robo import router as agents_robo_router
from api.routers.agents_comms import router as agents_comms_router
from api.routers.agents_finance import router as agents_finance_router
from api.routers.agents_analytics import router as agents_analytics_router
from api.routers.agents_bots import router as agents_bots_router
from api.routers.brand_analyze import router as brand_analyze_router
from api.routers.brand_kits import router as brand_kits_router
from api.routers.brand_system import router as brand_system_router
from api.routers.beta import router as beta_router
from api.routers.waitlist import router as waitlist_router
from api.routers.partnerships import router as partnerships_router
from api.routers.finances import router as finances_router
from api.routers.campaigns import router as campaigns_router
from api.routers.marketing_funnel import router as marketing_funnel_router
from api.routers.rnd import router as rnd_router
from api.routers.rnd_dossiers import router as rnd_dossiers_router
from api.routers.rnd_committee import router as rnd_committee_router
from api.routers.rnd_assets import router as rnd_assets_router
from api.routers.rnd_social import router as rnd_social_router
from api.routers.rnd_ceo import router as rnd_ceo_router
from api.routers.rnd_product import router as rnd_product_router
from api.routers.rnd_trees import router as rnd_trees_router
from api.routers.rnd_council import router as rnd_council_router
from api.routers.rnd_explorer import router as rnd_explorer_router
from api.routers.composio import router as composio_router
from api.routers.scanner import router as scanner_router
from api.routers.settings import router as settings_router
from api.routers.advanced_services import router as advanced_services_router
from api.routers.services_llm_router import router as services_llm_router
from api.routers.services_parallel import router as services_parallel_router
from api.routers.services_content import router as services_content_router
from api.routers.services_research import router as services_research_router
from api.routers.services_code_graph import router as services_code_graph_router
from api.routers.services_costs import router as services_costs_router
from api.routers.services_ab_test import router as services_ab_test_router
from api.routers.services_events import router as services_events_router
from api.routers.services_coo_briefing import router as services_coo_briefing_router
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
from api.routers.isolation import router as isolation_router
from api.routers.missions import router as missions_router
from api.routers.review_chain import router as review_chain_router
from api.routers.context_memory import router as context_memory_router
from api.routers.ue58_bridge import router as ue58_bridge_router
from api.routers.robo_phase21 import router as robo_phase21_router


ALL_ROUTERS = [
    health_router,
    pipeline_tasks_router,
    pipeline_openroom_router,
    pipeline_costs_router,
    dashboard_router,
    core_router,
    projects_router,
    tickets_router,
    robo_ops_router,
    gaming_ops_router,
    roadmap_router,
    posts_router,
    analytics_router,
    faq_router,
    briefing_router,
    releases_router,
    competition_router,
    agents_pole_router,
    agents_secretary_router,
    agents_dev_router,
    agents_gaming_studio_router,
    agents_rnd_persona_router,
    agents_robo_router,
    agents_comms_router,
    agents_finance_router,
    agents_analytics_router,
    agents_bots_router,
    brand_analyze_router,
    brand_kits_router,
    brand_system_router,
    beta_router,
    waitlist_router,
    partnerships_router,
    finances_router,
    campaigns_router,
    marketing_funnel_router,
    rnd_router,
    rnd_dossiers_router,
    rnd_committee_router,
    rnd_assets_router,
    rnd_social_router,
    rnd_ceo_router,
    rnd_product_router,
    rnd_trees_router,
    rnd_council_router,
    rnd_explorer_router,
    composio_router,
    scanner_router,
    settings_router,
    advanced_services_router,
    services_llm_router,
    services_parallel_router,
    services_content_router,
    services_research_router,
    services_code_graph_router,
    services_costs_router,
    services_ab_test_router,
    services_events_router,
    services_coo_briefing_router,
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
    isolation_router,
    missions_router,
    review_chain_router,
    context_memory_router,
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
