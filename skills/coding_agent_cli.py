"""Claude/Aider CLI helpers — split from skill_coding_agent."""
from __future__ import annotations

import logging
import os
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

def _resolve_cli(name: str) -> str:
    """Resolve CLI binary — uvicorn on Windows often lacks npm in PATH."""
    import sys
    if sys.platform == "win32":
        npm_bin = Path.home() / "AppData" / "Roaming" / "npm"
        if npm_bin.is_dir():
            path = os.environ.get("PATH", "")
            if str(npm_bin) not in path:
                os.environ["PATH"] = f"{npm_bin}{os.pathsep}{path}"
    resolved = shutil.which(name)
    if sys.platform == "win32":
        cmd_candidate = shutil.which(f"{name}.cmd")
        if cmd_candidate:
            resolved = cmd_candidate
        elif resolved and not resolved.lower().endswith((".exe", ".cmd", ".bat")):
            sibling = Path(resolved).with_suffix(".cmd")
            if sibling.is_file():
                resolved = str(sibling)
    if not resolved:
        raise FileNotFoundError(
            f"{name} CLI introuvable (PATH). Ex: npm i -g @anthropic-ai/claude-code"
        )
    return resolved

def run_command(

    cmd: list[str], cwd: str | None = None, timeout: int = 60
) -> tuple[int, str, str]:
    """

    Lance une commande shell et retourne (returncode, stdout, stderr).
    """

    try:
        from services.cli_paths import ensure_coding_cli_path, resolve_cli
        ensure_coding_cli_path()
        argv = list(cmd)
        if argv:
            try:
                argv[0] = resolve_cli(argv[0])
            except FileNotFoundError:
                pass
        result = subprocess.run(
            argv,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired as exc:
        logger.error("[CodingAgent] Command timeout (%ss): %s", timeout, cmd)
        stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return 124, stdout, stderr or f"Command timed out after {timeout}s"

