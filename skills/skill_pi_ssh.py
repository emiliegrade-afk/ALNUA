"""
skill_pi_ssh.py — Connexion SSH au Raspberry Pi Eve

Variables d'env :
- PI_HOST : IP ou hostname du Pi (ex: 192.168.1.42)
- PI_USER : utilisateur SSH (défaut: pi)
- PI_SSH_KEY : chemin clé SSH privée (défaut: ~/.ssh/id_ed25519)

Implémentation principale : agents/embedded_dev_agent.py (pi_ssh_command tool)
"""

from __future__ import annotations

import os
import subprocess
from typing import Any

PI_NOT_CONFIGURED = "Raspberry Pi non configuré — renseigne PI_HOST dans .env"


def pi_is_configured() -> bool:
    return bool(os.getenv("PI_HOST", "").strip())


def run_pi_command(command: str, timeout: int = 30) -> dict[str, Any]:
    """
    Exécute une commande sur le Raspberry Pi Eve via SSH.

    Returns:
        {"success": bool, "output": str, "host": str, "command": str}
    """
    pi_host = os.getenv("PI_HOST")
    pi_user = os.getenv("PI_USER", "pi")
    pi_key = os.path.expanduser(os.getenv("PI_SSH_KEY", "~/.ssh/id_ed25519"))

    if not pi_host:
        return {
            "success": False,
            "output": PI_NOT_CONFIGURED,
            "host": "",
            "command": command,
        }

    try:
        result = subprocess.run(
            [
                "ssh",
                "-i",
                pi_key,
                "-o",
                "StrictHostKeyChecking=no",
                f"{pi_user}@{pi_host}",
                command,
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = (result.stdout or result.stderr).strip()
        return {
            "success": result.returncode == 0,
            "output": output,
            "host": pi_host,
            "command": command,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": f"Timeout ({timeout}s) — Eve ne répond pas",
            "host": pi_host,
            "command": command,
        }
    except Exception as e:
        return {
            "success": False,
            "output": f"Erreur SSH : {e}",
            "host": pi_host,
            "command": command,
        }


def pi_ssh_command_raw(command: str, timeout: int = 30) -> str:
    """Exécute une commande SSH et retourne la sortie brute (lève si échec)."""
    result = run_pi_command(command, timeout=timeout)
    if not result["success"]:
        raise RuntimeError(result["output"])
    return result["output"]
