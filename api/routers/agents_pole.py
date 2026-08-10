"""Deprecated kitchen-sink — routes peeled to domain routers.

Empty router kept so `agents_pole_router` import remains valid; zero routes.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()
