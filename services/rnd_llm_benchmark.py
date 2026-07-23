"""
LLM latency benchmark — OpenRouter (live) vs DiffusionGemma (reference).

Runs short Hub-like prompts on OpenRouter and compares wall-clock latency
to published DiffusionGemma figures (local inference not required).
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from typing import Any

from config.paths import data_dir

logger = logging.getLogger(__name__)

BENCHMARK_FILE = data_dir("rnd_llm_benchmarks.json")

# Hub-realistic micro-tasks (ack, tri, JSON court)
DEFAULT_PROMPTS: tuple[str, ...] = (
    "Accusé Telegram en 1 phrase pour : « lance une recherche R&D robotique ».",
    "Classe cette demande (email|calendar|research|coding) : « mes mails urgents ».",
    'Réponds uniquement en JSON : {"intent":"research","topic":"robotique"}',
)

# Published DiffusionGemma reference (Google / vLLM, batch=1, Jun 2026)
DIFFUSION_GEMMA_REFERENCE: dict[str, Any] = {
    "model": "DiffusionGemma",
    "license": "Apache-2.0",
    "published_tokens_per_second_h100": 1008,
    "published_tokens_per_second_rtx5090": 700,
    "parallel_block_size": 256,
    "local_executable": False,
    "note": (
        "Référence Google DeepMind — non exécuté sur ce Hub. "
        "À benchmarker localement quand le 2e SSD + GPU sont prêts (Ollama/vLLM)."
    ),
    "url": "https://deepmind.google/models/gemma/diffusiongemma/",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_history() -> list[dict[str, Any]]:
    if not BENCHMARK_FILE.exists():
        return []
    try:
        data = json.loads(BENCHMARK_FILE.read_text(encoding="utf-8"))
        return data.get("runs") or []
    except Exception:
        return []


def _save_run(entry: dict[str, Any]) -> None:
    history = _load_history()
    history.insert(0, entry)
    BENCHMARK_FILE.parent.mkdir(parents=True, exist_ok=True)
    BENCHMARK_FILE.write_text(
        json.dumps({"runs": history[:30]}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def get_latest_benchmark() -> dict[str, Any] | None:
    runs = _load_history()
    return runs[0] if runs else None


def run_llm_latency_benchmark(
    *,
    agent_id: str = "secretary",
    prompts: list[str] | None = None,
    max_tokens: int = 120,
) -> dict[str, Any]:
    """Benchmark OpenRouter latency on short Hub tasks."""
    from agents.base import LLMClient, resolve_openrouter_model

    model = resolve_openrouter_model(agent_id)
    llm = LLMClient()
    system = "Tu es Nadia, secrétaire ALNUA. Réponds de façon concise."

    test_prompts = prompts or list(DEFAULT_PROMPTS)
    runs: list[dict[str, Any]] = []

    for i, prompt in enumerate(test_prompts[:5]):
        start = time.perf_counter()
        error: str | None = None
        output = ""
        try:
            output = llm.complete(
                system,
                prompt,
                agent_id=agent_id,
                temperature=0.2,
                max_tokens=max_tokens,
            )
        except Exception as exc:
            error = str(exc)[:200]
        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
        approx_tokens = max(1, len(output.split())) if output else 0
        tps = round(approx_tokens / (elapsed_ms / 1000), 1) if elapsed_ms > 0 and approx_tokens else 0

        runs.append(
            {
                "prompt_index": i,
                "prompt_preview": prompt[:80],
                "elapsed_ms": elapsed_ms,
                "approx_output_tokens": approx_tokens,
                "tokens_per_second": tps,
                "error": error,
            }
        )

    successful = [r for r in runs if not r.get("error")]
    avg_ms = (
        round(sum(r["elapsed_ms"] for r in successful) / len(successful), 1)
        if successful
        else None
    )
    avg_tps = (
        round(sum(r["tokens_per_second"] for r in successful) / len(successful), 1)
        if successful
        else None
    )

    ref_tps = DIFFUSION_GEMMA_REFERENCE["published_tokens_per_second_rtx5090"]
    speedup_factor = round(ref_tps / avg_tps, 1) if avg_tps and avg_tps > 0 else None

    recommendation = _build_recommendation(avg_ms, avg_tps, speedup_factor)

    entry = {
        "id": f"bench_{int(time.time())}",
        "ran_at": _utc_now(),
        "agent_id": agent_id,
        "model": model,
        "openrouter": {
            "runs": runs,
            "avg_elapsed_ms": avg_ms,
            "avg_tokens_per_second": avg_tps,
        },
        "diffusion_gemma_reference": DIFFUSION_GEMMA_REFERENCE,
        "comparison": {
            "diffusion_gemma_estimated_speedup_vs_openrouter": speedup_factor,
            "use_diffusion_gemma_for": [
                "Ack Telegram instantané",
                "Résumés 1-2 phrases",
                "JSON intents courts",
            ],
            "keep_openrouter_for": [
                "Dossiers R&D complets",
                "Deep research multi-rounds",
                "Comité multi-agents",
            ],
        },
        "recommendation": recommendation,
    }
    _save_run(entry)
    return entry


def _build_recommendation(
    avg_ms: float | None,
    avg_tps: float | None,
    speedup: float | None,
) -> str:
    if avg_ms is None:
        return "Benchmark OpenRouter échoué — vérifie OPENROUTER_API_KEY."
    parts = [f"OpenRouter répond en ~{avg_ms:.0f} ms en moyenne sur tâches courtes."]
    if speedup:
        parts.append(
            f"DiffusionGemma (réf. RTX 5090) serait ~{speedup}× plus rapide en tokens/s "
            "pour l'inférence locale single-user."
        )
    parts.append(
        "Phase 2 SSD : tester DiffusionGemma pour Nadia PC (ack + tri) ; "
        "garder OpenRouter pour R&D et dossiers."
    )
    return " ".join(parts)
