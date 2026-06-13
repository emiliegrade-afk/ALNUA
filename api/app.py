"""FastAPI application factory."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

import logging

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.lifespan import lifespan
from api.middleware import register_middleware
from api.routers import register_routers
from config.settings import get_settings

logger = logging.getLogger(__name__)

app = FastAPI(
    title="ALNUA Hub",
    description="Backend IA pour ALNUA — agents, bots et données centralisées",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3002",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_middleware(app)
register_routers(app)

# ---------------------------------------------------------------------------
# MCP Server — expose tous les endpoints ALNUA comme outils MCP natifs
# Cursor config: { "mcpServers": { "alnua-hub": { "url": "http://localhost:8000/mcp" } } }
# ---------------------------------------------------------------------------
try:
    from fastapi_mcp import FastApiMCP
    mcp = FastApiMCP(app)
    mcp.mount()
    logger.info("fastapi-mcp monté sur /mcp — ALNUA Hub disponible comme MCP server")
except ImportError:
    logger.warning("fastapi-mcp non installé — MCP server désactivé. `pip install fastapi-mcp`")
