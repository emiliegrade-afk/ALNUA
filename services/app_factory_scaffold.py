"""Local scaffold and registry for App Factory runs."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.app_factory_models import (
    AppFactoryRequest,
    FactoryTask,
    _FACTORY_STACK,
    _PLANS_DIR,
    default_local_path,
)
from services.app_registry import AppRegistryUpsert, upsert_app


def ensure_local_scaffold(slug: str, stack: _FACTORY_STACK, local_path: Path) -> bool:
    """Create minimal on-disk scaffold when repo folder is empty."""
    if local_path.exists() and any(local_path.iterdir()):
        return False
    local_path.mkdir(parents=True, exist_ok=True)
    readme = (
        f"# {slug}\n\nScaffold ALNUA App Factory (Phase 2).\n\n"
        f"Stack: {stack}\n"
    )
    (local_path / "README.md").write_text(readme, encoding="utf-8")
    if stack == "expo":
        (local_path / "app.json").write_text(
            json.dumps({"expo": {"name": slug, "slug": slug, "version": "1.0.0"}}, indent=2),
            encoding="utf-8",
        )
        (local_path / "package.json").write_text(
            json.dumps(
                {
                    "name": slug,
                    "version": "0.1.0",
                    "private": True,
                    "main": "expo/AppEntry.js",
                    "scripts": {"start": "expo start"},
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    else:
        (local_path / "package.json").write_text(
            json.dumps(
                {
                    "name": slug,
                    "version": "0.1.0",
                    "private": True,
                    "scripts": {
                        "dev": "next dev",
                        "build": "next build",
                        "lint": "next lint",
                    },
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        src_app = local_path / "src" / "app"
        src_app.mkdir(parents=True, exist_ok=True)
        (src_app / "page.tsx").write_text(
            'export default function Home() {\n  return <main>MVP</main>;\n}\n',
            encoding="utf-8",
        )
    return True


def persist_plan(slug: str, plan: list[FactoryTask]) -> Path:
    _PLANS_DIR.mkdir(parents=True, exist_ok=True)
    path = _PLANS_DIR / f"{slug}.json"
    payload = {
        "slug": slug,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "tasks": [t.model_dump() for t in plan],
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def register_factory_app(req: AppFactoryRequest, slug: str) -> dict[str, Any]:
    local = req.local_path.strip() or default_local_path(slug)
    stack_label = "Next.js" if req.stack == "nextjs" else "Expo"
    entry = upsert_app(
        AppRegistryUpsert(
            slug=slug,
            name=req.name.strip(),
            branch=req.branch,
            github_repo=req.github_repo.strip(),
            local_path=local,
            description=req.brief[:500],
            stack=stack_label,
            enabled=True,
        )
    )
    return entry.model_dump()
