"""IDE workspaces — safe file access for Hub web IDE and agent worktrees."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parents[1]
_SANDBOX = _ROOT / "data" / "ide_sandbox"

_EDITABLE_EXT = frozenset(
    {
        ".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".md", ".txt", ".yaml", ".yml",
        ".html", ".css", ".scss", ".env.example", ".sql", ".sh", ".ps1", ".toml",
        ".cfg", ".ini", ".xml", ".svg",
    }
)

_BLOCKED_NAMES = frozenset({".env", "credentials.json", ".pem", "id_rsa"})


@dataclass(frozen=True)
class WorkspaceInfo:
    id: str
    label: str
    path: str
    kind: str  # hub | sandbox | agent | worktree
    read_only: bool
    active: bool = False


def _hub_root() -> Path:
    return Path(os.getenv("HUB_REPO_PATH", str(_ROOT))).resolve()


def _ensure_sandbox() -> Path:
    _SANDBOX.mkdir(parents=True, exist_ok=True)
    readme = _SANDBOX / "README.md"
    if not readme.exists():
        readme.write_text(
            "# Bac à sable Emilie\n\n"
            "Espace pour apprendre à coder avec **Luca** (prof ALNUA).\n"
            "Tes fichiers ici ne touchent pas le Hub principal.\n",
            encoding="utf-8",
        )
    return _SANDBOX.resolve()


def _list_worktrees(hub: Path) -> list[Path]:
    wt_dir = hub / "worktrees"
    if not wt_dir.is_dir():
        return []
    return sorted([p for p in wt_dir.iterdir() if p.is_dir()], key=lambda p: p.name)


def _active_agent_worktree() -> Path | None:
    try:
        from services.coding_activity import get_active_worktree_path

        p = get_active_worktree_path()
        if p and Path(p).is_dir():
            return Path(p).resolve()
    except Exception:
        pass
    return None


def list_workspaces() -> list[WorkspaceInfo]:
    hub = _hub_root()
    sandbox = _ensure_sandbox()
    active_wt = _active_agent_worktree()
    out: list[WorkspaceInfo] = [
        WorkspaceInfo(
            id="hub",
            label="ALNUA Hub (principal)",
            path=str(hub),
            kind="hub",
            read_only=False,
            active=False,
        ),
        WorkspaceInfo(
            id="sandbox",
            label="Bac à sable — apprentissage",
            path=str(sandbox),
            kind="sandbox",
            read_only=False,
            active=False,
        ),
    ]
    if active_wt:
        out.append(
            WorkspaceInfo(
                id="agent",
                label=f"Agent en cours — {active_wt.name}",
                path=str(active_wt),
                kind="agent",
                read_only=True,
                active=True,
            )
        )
    for wt in _list_worktrees(hub):
        is_active = active_wt is not None and wt.resolve() == active_wt
        out.append(
            WorkspaceInfo(
                id=f"worktree:{wt.name}",
                label=f"Worktree — {wt.name}",
                path=str(wt.resolve()),
                kind="worktree",
                read_only=not is_active,
                active=is_active,
            )
        )
    return out


def resolve_workspace(workspace_id: str) -> tuple[Path, bool]:
    """Return (root_path, read_only). Raises ValueError if unknown."""
    wid = (workspace_id or "hub").strip()
    if wid == "hub":
        return _hub_root(), False
    if wid == "sandbox":
        return _ensure_sandbox(), False
    if wid == "agent":
        active = _active_agent_worktree()
        if not active:
            raise ValueError("Aucun agent en train de coder — worktree agent indisponible")
        return active, True
    if wid.startswith("worktree:"):
        name = wid.removeprefix("worktree:")
        hub = _hub_root()
        target = (hub / "worktrees" / name).resolve()
        hub_res = hub.resolve()
        if not str(target).startswith(str(hub_res)):
            raise ValueError("Worktree invalide")
        if not target.is_dir():
            raise ValueError(f"Worktree introuvable : {name}")
        active = _active_agent_worktree()
        ro = active is None or target.resolve() != active.resolve()
        return target, ro
    raise ValueError(f"Workspace inconnu : {wid}")


def _safe_rel(root: Path, rel: str) -> Path:
    rel = (rel or ".").strip().replace("\\", "/").lstrip("/")
    if ".." in rel.split("/"):
        raise ValueError("Chemin interdit")
    resolved = (root / rel).resolve()
    root_res = root.resolve()
    if not str(resolved).startswith(str(root_res)):
        raise ValueError("Hors workspace")
    return resolved


def _allowed_file(path: Path, *, for_write: bool = False) -> None:
    name = path.name.lower()
    if name in _BLOCKED_NAMES or name.startswith(".env"):
        raise ValueError(f"Fichier protégé : {path.name}")
    if for_write and path.suffix.lower() not in _EDITABLE_EXT and path.name not in ("README",):
        if path.suffix:
            raise ValueError(f"Extension non autorisée : {path.suffix}")


def list_tree(workspace_id: str, rel_path: str = ".") -> dict[str, Any]:
    root, read_only = resolve_workspace(workspace_id)
    base = _safe_rel(root, rel_path)
    if not base.is_dir():
        raise ValueError("Pas un dossier")
    entries: list[dict[str, Any]] = []
    try:
        children = sorted(base.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    except PermissionError:
        raise ValueError("Permission refusée") from None
    for child in children[:500]:
        if child.name.startswith(".git") and child.name != ".gitkeep":
            continue
        rel = str(child.relative_to(root)).replace("\\", "/")
        entries.append(
            {
                "name": child.name,
                "path": rel,
                "type": "dir" if child.is_dir() else "file",
            }
        )
    return {
        "workspace": workspace_id,
        "path": str(base.relative_to(root)).replace("\\", "/") if base != root else ".",
        "readOnly": read_only,
        "entries": entries,
    }


def read_file(workspace_id: str, rel_path: str) -> dict[str, Any]:
    from services.ide_workspace_shell import language_for

    root, read_only = resolve_workspace(workspace_id)
    path = _safe_rel(root, rel_path)
    if not path.is_file():
        raise ValueError("Fichier introuvable")
    _allowed_file(path)
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) > 500_000:
        text = text[:500_000] + "\n\n… [tronqué — fichier trop volumineux]"
    return {
        "workspace": workspace_id,
        "path": str(path.relative_to(root)).replace("\\", "/"),
        "content": text,
        "readOnly": read_only,
        "language": language_for(path),
    }


def write_file(workspace_id: str, rel_path: str, content: str) -> dict[str, str]:
    root, read_only = resolve_workspace(workspace_id)
    if read_only:
        raise ValueError("Workspace en lecture seule (agent en cours)")
    path = _safe_rel(root, rel_path)
    _allowed_file(path, for_write=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return {"path": str(path.relative_to(root)).replace("\\", "/"), "status": "saved"}


def run_sandbox_command(command: str, *, cwd_rel: str = ".") -> dict[str, Any]:
    from services.ide_workspace_shell import run_sandbox_command as _run

    return _run(command, cwd_rel=cwd_rel)


def git_diff(workspace_id: str) -> str:
    from services.ide_workspace_shell import git_diff as _git_diff

    return _git_diff(workspace_id)
