"""Monitoring LLM via Langfuse — trace chaque appel agent."""

from __future__ import annotations

import os
from functools import wraps
from typing import Any, Callable, TypeVar

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


def trace_agent(agent_name: str):
    """Décorateur pour tracer les appels d'un agent."""

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any):
            lf = get_langfuse()
            if not lf:
                return func(*args, **kwargs)
            trace = lf.trace(name=f"{agent_name}.{func.__name__}", user_id="emilie")
            try:
                result = func(*args, **kwargs)
                trace.update(output=str(result)[:500])
                return result
            except Exception as e:
                trace.update(output=f"ERROR: {e}", level="ERROR")
                raise
            finally:
                lf.flush()

        return wrapper  # type: ignore[return-value]

    return decorator
