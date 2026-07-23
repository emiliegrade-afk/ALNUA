"""
skill_pi_ssh.py — Connexion SSH au Raspberry Pi Eve

Variables d'env :
- PI_HOST : IP ou hostname du Pi (ex: 192.168.1.42)
- PI_USER : utilisateur SSH (défaut: pi)
- PI_SSH_KEY : chemin clé SSH privée (défaut: ~/.ssh/id_ed25519)

Implémentation principale : agents/embedded_dev_agent.py (pi_ssh_command tool)
"""

from __future__ import annotations

import logging
import os
import re
import subprocess
from typing import Any

logger = logging.getLogger(__name__)

PI_NOT_CONFIGURED = "Raspberry Pi non configuré — renseigne PI_HOST dans .env"
PI_COMMAND_BLOCKED = "Commande bloquée — motif destructeur détecté : {pattern}"
PI_COMMAND_TOO_LONG = "Commande trop longue (max 4000 caractères)"

# This is a trust boundary, not a sandbox: whoever holds HUB_API_KEY can already
# run arbitrary commands on Eve by design (agent tool, /agents/embedded/pi-command).
# This blocklist catches catastrophic accidents and injected payloads — a wipe,
# a fork bomb, an unattended reboot, curl|sh from the open internet — not a
# fully malicious authenticated caller.
_DESTRUCTIVE_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\brm\b(?=.*-[a-z]*r)(?=.*-[a-z]*f)",  # rm with both -r and -f, any order/grouping
        r"mkfs\.",
        r"dd\s+.*of=/dev/",
        r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:",  # classic fork bomb
        r"\bshutdown\b|\breboot\b|\bpoweroff\b|\bhalt\b",
        r">\s*/dev/sd[a-z]",
        r"chmod\s+-R\s+777\s+/",
        r"(curl|wget)\s+.*\|\s*(sh|bash)",
    )
)


def _check_command_safety(command: str) -> str | None:
    """Returns a rejection reason, or None if the command is allowed to run."""
    if len(command) > 4000:
        return PI_COMMAND_TOO_LONG
    for pattern in _DESTRUCTIVE_PATTERNS:
        if pattern.search(command):
            return PI_COMMAND_BLOCKED.format(pattern=pattern.pattern)
    return None


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

    rejection = _check_command_safety(command)
    if rejection:
        logger.warning("Pi SSH command rejected: %s | command=%r", rejection, command[:200])
        return {
            "success": False,
            "output": rejection,
            "host": pi_host,
            "command": command,
        }

    logger.info("Pi SSH command: %s@%s: %s", pi_user, pi_host, command[:200])

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
