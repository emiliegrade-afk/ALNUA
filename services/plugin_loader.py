"""Plugin marketplace loader — dynamic agent packs from plugins/ directory."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

PLUGINS_ROOT = Path(__file__).resolve().parent.parent / "plugins"


@dataclass
class PluginManifest:
    id: str
    name: str
    version: str
    author: str
    description: str
    agent_module: str
    compatible_hub: str
    path: Path


def _parse_manifest(path: Path) -> PluginManifest | None:
    manifest_path = path / "manifest.json"
    if not manifest_path.exists():
        return None
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        return PluginManifest(
            id=data["id"],
            name=data.get("name", data["id"]),
            version=data.get("version", "0.0.0"),
            author=data.get("author", "unknown"),
            description=data.get("description", ""),
            agent_module=data.get("agent_module", "agent"),
            compatible_hub=data.get("compatible_hub", ">=0.1.0"),
            path=path,
        )
    except (json.JSONDecodeError, KeyError) as exc:
        logger.warning("Invalid manifest %s: %s", manifest_path, exc)
        return None


def discover_plugins() -> list[PluginManifest]:
    """Scan plugins/ for valid manifest.json files."""
    if not PLUGINS_ROOT.exists():
        return []
    manifests: list[PluginManifest] = []
    for child in sorted(PLUGINS_ROOT.iterdir()):
        if child.is_dir() and not child.name.startswith("_"):
            m = _parse_manifest(child)
            if m:
                manifests.append(m)
    return manifests


def load_plugin_agent(manifest: PluginManifest) -> Any | None:
    """Import agent class from plugin directory (lazy, on demand)."""
    agent_file = manifest.path / f"{manifest.agent_module}.py"
    if not agent_file.exists():
        logger.warning("Plugin %s: agent file missing %s", manifest.id, agent_file)
        return None
    try:
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            f"plugin_{manifest.id}",
            agent_file,
        )
        if not spec or not spec.loader:
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return getattr(module, "PluginAgent", None)
    except Exception as exc:
        logger.exception("Failed to load plugin %s: %s", manifest.id, exc)
        return None


def list_plugins() -> list[dict[str, Any]]:
    """List plugins from Supabase hub_plugins, fallback to filesystem."""
    try:
        from database.supabase_client import get_supabase
        db = get_supabase()
        rows = db.select("hub_plugins", filters={"enabled": True})
        if rows:
            return [
                {
                    "id": r["id"],
                    "name": r.get("name", r["id"]),
                    "version": r.get("version", "0.0.0"),
                    "author": r.get("author", ""),
                    "description": r.get("description", ""),
                    "compatible_hub": r.get("compatible_hub", ">=0.1.0"),
                    "storage_path": r.get("storage_path"),
                }
                for r in rows
            ]
    except Exception:
        pass
    return [
        {
            "id": m.id,
            "name": m.name,
            "version": m.version,
            "author": m.author,
            "description": m.description,
            "compatible_hub": m.compatible_hub,
        }
        for m in discover_plugins()
    ]
