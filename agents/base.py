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
        method_name: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        return self.chat(
            system=system,
            messages=[{"role": "user", "content": user}],
            model=model,
            agent_id=agent_id,
            method_name=method_name,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def chat(
        self,
        system: str,
        messages: list[dict[str, str]],
        model: str | None = None,
        agent_id: str | None = None,
        method_name: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        # Résolution : explicit > llm_router > agent_id config > global .env
        resolved_model = to_api_model_slug(model) if model else None
        if not resolved_model and agent_id and method_name:
            try:
                from services.llm_router import route_to_model

                user_text = " ".join(
                    m.get("content", "") for m in messages if m.get("role") == "user"
                )
                resolved_model = to_api_model_slug(
                    route_to_model(agent_id, user_text, method_name)
                )
            except Exception:
                pass
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
        content = data["choices"][0]["message"]["content"]
        self._record_usage(
            data=data,
            agent_id=agent_id,
            model=resolved_model,
            method_name=method_name,
        )
        return content

    def _record_usage(
        self,
        *,
        data: dict[str, Any],
        agent_id: str | None,
        model: str,
        method_name: str,
    ) -> None:
        """Track LLM usage in cost_monitor (+ optional Supabase legacy)."""
        try:
            usage = data.get("usage") or {}
            prompt_tokens = int(usage.get("prompt_tokens") or 0)
            completion_tokens = int(usage.get("completion_tokens") or 0)
            if not prompt_tokens and not completion_tokens:
                return

            from services.cost_monitor import check_budget_alert, record_call

            cost_usd = record_call(
                agent_id=agent_id or "unknown",
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                method=method_name,
            )
            try:
                from skills.skill_model_usage import log_usage

                log_usage(
                    agent_name=agent_id or "unknown",
                    model=model,
                    tokens_in=prompt_tokens,
                    tokens_out=completion_tokens,
                    cost_usd=cost_usd,
                    task_id=method_name or None,
                )
            except Exception:
                pass

            alert = check_budget_alert()
            if alert.get("alert"):
                from services.event_bus import emit

                emit(
                    "budget_alert",
                    {
                        "severity": alert.get("severity"),
                        "spent_usd": alert.get("spent_usd"),
                        "daily_budget_usd": alert.get("daily_budget_usd"),
                    },
                    source_agent=agent_id or "system",
                )
        except Exception:
            pass


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
        try:
            from services.event_bus import emit

            emit(
                "task_completed",
                {"task": task[:200], "agent_id": agent_id},
                source_agent=agent_id,
            )
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
        try:
            from services.event_bus import emit

            emit(
                "task_failed",
                {
                    "task": task[:200],
                    "agent_id": agent_id,
                    "error": error_str[:300],
                },
                source_agent=agent_id,
            )
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
