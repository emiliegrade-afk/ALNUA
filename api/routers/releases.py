"""Auto-split from api/main.py — releases routes."""

from __future__ import annotations

from api.route_common import *  # noqa: F403
from api.routers.releases_agents_misc import router as agents_misc_router
from api.routers.releases_brainstorm import router as brainstorm_router
from api.routers.releases_coo_webhooks import router as coo_webhooks_router
from api.routers.releases_crud import router as crud_router

router = APIRouter()
router.include_router(crud_router)
router.include_router(coo_webhooks_router)
router.include_router(agents_misc_router)
router.include_router(brainstorm_router)
