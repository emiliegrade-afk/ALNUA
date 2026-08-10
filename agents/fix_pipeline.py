"""
fix_pipeline.py — Pipeline autonome de correction de bugs ALNUA.

Inspiré de AI Scientist (Sakana) + Hermes (Nous Research) :
- Itératif : jamais "impossible", juste "pas encore assez de contexte"
- Auto-apprenant : chaque tentative enrichit le journal
- Multi-agent : QA + Spec vérifient avant merge
- Auto-déploiement : détecte l'environnement et redémarre seul

Flow complet :
    bug_watchdog détecte erreur
        ↓
    fix_pipeline.run(error)
        ↓
    [Boucle itérative — contexte croissant à chaque retry]
    Tentative N : CodeAgent génère fix → pytest → QA review → Spec review
        ↓ (tout vert)
    Auto-merge main → Auto-deploy → Telegram ✅
        ↓ (persistance)
    Journal mis à jour → Mem0 → agents apprennent pour la prochaine fois
"""
from __future__ import annotations

from agents.fix_pipeline_constants import (  # noqa: F401 — re-export
    CONTEXT_LEVELS,
    FIX_MODEL,
    GITHUB_TOKEN,
    MAX_PIPELINE_ATTEMPTS,
    REVIEW_MODEL,
)
from agents.fix_pipeline_deploy import _detect_deploy_method  # noqa: F401 — re-export
from agents.fix_pipeline_llm import _llm  # noqa: F401 — re-export
from agents.fix_pipeline_reviews import _qa_review, _spec_review  # noqa: F401 — re-export
from agents.fix_pipeline_run import run

__all__ = [
    "CONTEXT_LEVELS",
    "FIX_MODEL",
    "GITHUB_TOKEN",
    "MAX_PIPELINE_ATTEMPTS",
    "REVIEW_MODEL",
    "_detect_deploy_method",
    "_llm",
    "_qa_review",
    "_spec_review",
    "run",
]
