"""Distill lessons from task outcomes and persist them to Mem0."""
from __future__ import annotations

import json
import logging
import threading
import urllib.request
from datetime import datetime

from config.agent_models import memory_agent_id

from skills.skill_agent_learning_constants import (
    DEFAULT_LENS,
    LEARN_MODEL,
    LEARNING_LENS,
    OPENROUTER_BASE,
    _FAILURE_MARKERS,
    openrouter_api_key,
)

logger = logging.getLogger(__name__)


def _get_lens(agent_id: str) -> str:
    """Résout la lentille d'apprentissage (clé canonique ou legacy *_agent)."""
    aid = memory_agent_id(agent_id)
    if aid in LEARNING_LENS:
        return LEARNING_LENS[aid]
    if aid == "accounting":
        return LEARNING_LENS.get("accounting", LEARNING_LENS.get("accountant_agent", DEFAULT_LENS))
    legacy = f"{aid}_agent"
    if legacy in LEARNING_LENS:
        return LEARNING_LENS[legacy]
    if agent_id in LEARNING_LENS:
        return LEARNING_LENS[agent_id]
    return DEFAULT_LENS


def record_task_learning(
    agent_id: str,
    task: str,
    outcome: str,
    *,
    success: bool | None = None,
) -> None:
    """Enregistre une leçon après tâche (succès auto-détecté si non fourni)."""
    learn_from_outcome(
        agent_id=agent_id,
        task=task,
        outcome=outcome,
        success=success if success is not None else not is_task_failure(outcome),
    )


def is_task_failure(outcome: str) -> bool:
    """Heuristique : détecte un échec dans la sortie texte d'un agent."""
    text = str(outcome).lower()
    return any(marker in text for marker in _FAILURE_MARKERS)


def _distill_lessons(agent_id: str, task: str, outcome: str, success: bool) -> str:
    """
    Appelle le LLM pour distiller 1-2 leçons concrètes depuis le résultat d'une tâche.
    Retourne une leçon en 2-3 phrases max.
    """
    lens = _get_lens(agent_id)
    status = "réussie" if success else "échouée"

    system = f"""{lens}
Après chaque tâche, tu distilles UNE leçon concrète et actionnable.
Réponds en 2-3 phrases max. Pas de bullet points. Pas d'intro.
Format : "[Leçon] Ce que j'ai appris et comment je l'appliquerai la prochaine fois."
Sois spécifique — pas de généralités."""

    user = f"""Tâche ({status}) : {task[:400]}

Résultat : {outcome[:600]}

Quelle est la leçon concrète à retenir pour être plus efficace la prochaine fois ?"""

    model = (LEARN_MODEL or "anthropic/claude-haiku-4-5").replace("openrouter/", "")
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.3,
        "max_tokens": 200,
    }).encode()

    req = urllib.request.Request(
        OPENROUTER_BASE,
        data=payload,
        headers={
            "Authorization": f"Bearer {openrouter_api_key()}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
            content = data["choices"][0]["message"].get("content") or ""
            return content.strip()
    except Exception as exc:
        logger.warning("skill_agent_learning: LLM call failed: %s", exc)
        return ""


def learn_from_outcome(
    agent_id: str,
    task: str,
    outcome: str,
    success: bool = True,
    blocking: bool = False,
    tag: str = "",
) -> None:
    """
    Point d'entrée principal. À appeler après chaque tâche complétée.

    L'apprentissage tourne en arrière-plan — l'agent n'attend pas (sauf blocking=True).
    """
    canonical_id = memory_agent_id(agent_id)

    def _run():
        try:
            lesson = _distill_lessons(canonical_id, task, outcome, success)
            if not lesson:
                return

            from skills.skill_mem0 import remember

            date = datetime.now().strftime("%Y-%m-%d")
            status_tag = "✅" if success else "⚠️"
            prefix = f"{tag} " if tag else ""
            memory_entry = (
                f"{prefix}{status_tag} [{date}] Apprentissage {canonical_id} : {lesson}"
            )
            remember(memory_entry, agent_id=canonical_id)
            logger.info("skill_agent_learning: leçon enregistrée pour %s", canonical_id)
            try:
                from services.collective_learning import record_lesson_candidate

                record_lesson_candidate(canonical_id, lesson, task=task)
            except Exception:
                pass

        except Exception as exc:
            logger.warning("skill_agent_learning: échec apprentissage %s: %s", agent_id, exc)

    if blocking:
        _run()
    else:
        threading.Thread(target=_run, daemon=True).start()


def learn_from_failure(agent_id: str, task: str, error: str) -> None:
    """Raccourci pour enregistrer un échec. L'agent apprend aussi de ses erreurs."""
    learn_from_outcome(
        agent_id=agent_id,
        task=task,
        outcome=f"ÉCHEC : {error}",
        success=False,
    )
