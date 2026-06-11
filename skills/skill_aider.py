"""
Aider — agent de codage ciblé.
Utiliser pour des tâches simples : fix de bug, ajout de fonction, refacto.
Utiliser OpenHands pour des features complètes.
"""
import os
import subprocess


def run_aider_task(
    message: str,
    repo_path: str,
    files: list[str] | None = None,
    model: str | None = None,
) -> dict:
    """
    Lance Aider sur une tâche de codage.

    Args:
        message: La tâche à effectuer
        repo_path: Chemin local du repo
        files: Fichiers spécifiques à modifier (optionnel)
        model: Modèle LLM

    Returns:
        {"success": bool, "output": str}
    """
    model = model or os.getenv("AIDER_MODEL", "anthropic/claude-sonnet-4-5")
    api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENROUTER_API_KEY")

    cmd = [
        "aider",
        "--model",
        model,
        "--yes",
        "--no-git",
        "--message",
        message,
    ]

    if files:
        cmd.extend(files)

    env = os.environ.copy()
    if api_key:
        env["ANTHROPIC_API_KEY"] = api_key

    try:
        result = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=300,
            env=env,
        )
        success = result.returncode == 0
        return {
            "success": success,
            "output": result.stdout[-2000:] if success else result.stderr[-1000:],
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": "Timeout — tâche trop longue pour Aider, utilise OpenHands",
        }
    except Exception as e:
        return {"success": False, "output": str(e)}
