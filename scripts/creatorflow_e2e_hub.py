"""CreatorFlow E2E — minimal Hub with in-memory cf_* store."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

os.environ["HUB_API_KEY"] = "test-hub-key-for-ci"
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-supabase-key")
os.environ.setdefault("OPENROUTER_API_KEY", "test-openrouter-key")
os.environ["ENVIRONMENT"] = "development"
os.environ["CF_EXPORT_MODE"] = "mock"

from config.settings import get_settings

get_settings.cache_clear()

from tests.test_creatorflow_sprint4 import _FakeCfDB  # noqa: E402

_fake_db = _FakeCfDB()


def _patch_services() -> None:
    import database.supabase_client as sc

    sc.get_supabase = lambda: _fake_db  # type: ignore[assignment]

    import agents.cf_content_analyzer as analyzer
    import agents.cf_timing_optimizer as timing
    import services.creatorflow_platforms as platforms

    analyzer.analyze_cf_asset = lambda asset: {  # type: ignore[method-assign]
        "themes": ["e2e"],
        "content_type": "test",
        "quality_score": 0.9,
    }
    timing.get_cf_timing_suggestions = lambda user_id, platform, db=None: [  # type: ignore[method-assign]
        {
            "platform": platform,
            "suggested_at": "2030-01-01T18:00:00+00:00",
            "score": 0.9,
            "reason": "E2E slot",
        }
    ]
    platforms.has_active_connection = lambda _u, _t: False  # type: ignore[method-assign]
    platforms.list_cf_platform_status = lambda user_id, db=None: [  # type: ignore[method-assign]
        {"platform": "youtube", "is_active": False, "platform_username": None, "connected_at": None},
        {"platform": "instagram", "is_active": False, "platform_username": None, "connected_at": None},
    ]
    platforms.start_cf_platform_connect = lambda platform, user_id: {  # type: ignore[method-assign]
        "platform": platform,
        "oauth_url": f"https://example.com/oauth/{platform}",
        "already_connected": False,
        "message": None,
    }


def build_app():
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from api.middleware import hub_api_key_middleware
    from api.routers.creatorflow import router as creatorflow_router

    app = FastAPI(title="CreatorFlow E2E Hub")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3002",
            "http://127.0.0.1:3002",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.middleware("http")(hub_api_key_middleware)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "creatorflow-e2e"}

    app.include_router(creatorflow_router)
    return app


def main() -> None:
    _patch_services()
    import uvicorn

    port = int(os.environ.get("CF_E2E_HUB_PORT", "8012"))
    uvicorn.run(build_app(), host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    main()
