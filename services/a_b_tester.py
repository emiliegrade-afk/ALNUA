"""
services/a_b_tester.py — A/B test de prompts et d'agents ALNUA.

Inspiré de prompt-optimizer (⭐2.1k). Compare deux variants (prompt, agent,
ou paramètres) sur un même batch d'inputs. Un LLM juge impartialement le gagnant.

Cas d'usage :
- Comparer deux versions du SYSTEM_PROMPT d'un agent
- Tester temperature 0.3 vs 0.7 sur la même tâche
- Comparer deux agents (ex: brainstorm vs rnd_agent) sur la même question

Usage:
    from services.a_b_tester import run_ab_test, ABTestConfig

    result = run_ab_test(
        config=ABTestConfig(
            name="Marketing post LinkedIn",
            variant_a={"agent_id": "content", "method": "handle_instruction",
                       "kwargs": {"instruction": "Écris un post LinkedIn sur le ML"}},
            variant_b={"agent_id": "marketing", "method": "handle_instruction",
                       "kwargs": {"instruction": "Écris un post LinkedIn sur le ML"}},
            judge_criteria="Lequel est le plus engageant et professionnel ?",
            runs_per_variant=3,
        )
    )
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

_JUDGE_SYSTEM = """Tu es un évaluateur expert et impartial. On te présente deux réponses (A et B)
à la même tâche. Tu les évalues selon les critères donnés et tu désignes un gagnant.
Réponds en JSON valide uniquement."""


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class ABVariant:
    agent_id: str
    method: str
    kwargs: dict[str, Any] = field(default_factory=dict)
    label: str = ""  # "Variant A" par défaut


@dataclass
class ABTestConfig:
    name: str
    variant_a: dict[str, Any]   # ABVariant-compatible dict
    variant_b: dict[str, Any]
    judge_criteria: str = "Lequel est le plus utile, précis et bien structuré ?"
    runs_per_variant: int = 1   # moyenne sur N runs
    judge_agent_id: str = "qa"  # Sven juge par défaut


@dataclass
class RunResult:
    variant: str   # "A" | "B"
    agent_id: str
    method: str
    result: Any
    cost_ms: int
    success: bool
    error: str = ""


@dataclass
class ABTestResult:
    name: str
    winner: str   # "A" | "B" | "tie"
    confidence: float
    judge_reasoning: str
    variant_a_label: str
    variant_b_label: str
    runs_a: list[RunResult] = field(default_factory=list)
    runs_b: list[RunResult] = field(default_factory=list)
    duration_ms: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "winner": self.winner,
            "confidence": self.confidence,
            "judge_reasoning": self.judge_reasoning,
            "variant_a": {
                "label": self.variant_a_label,
                "success_rate": sum(1 for r in self.runs_a if r.success) / max(1, len(self.runs_a)),
                "avg_ms": sum(r.cost_ms for r in self.runs_a) // max(1, len(self.runs_a)),
                "results": [r.result for r in self.runs_a if r.success],
            },
            "variant_b": {
                "label": self.variant_b_label,
                "success_rate": sum(1 for r in self.runs_b if r.success) / max(1, len(self.runs_b)),
                "avg_ms": sum(r.cost_ms for r in self.runs_b) // max(1, len(self.runs_b)),
                "results": [r.result for r in self.runs_b if r.success],
            },
            "total_duration_ms": self.duration_ms,
        }


# ---------------------------------------------------------------------------
# Exécution
# ---------------------------------------------------------------------------

def _run_variant(variant_dict: dict, variant_label: str, runs: int) -> list[RunResult]:
    """Exécute un variant N fois et retourne les résultats."""
    from services.parallel_runner import _get_agent_method

    agent_id = variant_dict.get("agent_id", "")
    method_name = variant_dict.get("method", "")
    kwargs = variant_dict.get("kwargs", {})

    results = []
    for _ in range(runs):
        start = time.monotonic()
        try:
            method = _get_agent_method(agent_id, method_name)
            result = method(**kwargs)
            results.append(RunResult(
                variant=variant_label, agent_id=agent_id, method=method_name,
                result=result, cost_ms=int((time.monotonic() - start) * 1000),
                success=True,
            ))
        except Exception as e:
            results.append(RunResult(
                variant=variant_label, agent_id=agent_id, method=method_name,
                result=None, cost_ms=int((time.monotonic() - start) * 1000),
                success=False, error=str(e),
            ))
    return results


def _judge_results(
    runs_a: list[RunResult],
    runs_b: list[RunResult],
    config: ABTestConfig,
) -> dict[str, Any]:
    """LLM juge les outputs A vs B selon les critères."""
    from agents.base import LLMClient, parse_json_response

    # Prend le meilleur résultat de chaque variant (premier succès)
    best_a = next((r.result for r in runs_a if r.success), "ÉCHEC — aucun résultat")
    best_b = next((r.result for r in runs_b if r.success), "ÉCHEC — aucun résultat")

    label_a = config.variant_a.get("label") or f"{config.variant_a.get('agent_id')}.{config.variant_a.get('method')}"
    label_b = config.variant_b.get("label") or f"{config.variant_b.get('agent_id')}.{config.variant_b.get('method')}"

    llm = LLMClient()
    prompt = f"""Test A/B : {config.name}

