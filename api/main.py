"""ALNUA Hub — FastAPI entrypoint (uvicorn api.main:app)."""

from api.app import app  # noqa: F401

# ---------------------------------------------------------------------------
# CLI entry
# ---------------------------------------------------------------------------
def main() -> None:
    import logging

    import uvicorn

    from config.settings import get_settings

    settings = get_settings()
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
    )


if __name__ == "__main__":
    main()
