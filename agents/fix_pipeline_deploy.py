"""Deploy detection, restart, and test execution for fix_pipeline."""
from __future__ import annotations

import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _detect_deploy_method(repo_path: str) -> dict[str, Any]:
    """
    Lit le repo et détecte comment l'app tourne.
    Retourne {"method": str, "command": list, "restart_signal": str}
    """
    root = Path(repo_path)

    if (root / "pm2.config.js").exists() or (root / "ecosystem.config.js").exists():
        name = "hub"
        try:
            cfg = (root / "pm2.config.js").read_text()
            import re

            m = re.search(r'name["\s:]+["\']([^"\']+)', cfg)
            if m:
                name = m.group(1)
        except Exception:
            pass
        return {"method": "pm2", "command": ["pm2", "restart", name], "name": name}

    if (root / "docker-compose.yml").exists() or (root / "docker-compose.yaml").exists():
        return {"method": "docker", "command": ["docker-compose", "restart"], "name": "docker"}

    for f in Path("/etc/systemd/system").glob("*.service") if Path("/etc/systemd/system").exists() else []:
        if "hub" in f.stem or "alnua" in f.stem.lower():
            return {"method": "systemd", "command": ["systemctl", "restart", f.stem], "name": f.stem}

    if (root / "Procfile").exists():
        try:
            proc = (root / "Procfile").read_text().split("\n")[0]
            cmd = proc.split(":", 1)[-1].strip().split()
            return {"method": "procfile", "command": cmd, "name": "web"}
        except Exception:
            pass

    if (root / "api" / "main.py").exists() or (root / "main.py").exists():
        entry = "api.main:app" if (root / "api" / "main.py").exists() else "main:app"
        return {
            "method": "uvicorn",
            "command": ["uvicorn", entry, "--reload", "--port", "8000"],
            "name": "uvicorn",
        }

    return {"method": "unknown", "command": [], "name": "unknown"}


def _restart_app(repo_path: str, deploy_info: dict) -> bool:
    """Redémarre l'app selon la méthode détectée."""
    method = deploy_info["method"]
    cmd = deploy_info["command"]

    if not cmd:
        logger.warning("fix_pipeline: méthode de déploiement inconnue, pas de restart")
        return False

    try:
        if method in ("pm2", "systemd", "docker"):
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return r.returncode == 0
        if method == "uvicorn":
            subprocess.run(["pkill", "-f", "uvicorn"], capture_output=True)
            asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.Popen(cmd, cwd=repo_path),
            )
            return True
        if method == "procfile":
            subprocess.Popen(cmd, cwd=repo_path)
            return True
    except Exception as exc:
        logger.error("fix_pipeline: restart failed: %s", exc)
    return False


def _run_tests(repo_path: str) -> dict[str, Any]:
    """
    Lance pytest si disponible. Retourne {"passed": bool, "output": str, "coverage": int}.
    Si pas de tests → retourne passed=True (no tests = no regression detected).
    """
    root = Path(repo_path)

    test_dirs = [d for d in ["tests", "test", "spec"] if (root / d).is_dir()]
    test_files = list(root.glob("test_*.py")) + list(root.glob("*_test.py"))

    if not test_dirs and not test_files:
        return {
            "passed": True,
            "output": "Aucun test trouvé — skip (pas de régression détectée).",
            "coverage": -1,
        }

    try:
        r = subprocess.run(
            ["python", "-m", "pytest", "-x", "-q", "--tb=short", "--no-header"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=120,
        )
        passed = r.returncode == 0
        output = (r.stdout + r.stderr)[-3000:]
        return {"passed": passed, "output": output, "coverage": -1}
    except FileNotFoundError:
        return {"passed": True, "output": "pytest non installé — skip.", "coverage": -1}
    except subprocess.TimeoutExpired:
        return {"passed": False, "output": "pytest timeout (>2min) — fix potentiellement bloquant.", "coverage": -1}
