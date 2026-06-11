"""Monitoring LLM via Langfuse — trace chaque appel agent."""

from __future__ import annotations

import os
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Generator, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def get_langfuse():
    try:
        from langfuse import Langfuse

        public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        secret_key = os.getenv("LANGFUSE_SECRET_KEY")
        if not public_key or not secret_key:
            return None
        return Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
        )
    except Exception:
        return None


@contextmanager
def agent_trace(
    name: str,
    *,
    input: str | None = None,
    user_id: str = "emilie",
) -> Generator[Any, None, None]:
    """Context manager for a Langfuse v4 observation (replaces legacy trace())."""
    lf = get_langfuse()
    if not lf:
        yield None
        return

    from langfuse import propagate_attributes

    with propagate_attributes(user_id=user_id, trace_name=name):
        obs = lf.start_observation(name=name, as_type="span", input=input)
        try:
            yield obs
        finally:
            obs.end()
            lf.flush()


def trace_agent(agent_name: str):
    """Décorateur pour tracer les appels d'un agent."""

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any):
            trace_name = f"{agent_name}.{func.__name__}"
            with agent_trace(trace_name) as obs:
                try:
                    result = func(*args, **kwargs)
                    if obs:
                        obs.update(output=str(result)[:500])
                    return result
                except Exception as e:
                    if obs:
                        obs.update(output=f"ERROR: {e}", level="ERROR")
                    raise

        return wrapper  # type: ignore[return-value]

    return decorator
