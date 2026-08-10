"""IDE workspace — sandbox shell and git helpers."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any

from services.ide_workspace import _safe_rel, resolve_workspace

_SHELL_METACHARS = re.compile(r"[;&|`$<>\n\r]")


def language_for(path: Path) -> str:
    ext = path.suffix.lower()
    return {
        ".py": "python",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".js": "javascript",
        ".jsx": "javascript",
        ".json": "json",
        ".md": "markdown",
        ".html": "html",
        ".css": "css",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".sql": "sql",
        ".sh": "shell",
        ".ps1": "powershell",
    }.get(ext, "plaintext")


def run_sandbox_command(command: str, *, cwd_rel: str = ".") -> dict[str, Any]:
    """Restricted shell — sandbox workspace only (CEO learning)."""
    root, _ = resolve_workspace("sandbox")
    cwd = _safe_rel(root, cwd_rel)
    if not cwd.is_dir():
        raise ValueError("cwd invalide")
    cmd = command.strip()
    if _SHELL_METACHARS.search(cmd):
        raise ValueError(
            "Commande refusée : caractères de chaînage/redirection interdits (; & | ` $ < >)"
        )
    allowed = ("python", "py", "node", "npm", "npx", "pytest", "echo", "dir", "ls")
    first_token = cmd.split(None, 1)[0].lower() if cmd else ""
    if first_token not in allowed:
        raise ValueError(f"Commande non autorisée. Autorisé : {', '.join(allowed)}")
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            shell=True,
            capture_output=True,
            text=True,
            timeout=120,
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        return {
            "exitCode": proc.returncode,
            "output": out[-8000:] if len(out) > 8000 else out,
        }
    except subprocess.TimeoutExpired:
        return {"exitCode": -1, "output": "[timeout 120s]"}


def git_diff(workspace_id: str) -> str:
    root, _ = resolve_workspace(workspace_id)
    try:
        proc = subprocess.run(
            ["git", "diff", "--stat"],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=30,
        )
        stat = (proc.stdout or proc.stderr or "").strip()
        proc2 = subprocess.run(
            ["git", "diff"],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=30,
        )
        diff = (proc2.stdout or "")[:12000]
        return f"{stat}\n\n{diff}".strip() or "(aucun changement git)"
    except Exception as exc:
        return f"(git diff indisponible: {exc})"