CRITÈRES D'ÉVALUATION : {config.judge_criteria}

--- RÉPONSE A ({label_a}) ---
{str(best_a)[:2000]}

--- RÉPONSE B ({label_b}) ---
{str(best_b)[:2000]}

Évalue les deux réponses et réponds avec :
- winner: "A" | "B" | "tie"
- confidence: float 0-1 (1 = certitude absolue)
- score_a: float 0-10
- score_b: float 0-10
- strengths_a: list[str] — points forts de A
- strengths_b: list[str] — points forts de B
- reasoning: string — explication courte de ta décision"""

    try:
        raw = llm.complete(_JUDGE_SYSTEM, prompt, agent_id=config.judge_agent_id, temperature=0.1)
        return parse_json_response(raw)
    except Exception as e:
        logger.error(f"AB test judge failed: {e}")
        return {
            "winner": "tie", "confidence": 0.0,
            "score_a": 5.0, "score_b": 5.0,
            "reasoning": f"Jugement impossible: {e}",
            "strengths_a": [], "strengths_b": [],
        }


# ---------------------------------------------------------------------------
# API principale
# ---------------------------------------------------------------------------

def run_ab_test(config: ABTestConfig) -> dict[str, Any]:
    """
    Lance un A/B test complet : exécute les variants en parallèle → juge.
    Endpoint: POST /services/ab-test/run
    """
    import concurrent.futures

    start = time.monotonic()
    label_a = config.variant_a.get("label") or "Variant A"
    label_b = config.variant_b.get("label") or "Variant B"

    logger.info(f"A/B test '{config.name}': {label_a} vs {label_b} ({config.runs_per_variant} runs each)")

    # Exécuter A et B en parallèle
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_a = executor.submit(_run_variant, config.variant_a, "A", config.runs_per_variant)
        future_b = executor.submit(_run_variant, config.variant_b, "B", config.runs_per_variant)
        runs_a = future_a.result()
        runs_b = future_b.result()

    # Juger
    judgment = _judge_results(runs_a, runs_b, config)

    result = ABTestResult(
        name=config.name,
        winner=judgment.get("winner", "tie"),
        confidence=judgment.get("confidence", 0.0),
        judge_reasoning=judgment.get("reasoning", ""),
        variant_a_label=label_a,
        variant_b_label=label_b,
        runs_a=runs_a,
        runs_b=runs_b,
        duration_ms=int((time.monotonic() - start) * 1000),
    )

    output = result.to_dict()
    output["judgment"] = judgment

    # Points compétition au gagnant
    try:
        from services.competition import add_points
        winner_agent = (
            config.variant_a.get("agent_id") if result.winner == "A"
            else config.variant_b.get("agent_id") if result.winner == "B"
            else None
        )
        if winner_agent:
            add_points(winner_agent, "task_validated", note=f"A/B winner: {config.name[:40]}")
    except Exception:
        pass

    return output


def quick_compare(
    agent_id: str,
    method: str,
    kwargs_a: dict[str, Any],
    kwargs_b: dict[str, Any],
    criteria: str = "Lequel est le meilleur résultat ?",
) -> dict[str, Any]:
    """
    Compare deux sets de kwargs sur le même agent/méthode.
    Utile pour tester des paramètres (temperature, tone, etc.)
    Endpoint: POST /services/ab-test/quick-compare
    """
    config = ABTestConfig(
        name=f"{agent_id}.{method} params comparison",
        variant_a={"agent_id": agent_id, "method": method, "kwargs": kwargs_a, "label": "Params A"},
        variant_b={"agent_id": agent_id, "method": method, "kwargs": kwargs_b, "label": "Params B"},
        judge_criteria=criteria,
        runs_per_variant=1,
    )
    return run_ab_test(config)
