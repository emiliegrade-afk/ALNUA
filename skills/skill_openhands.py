"""
Skill OpenHands — envoie une tâche de codage à OpenHands et streame le résultat.
OpenHands tourne sur localhost:3001 (docker).
"""
import json
import os
import urllib.request

OPENHANDS_URL = os.getenv("OPENHANDS_URL", "http://localhost:3001")


def run_openhands_task(
    task: str,
    repo_path: str,
    model: str | None = None,
    api_key: str | None = None,
) -> dict:
    """
    Envoie une tâche à OpenHands et retourne le résultat.

    Args:
        task: Description de la tâche en langage naturel
        repo_path: Chemin local du repo (ex: C:/Dev/naia)
        model: Modèle LLM à utiliser (défaut: depuis .env)
        api_key: Clé API LLM (défaut: depuis .env)

    Returns:
        {"success": bool, "result": str, "conversation_id": str | None}
    """
    model = model or os.getenv("OPENROUTER_MODEL", "anthropic/claude-sonnet-4-5")
    api_key = api_key or os.getenv("OPENROUTER_API_KEY") or os.getenv("ANTHROPIC_API_KEY")

    payload = {
        "initial_user_msg": task,
        "runtime_container_image": os.getenv(
            "SANDBOX_RUNTIME_CONTAINER_IMAGE",
            "ghcr.io/all-hands-ai/runtime:0.39-nikolaik",
        ),
        "llm_model": model,
        "llm_api_key": api_key,
        "llm_base_url": os.getenv("OPENROUTER_BASE_URL", ""),
        "selected_repository": repo_path,
    }

    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{OPENHANDS_URL}/api/conversations",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=300) as r:
            result = json.loads(r.read())
        return {
            "success": True,
            "conversation_id": result.get("conversation_id"),
            "result": result.get("final_response", "Tâche terminée"),
        }
    except Exception as e:
        return {"success": False, "result": str(e), "conversation_id": None}


def get_openhands_status(conversation_id: str) -> dict:
    """Vérifie le statut d'une tâche OpenHands en cours."""
    try:
        req = urllib.request.Request(
            f"{OPENHANDS_URL}/api/conversations/{conversation_id}",
        )
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"status": "unknown", "error": str(e)}
