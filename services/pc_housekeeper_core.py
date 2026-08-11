"""PC housekeeper — scan / propose / state (DEC-030)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config.settings import get_settings

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
STATE_FILE = DATA / "housekeeper_state.json"
REPORT_DIR = DATA / "housekeeper_reports"
DEFAULT_QUARANTINE = DATA / "housekeeper_quarantine"
DEFAULT_PROPOSALS = DATA / "housekeeper_proposals"

_BLOCKED_NAMES = frozenset(
    {
        ".git",
        ".ssh",
        ".gnupg",
        "AppData",
        "NTUSER.DAT",
        "System Volume Information",
        "$Recycle.Bin",
    }
)


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_state() -> dict[str, Any]:
    DATA.mkdir(parents=True, exist_ok=True)
    if not STATE_FILE.is_file():
        return {"autonomy": False, "trusted_since": None, "good_reports": 0, "roots": []}
    try:
        raw = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        return raw if isinstance(raw, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _save_state(state: dict[str, Any]) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _is_blocked(path: Path) -> bool:
    parts = {p.lower() for p in path.parts}
    return any(b.lower() in parts for b in _BLOCKED_NAMES)


def resolve_roots(extra: list[str] | None = None) -> list[Path]:
    configured = (getattr(get_settings(), "housekeeper_roots", "") or "").strip()
    roots: list[Path] = []
    if configured:
        for part in configured.split(";"):
            p = Path(part.strip()).expanduser()
            if p.is_dir():
                roots.append(p.resolve())
    home = Path.home()
    for candidate in (home / "Desktop", home / "Documents", home / "Downloads"):
        if candidate.is_dir():
            roots.append(candidate.resolve())
    for part in extra or []:
        p = Path(part).expanduser()
        if p.is_dir():
            roots.append(p.resolve())
    seen: set[str] = set()
    out: list[Path] = []
    for r in roots:
        key = str(r).lower()
        if key not in seen:
            seen.add(key)
            out.append(r)
    return out


def scan_clutter(roots: list[Path] | None = None, *, limit: int = 200) -> dict[str, Any]:
    roots = roots or resolve_roots()
    items: list[dict[str, Any]] = []
    for root in roots:
        if _is_blocked(root):
            continue
        try:
            entries = list(root.iterdir())
        except OSError:
            continue
        for entry in entries:
            if len(items) >= limit:
                break
            if _is_blocked(entry):
                continue
            try:
                if entry.is_file():
                    items.append(
                        {
                            "path": str(entry),
                            "name": entry.name,
                            "root": str(root),
                            "size": entry.stat().st_size,
                            "kind": "file",
                        }
                    )
                elif entry.is_dir() and not entry.name.startswith("."):
                    try:
                        children = [c for c in entry.iterdir() if c.is_file()][:5]
                    except OSError:
                        children = []
                    items.append(
                        {
                            "path": str(entry),
                            "name": entry.name,
                            "root": str(root),
                            "size": 0,
                            "kind": "dir",
                            "sample_files": [c.name for c in children],
                        }
                    )
            except OSError:
                continue
    return {"roots": [str(r) for r in roots], "items": items, "count": len(items), "at": _utc()}


def propose_organization(scan: dict[str, Any] | None = None) -> dict[str, Any]:
    scan = scan or scan_clutter()
    DEFAULT_PROPOSALS.mkdir(parents=True, exist_ok=True)
    categories = {
        ".pdf": "Documents/PDF",
        ".doc": "Documents/Word",
        ".docx": "Documents/Word",
        ".xls": "Documents/Excel",
        ".xlsx": "Documents/Excel",
        ".png": "Media/Images",
        ".jpg": "Media/Images",
        ".jpeg": "Media/Images",
        ".mp4": "Media/Video",
        ".zip": "Archives",
        ".rar": "Archives",
        ".exe": "Installers_a_verifier",
        ".msi": "Installers_a_verifier",
    }
    proposals: list[dict[str, Any]] = []
    for item in scan.get("items") or []:
        if item.get("kind") != "file":
            continue
        ext = Path(str(item.get("name") or "")).suffix.lower()
        cat = categories.get(ext, "Divers")
        proposals.append(
            {
                "source": item.get("path"),
                "suggested_dir": str(DEFAULT_PROPOSALS / cat),
                "category": cat,
                "action": "move_proposed",
            }
        )
    report = {
        "at": _utc(),
        "type": "proposal",
        "proposals": proposals,
        "note": "Rien déplacé. Valide puis apply_proposals.",
    }
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORT_DIR / f"proposal_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    report["report_path"] = str(path)
    return report


def list_quarantine() -> list[dict[str, Any]]:
    if not DEFAULT_QUARANTINE.is_dir():
        return []
    out: list[dict[str, Any]] = []
    for p in DEFAULT_QUARANTINE.iterdir():
        try:
            out.append(
                {"path": str(p), "name": p.name, "size": p.stat().st_size if p.is_file() else 0}
            )
        except OSError:
            continue
    return out


def set_autonomy(enabled: bool) -> dict[str, Any]:
    state = _load_state()
    state["autonomy"] = bool(enabled)
    if enabled and not state.get("trusted_since"):
        state["trusted_since"] = _utc()
    _save_state(state)
    return state


def status() -> dict[str, Any]:
    state = _load_state()
    return {
        **state,
        "roots": [str(r) for r in resolve_roots()],
        "quarantine_count": len(list_quarantine()),
        "quarantine_dir": str(DEFAULT_QUARANTINE),
        "proposals_dir": str(DEFAULT_PROPOSALS),
    }
