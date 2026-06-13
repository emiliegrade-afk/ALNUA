"""Shared utilities for ALNUA Hub agents."""

from __future__ import annotations

import json
from typing import Any

import httpx

from config.settings import get_settings
from database.supabase_client import SupabaseClient, get_supabase


def to_api_model_slug(model: str) -> str:
    """OpenRouter REST API expects provider/model without openrouter/ prefix."""
    m = model.strip()
    if m.startswith("openrouter/"):
        return m[len("openrouter/") :]
    return m


def to_crewai_model_slug(model: str) -> str:
    """CrewAI LLM wrapper expects openrouter/provider/model."""
    m = model.strip()
    if not m.startswith("openrouter/"):
        return f"openrouter/{m}"
    return m


def resolve_openrouter_model(agent_id: str) -> str:
    """Resolved model slug for OpenRouter REST API calls."""
    from config.agent_models import get_model_for_agent

    return to_api_model_slug(get_model_for_agent(agent_id))


def build_crewai_llm(agent_id: str, temperature: float = 0.3):
    """CrewAI LLM instance using per-agent model config."""
    from crewai import LLM

    settings = get_settings()
    model = to_crewai_model_slug(resolve_openrouter_model(agent_id))
    return LLM(
        model=model,
        base_url=settings.openrouter_base_url,
        api_key=settings.openrouter_api_key,
        temperature=temperature,
    )


class LLMClient:
    """OpenRouter chat completion client."""

    def __init__(self) -> None:
        self._settings = get_settings()

    def complete(
        self,
        system: str,
        user: str,
        model: str | None = None,
        agent_id: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        return self.chat(
            system=system,
            messages=[{"role": "user", "content": user}],
            model=model,
            agent_id=agent_id,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def chat(
        self,
        system: str,
        messages: list[dict[str, str]],
        model: str | None = None,
        agent_id: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        # Résolution : explicit > agent_id config > global .env
        resolved_model = to_api_model_slug(model) if model else None
        if not resolved_model:
            if agent_id:
                try:
                    resolved_model = resolve_openrouter_model(agent_id)
                except Exception:
                    pass
            fallback = self._settings.agent_model or self._settings.default_llm_model
            resolved_model = resolved_model or to_api_model_slug(fallback)

        # Injection contexte compétitif
        enriched_system = system
        if agent_id:
            try:
                from config.agent_personas import get_persona, get_competitive_context
                persona = get_persona(agent_id)
                if persona and persona.get("competitive", False):
                    from services.competition import get_scores
                    current_scores = get_scores()
                    competitive_block = get_competitive_context(agent_id, current_scores)
                    if competitive_block:
                        enriched_system = f"{system}\n\n{competitive_block}"
            except Exception:
                pass  # Dégradé silencieux — ne jamais bloquer un appel LLM

        payload = {
            "model": resolved_model,
            "messages": [{"role": "system", "content": enriched_system}, *messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self._settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://alnua-hub.local",
            "X-Title": "ALNUA Hub",
        }
        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                f"{self._settings.openrouter_base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        return data["choices"][0]["message"]["content"]


def run_with_learning(
    agent_id: str,
    task: str,
    fn,
    *args,
    **kwargs,
) -> Any:
    """
    Wrapper universel : exécute fn(*args, **kwargs) puis déclenche
    l'apprentissage en arrière-plan selon le résultat.

    Usage dans n'importe quel agent :
        result = run_with_learning("marketing_agent", "Rédiger post", self.write_post, topic)

    Tous les agents héritent de cette fonction — aucun code dupliqué.
    """
    import traceback
    from skills.skill_agent_learning import is_task_failure

    try:
        result = fn(*args, **kwargs)
        outcome = str(result)[:600] if result else "Tâche complétée sans output"
        try:
            from skills.skill_agent_learning import learn_from_outcome
            learn_from_outcome(
                agent_id=agent_id,
                task=task,
                outcome=outcome,
                success=not is_task_failure(outcome),
            )
        except Exception:
            pass
        try:
            from services.competition import add_points
            add_points(agent_id, "task_completed", note=f"{task[:80]}")
        except Exception:
            pass
        return result
    except Exception as exc:
        error_str = f"{type(exc).__name__}: {exc}\n{traceback.format_exc()[-500:]}"
        try:
            from skills.skill_agent_learning import learn_from_failure
            learn_from_failure(agent_id=agent_id, task=task, error=error_str)
        except Exception:
            pass
        raise


def log_agent_action(
    db: SupabaseClient,
    agent_name: str,
    action: str,
    input_summary: str,
    output_summary: str,
    status: str = "success",
    project_id: str | None = None,
) -> dict[str, Any]:
    return db.insert(
        "agent_logs",
        {
            "agent_name": agent_name,
            "action": action,
            "project_id": project_id,
            "input_summary": input_summary[:2000],
            "output_summary": output_summary[:2000],
            "status": status,
        },
    )


def parse_json_response(text: str) -> dict[str, Any]:
    """Extract JSON object from LLM response (handles markdown fences)."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = lines[1:] if lines[0].startswith("```") else lines
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines)
    return json.loads(cleaned)
