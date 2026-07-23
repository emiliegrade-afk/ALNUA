"""Resolve git/npm/gh on Windows when Hub runs as a background daemon (minimal PATH)."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


def ensure_coding_cli_path() -> None:
    """Prepend common CLI install dirs so subprocess finds git, gh, npm, npx."""
    if sys.platform != "win32":
        return
    extras: list[str] = []
    pf = os.environ.get("ProgramFiles", r"C:\Program Files")
    pf86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    for candidate in (
        Path(pf) / "Git" / "cmd",
        Path(pf) / "GitHub CLI",
        Path(pf) / "nodejs",
        Path(pf86) / "Git" / "cmd",
        Path.home() / "AppData" / "Roaming" / "npm",
    ):
        if candidate.is_dir():
            extras.append(str(candidate))
    if not extras:
        return
    current = os.environ.get("PATH", "")
    prefix = os.pathsep.join(extras)
    if not any(p in current for p in extras):
        os.environ["PATH"] = f"{prefix}{os.pathsep}{current}"


def resolve_cli(name: str) -> str:
    """Return executable path for git, gh, npm, npx, etc."""
    ensure_coding_cli_path()
    resolved = shutil.which(name)
    if sys.platform == "win32":
        cmd = shutil.which(f"{name}.cmd")
        if cmd:
            resolved = cmd
        elif resolved and not resolved.lower().endswith((".exe", ".cmd", ".bat")):
            sibling = Path(resolved).with_suffix(".cmd")
            if sibling.is_file():
                resolved = str(sibling)
    if not resolved:
        raise FileNotFoundError(f"{name} CLI introuvable (PATH)")
    return resolved
