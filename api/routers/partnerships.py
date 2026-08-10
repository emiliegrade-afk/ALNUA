"""Auto-split from api/main.py — partnerships routes."""

from __future__ import annotations

from api.route_common import *  # noqa: F403
from api.routers.partnerships_affiliate import router as affiliate_router
from api.routers.partnerships_partners import router as partners_router
from api.routers.partnerships_requests import router as requests_router

router = APIRouter()
router.include_router(partners_router)
router.include_router(affiliate_router)
router.include_router(requests_router)
