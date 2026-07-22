"""FastAPI application factory."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.lifespan import lifespan
from api.middleware import register_middleware
from api.routers import register_routers
from config.settings import get_settings

logger = logging.getLogger(__name__)


def _cors_origins() -> list[str]:
    """Local dev ports + production portal (BETA_PORTAL_BASE_URL / VERCEL_URL)."""
    origins = {
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3002",
    }
    settings = get_settings()
    portal = settings.beta_portal_base_url.strip().rstrip("/")
    if portal:
        origins.add(portal)
    vercel_url = os.environ.get("VERCEL_URL", "").strip()
    if vercel_url:
        origins.add(f"https://{vercel_url}")
    return sorted(origins)


app = FastAPI(
    title="ALNUA Hub",
    description="Backend IA pour ALNUA — agents, bots et données centralisées",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_middleware(app)
register_routers(app)

try:
    from services.otel import instrument_fastapi
    instrument_fastapi(app)
except Exception:
    pass

# ---------------------------------------------------------------------------
# MCP Server — expose tous les endpoints ALNUA comme outils MCP natifs (HTTP transport)
# Cursor config: { "mcpServers": { "alnua-hub": { "url": "http://localhost:8000/mcp" } } }
# ---------------------------------------------------------------------------
try:
    from fastapi_mcp import FastApiMCP
    mcp = FastApiMCP(app)
    mcp.mount_http()
    logger.info("fastapi-mcp monté sur /mcp (HTTP) — ALNUA Hub disponible comme MCP server")
except ImportError:
    logger.warning("fastapi-mcp non installé — MCP server désactivé. `pip install fastapi-mcp`")
