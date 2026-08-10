"""Deprecated kitchen-sink — routes peeled to services_*.py routers.

Empty router kept so `advanced_services_router` import remains valid; zero routes.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()
