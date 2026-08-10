"""Multi-agent QA and Spec reviews for fix_pipeline."""
from __future__ import annotations

import json
import logging
import re
from typing import Any

from config.agent_operating_spec import get_system_prompt

logger = logging.getLogger(__name__)


def _qa_review(diff: str, error_message: str, fix_summary: str) -> dict[str, Any]:
    """
    QA Agent — vérifie que le fix est logiquement correct.
    Retourne {"approved": bool, "feedback": str}
    """
    system = get_system_prompt("fix_pipeline_qa_review")

    user = f"""ERREUR ORIGINALE :
{error_message[:800]}

FIX APPLIQUÉ (résumé) :
{fix_summary}

DIFF :
{diff[:3000]}

Ce fix résout-il correctement l'erreur sans introduire de nouveaux problèmes ?"""

    try:
        from agents import fix_pipeline as fp

        raw = fp._llm(system, user)
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            return json.loads(m.group())
    except Exception as exc:
        logger.warning("QA review failed: %s", exc)
    return {"approved": False, "feedback": "Review impossible — fix non approuvé par précaution."}


def _spec_review(diff: str, fix_summary: str, repo_context: str) -> dict[str, Any]:
    """
    Spec Agent — vérifie cohérence architecturale.
    Retourne {"approved": bool, "feedback": str}
    """
    system = get_system_prompt("fix_pipeline_spec_review")

    user = f"""CONTEXTE PROJET :
{repo_context[:1000]}

FIX APPLIQUÉ :
{fix_summary}

DIFF :
{diff[:2000]}

Le fix respecte-t-il l'architecture et les conventions du projet ?"""

    try:
        from agents import fix_pipeline as fp

        raw = fp._llm(system, user)
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            return json.loads(m.group())
    except Exception as exc:
        logger.warning("Spec review failed: %s", exc)
    return {"approved": False, "feedback": "Review impossible — fix non approuvé par précaution."}
