#!/usr/bin/env python3
"""One-shot splitter: api/main.py -> api/routers/*.py + thin main.py.

Run from repo root: python scripts/split_api_main.py
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAIN = ROOT / "api" / "main.py"
ROUTERS_DIR = ROOT / "api" / "routers"

# (filename, start_line inclusive, end_line exclusive) — 1-based line numbers from audit
ROUTER_SLICES: list[tuple[str, int, int]] = [
    ("health", 953, 961),
    ("pipeline", 961, 1321),
    ("dashboard", 1321, 1514),
    ("core", 1514, 2252),
    ("briefing", 2255, 2290),
    ("releases", 2290, 2562),
    ("competition", 2562, 2597),
    ("agents_pole", 2597, 2949),
    ("brand", 2949, 3371),
    ("beta", 3371, 3636),
    ("waitlist", 3636, 3819),
    ("partnerships", 3819, 4194),
    ("finances", 4194, 4265),
    ("rnd", 4265, 5226),
    ("composio", 5226, 5246),
    ("scanner", 5246, 5266),
    ("settings", 5266, 5318),
]

ROUTER_HEADER = '''"""Auto-split from api/main.py — {name} routes."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter()


'''

BOOTSTRAP_END = 362  # through middleware
SCHEMAS_START = 364
SCHEMAS_END = 951  # through _beta_tester_auth function end - deps separate
DEPS_START = 946
DEPS_END = 951


def main() -> None:
    lines = MAIN.read_text(encoding="utf-8").splitlines()
    ROUTERS_DIR.mkdir(parents=True, exist_ok=True)

    # --- route_common.py (imports + logger) ---
    import_block: list[str] = []
    for i, line in enumerate(lines):
        ln = i + 1
        if ln < 13:
            continue
        if ln > 158:
            break
        if line.startswith("logger ="):
            import_block.append(line)
            break
        import_block.append(line)

    route_common = (
        '"""Shared imports for split API routers."""\n\n'
        "from __future__ import annotations\n\n"
        + "\n".join(import_block)
        + "\n\n"
        + "from fastapi import APIRouter\n"
    )
    (ROOT / "api" / "route_common.py").write_text(route_common, encoding="utf-8")

    # --- schemas.py ---
    schema_lines = lines[SCHEMAS_START - 1 : SCHEMAS_END]
    schemas_content = (
        '"""Pydantic request/response models for the Hub API."""\n\n'
        "from __future__ import annotations\n\n"
        "from datetime import date\n\n"
        "from fastapi import HTTPException, Header\n"
        "from pydantic import BaseModel, Field\n\n"
        "from services.beta_portal import decode_tester_token\n\n"
        + "\n".join(schema_lines)
        + "\n"
    )
    (ROOT / "api" / "schemas.py").write_text(schemas_content, encoding="utf-8")

    # --- middleware.py ---
    middleware_lines = lines[318:362]
    middleware_content = (
        '"""Hub API key middleware."""\n\n'
        "from __future__ import annotations\n\n"
        "from fastapi import Request\n"
        "from fastapi.responses import JSONResponse\n\n"
        "from config.settings import get_settings\n\n"
        + "\n".join(middleware_lines)
        + "\n\n\n"
        + "def register_middleware(app) -> None:\n"
        + "    app.middleware('http')(hub_api_key_middleware)\n"
    )
    (ROOT / "api" / "middleware.py").write_text(middleware_content, encoding="utf-8")

    # --- lifespan.py ---
    lifespan_lines = lines[160:293]
    lifespan_content = (
        '"""FastAPI lifespan — schedulers, bots, background tasks."""\n\n'
        "from __future__ import annotations\n\n"
        + "\n".join(lifespan_lines)
        + "\n"
    )
    (ROOT / "api" / "lifespan.py").write_text(lifespan_content, encoding="utf-8")

    # --- routers ---
    init_exports: list[str] = []
    for name, start, end in ROUTER_SLICES:
        chunk = lines[start - 1 : end - 1]
        body: list[str] = []
        for line in chunk:
            if line.startswith("# ---") or line.startswith("# ==="):
                continue
            if line.startswith("# ") and not line.strip().startswith("# @") :
                stripped = line.lstrip("# ").strip()
                if stripped and not stripped.startswith("-"):
                    continue
            body.append(line.replace("@app.", "@router."))

        content = ROUTER_HEADER.format(name=name) + "\n".join(body) + "\n"
        (ROUTERS_DIR / f"{name}.py").write_text(content, encoding="utf-8")
        init_exports.append(name)

    init_py = (
        '"""Hub API routers (split from main.py)."""\n\n'
        "from __future__ import annotations\n\n"
        "from fastapi import FastAPI\n\n"
    )
    for name in init_exports:
        init_py += f"from api.routers.{name} import router as {name}_router\n"
    init_py += "\n\nALL_ROUTERS = [\n"
    for name in init_exports:
        init_py += f"    {name}_router,\n"
    init_py += "]\n\n\n"
    init_py += "def register_routers(app: FastAPI) -> None:\n"
    init_py += "    for router in ALL_ROUTERS:\n"
    init_py += "        app.include_router(router)\n"
    (ROUTERS_DIR / "__init__.py").write_text(init_py, encoding="utf-8")

    # --- app.py ---
    bootstrap = lines[0:11]  # docstring + future + path + load_dotenv
    app_py = (
        '"""FastAPI application factory."""\n\n'
        + "\n".join(bootstrap)
        + "\n\n"
        + "import logging\n\n"
        + "import sentry_sdk\n"
        + "from fastapi import FastAPI\n"
        + "from fastapi.middleware.cors import CORSMiddleware\n\n"
        + "from api.lifespan import lifespan\n"
        + "from api.middleware import register_middleware\n"
        + "from api.routers import register_routers\n"
        + "from config.settings import get_settings\n\n"
        + "logger = logging.getLogger(__name__)\n\n"
        + "app = FastAPI(\n"
        + "    title=\"ALNUA Hub\",\n"
        + "    description=\"Backend IA pour ALNUA — agents, bots et données centralisées\",\n"
        + "    version=\"0.1.0\",\n"
        + "    lifespan=lifespan,\n"
        + ")\n\n"
        + "app.add_middleware(\n"
        + "    CORSMiddleware,\n"
        + "    allow_origins=[\n"
        + "        \"http://localhost:3000\",\n"
        + "        \"http://127.0.0.1:3000\",\n"
        + "        \"http://localhost:3001\",\n"
        + "        \"http://127.0.0.1:3001\",\n"
        + "        \"http://localhost:3002\",\n"
        + "        \"http://127.0.0.1:3002\",\n"
        + "    ],\n"
        + "    allow_credentials=True,\n"
        + "    allow_methods=[\"*\"],\n"
        + "    allow_headers=[\"*\"],\n"
        + ")\n\n"
        + "register_middleware(app)\n"
        + "register_routers(app)\n"
    )
    (ROOT / "api" / "app.py").write_text(app_py, encoding="utf-8")

    # --- thin main.py ---
    cli_lines = lines[5317:]
    thin_main = (
        '"""ALNUA Hub — FastAPI entrypoint (uvicorn api.main:app)."""\n\n'
        "from api.app import app  # noqa: F401\n\n"
        + "\n".join(cli_lines)
        + "\n"
    )
    MAIN.write_text(thin_main, encoding="utf-8")
    print(f"Split complete: {len(init_exports)} routers, thin main.py")


if __name__ == "__main__":
    main()
