"""Mission Graph persistence — data/missions/{id}.json (DEC-023)."""

from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Any

from config.paths import get_hub_repo_path
from services.mission_graph_models import Mission, _now_iso

logger = logging.getLogger(__name__)

_LOCK = threading.RLock()


def _missions_dir() -> Path:
    path = get_hub_repo_path() / "data" / "missions"
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_mission(mission: Mission) -> Path:
    mission.updated_at = _now_iso()
    mission.recompute_status()
    path = _missions_dir() / f"{mission.mission_id}.json"
    with _LOCK:
        tmp = path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(mission.to_dict(), indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
        tmp.replace(path)
    return path


def get_mission(mission_id: str) -> Mission | None:
    mid = (mission_id or "").strip()
    if not mid:
        return None
    path = _missions_dir() / f"{mid}.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return Mission.from_dict(data)
    except Exception as exc:
        logger.warning("mission get failed %s: %s", mid, exc)
        return None


def list_missions(*, limit: int = 30, status: str | None = None) -> list[dict[str, Any]]:
    items: list[Mission] = []
    for path in sorted(_missions_dir().glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            m = Mission.from_dict(json.loads(path.read_text(encoding="utf-8")))
            if status and m.status != status:
                continue
            items.append(m)
        except Exception:
            continue
        if len(items) >= limit:
            break
    return [
        {
            "mission_id": m.mission_id,
            "title": m.title,
            "status": m.status,
            "objective": (m.objective or "")[:160],
            "progress_pct": m.progress_pct(),
            "task_count": len(m.tasks),
            "created_at": m.created_at,
            "updated_at": m.updated_at,
            "finished_at": m.finished_at,
            "source": m.source,
        }
        for m in items
    ]


def delete_mission(mission_id: str) -> bool:
    path = _missions_dir() / f"{(mission_id or '').strip()}.json"
    if not path.exists():
        return False
    path.unlink()
    return True


def set_missions_dir_for_tests(path: Path) -> None:
    """Test helper — redirect store root."""
    global _missions_dir

    def _dir() -> Path:
        path.mkdir(parents=True, exist_ok=True)
        return path

    # Monkeypatch via attribute on module used by tests
    import services.mission_graph_store as mod

    mod._missions_dir = _dir  # type: ignore[assignment]
