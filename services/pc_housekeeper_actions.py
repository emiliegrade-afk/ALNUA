"""PC housekeeper — move / quarantine / purge actions."""

from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.pc_housekeeper_core import (
    DEFAULT_PROPOSALS,  # noqa: F401 — re-export for tests / callers
    DEFAULT_QUARANTINE,
    REPORT_DIR,
    _is_blocked,
    _load_state,
    _save_state,
    _utc,
    list_quarantine,
)


def apply_proposals(proposals: list[dict[str, Any]], *, dry_run: bool = False) -> dict[str, Any]:
    moves: list[dict[str, Any]] = []
    errors: list[str] = []
    for p in proposals:
        src = Path(str(p.get("source") or ""))
        dest_dir = Path(str(p.get("suggested_dir") or ""))
        if not src.is_file() or _is_blocked(src):
            errors.append(f"skip invalid: {src}")
            continue
        try:
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / src.name
            if dest.exists():
                dest = dest_dir / f"{src.stem}_{datetime.now().strftime('%H%M%S')}{src.suffix}"
            if dry_run:
                moves.append({"from": str(src), "to": str(dest), "dry_run": True})
            else:
                shutil.move(str(src), str(dest))
                moves.append({"from": str(src), "to": str(dest)})
        except OSError as exc:
            errors.append(f"{src}: {exc}")
    report = {"at": _utc(), "type": "apply", "moves": moves, "errors": errors}
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORT_DIR / f"apply_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    path.write_text(__import__("json").dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    report["report_path"] = str(path)
    state = _load_state()
    if moves and not errors:
        state["good_reports"] = int(state.get("good_reports") or 0) + 1
        _save_state(state)
    return report


def quarantine_for_delete(paths: list[str]) -> dict[str, Any]:
    DEFAULT_QUARANTINE.mkdir(parents=True, exist_ok=True)
    moved: list[dict[str, Any]] = []
    errors: list[str] = []
    for raw in paths:
        src = Path(raw)
        if not src.exists() or _is_blocked(src):
            errors.append(f"skip: {raw}")
            continue
        try:
            dest = DEFAULT_QUARANTINE / src.name
            if dest.exists():
                dest = DEFAULT_QUARANTINE / f"{src.stem}_{datetime.now().strftime('%H%M%S')}{src.suffix}"
            shutil.move(str(src), str(dest))
            moved.append({"from": str(src), "quarantine": str(dest)})
        except OSError as exc:
            errors.append(f"{raw}: {exc}")
    report = {
        "at": _utc(),
        "type": "quarantine",
        "moved": moved,
        "errors": errors,
        "note": "Fichiers en quarantaine — vérifie puis purge_quarantine(confirm=True).",
        "quarantine_dir": str(DEFAULT_QUARANTINE),
    }
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORT_DIR / f"quarantine_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    path.write_text(__import__("json").dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    report["report_path"] = str(path)
    return report


def purge_quarantine(*, confirm: bool = False) -> dict[str, Any]:
    if not confirm:
        return {
            "ok": False,
            "error": "confirm=false — rien supprimé. Passe confirm=true après vérification.",
            "items": list_quarantine(),
        }
    deleted: list[str] = []
    errors: list[str] = []
    for item in list_quarantine():
        p = Path(item["path"])
        try:
            if p.is_file():
                p.unlink()
            elif p.is_dir():
                shutil.rmtree(p)
            deleted.append(str(p))
        except OSError as exc:
            errors.append(f"{p}: {exc}")
    return {"ok": True, "deleted": deleted, "errors": errors, "at": _utc()}
