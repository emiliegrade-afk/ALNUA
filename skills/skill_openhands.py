"""
OpenHands — agent de codage autonome pour tâches complexes.
Utiliser pour des features complètes ; Aider pour les fixes rapides.
"""
import os
import subprocess


def run_openhands_task(
    message: str,
    repo_path: str,
    timeout: int = 1800,
) -> dict:
    """
    Lance OpenHands en mode headless sur une tâche de codage.

    Args:
        message: La tâche à effectuer
        repo_path: Chemin local du repo
        timeout: Durée max en secondes (défaut 30 min)

    Returns:
        {"success": bool, "output": str}
    """
    cmd = [
        "openhands",
        "--headless",
        "-t",
        message,
    ]

    env = os.environ.copy()
    api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENROUTER_API_KEY")
    if api_key and not env.get("ANTHROPIC_API_KEY"):
        env["ANTHROPIC_API_KEY"] = api_key

    try:
        result = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
        success = result.returncode == 0
        combined = (result.stdout or "") + (result.stderr or "")
        return {
            "success": success,
            "output": combined[-2000:] if success else combined[-1000:],
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": f"Timeout — tâche non terminée après {timeout}s",
        }
    except Exception as e:
        return {"success": False, "output": str(e)}
