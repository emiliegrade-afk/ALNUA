"""
BugWatchdog — Surveillance autonome des erreurs + auto-fix.

Flow :
1. Poll `agent_error_journal` toutes les 60s
2. Pour chaque erreur "open" :
   a. Cherche une solution connue dans l'historique
   b. Appelle skill_code_agent (LLM OpenRouter + gitpython) pour le fix
   c. Crée une PR GitHub si le fix réussit
   d. Notifie Emilie par Telegram
   e. Marque l'erreur resolved/escalated

100% in-house — aucune dépendance externe (pas Aider, pas OpenHands).
Stack : OpenRouter + gitpython + GitHub API.

Limites de sécurité :
- Max 3 tentatives par erreur avant escalade COO
- Pas de modif sur main directement — toujours une branche fix/
- Timeout LLM : 2 minutes
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Any

from config.agent_operating_spec import get_system_prompt

logger = logging.getLogger(__name__)

POLL_INTERVAL = int(os.getenv("WATCHDOG_POLL_INTERVAL", "60"))  # secondes
MAX_ATTEMPTS = int(os.getenv("WATCHDOG_MAX_ATTEMPTS", "3"))
WATCHDOG_ENABLED = os.getenv("WATCHDOG_ENABLED", "true").lower() not in (
    "0",
    "false",
    "no",
)
_stop_event: asyncio.Event | None = None

# Repos locaux par agent (pour OpenHands)
AGENT_REPO_PATHS: dict[str, str] = {
    "dev_app": os.getenv("REPO_PATH_NOMAD", "C:/Dev/nomad"),
    "dev_gaming": os.getenv("REPO_PATH_NAIA", "C:/Dev/naia"),
    "embedded": os.getenv("REPO_PATH_NAIA", "C:/Dev/naia"),
    "coo": os.getenv("HUB_REPO_PATH", "C:/Dev/ALUNA_HUB"),
    "pm_agent": os.getenv("HUB_REPO_PATH", "C:/Dev/ALUNA_HUB"),
    "qa_agent": os.getenv("HUB_REPO_PATH", "C:/Dev/ALUNA_HUB"),
    "spec_agent": os.getenv("HUB_REPO_PATH", "C:/Dev/ALUNA_HUB"),
}

DEFAULT_REPO_PATH = os.getenv("HUB_REPO_PATH", "C:/Dev/ALUNA_HUB")


# ---------------------------------------------------------------------------
# Génération du prompt de fix
# ---------------------------------------------------------------------------

def _build_fix_prompt(error: dict[str, Any], similar: list[dict]) -> str:
    """Génère le prompt utilisateur pour correction (system = spec 9 couches)."""
    agent = error.get("agent_name", "unknown")
    err_type = error.get("error_type", "unknown")
    err_msg = error.get("error_message", "")
    context = error.get("context", "")

    user = f"""ERREUR DÉTECTÉE :
- Agent : {agent}
- Type : {err_type}
- Message : {err_msg[:1000]}
- Contexte : {context[:500] if context else "non disponible"}
"""

    if similar:
        user += "\nSOLUTIONS CONNUES POUR DES ERREURS SIMILAIRES :\n"
        for s in similar[:2]:
            if s.get("solution"):
                user += f"- {s['solution'][:300]}\n"

    slug = err_type.replace(" ", "_").lower()[:30]
    user += f"""
INSTRUCTIONS :
1. Analyse l'erreur et localise le fichier/fonction concerné
2. Applique le fix minimal nécessaire (ne change rien d'autre)
3. Vérifie que les imports et dépendances sont corrects
4. Lance les tests si disponibles (pytest tests/ -x -q)
5. Crée une branche fix/{slug}_auto et commit le fix
6. Résume en 2 lignes ce que tu as changé et pourquoi

Ne fais PAS de refactoring, reste focalisé sur le bug précis.
"""
    return get_system_prompt("bug_watchdog_fix") + "\n\n---\n\n" + user


# ---------------------------------------------------------------------------
# Notification Telegram
# ---------------------------------------------------------------------------

async def _notify_telegram(message: str) -> None:
    """Envoie une notification Telegram à Emilie."""
    try:
        from api.telegram_bot import get_telegram_bot
        bot = get_telegram_bot()
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        if chat_id:
            await bot.bot.send_message(chat_id=int(chat_id), text=message)
    except Exception as exc:
        logger.warning("Telegram notification failed: %s", exc)


# ---------------------------------------------------------------------------
# Pipeline de fix
# ---------------------------------------------------------------------------

async def _process_error(error: dict[str, Any]) -> None:
    """
    Traite une erreur du journal via fix_pipeline.
    fix_pipeline gère lui-même les retries, les reviews et le merge.
    """
    from agents.fix_pipeline import run as pipeline_run

    error_id = error["id"]
    agent_name = error.get("agent_name", "unknown")
    err_type = error.get("error_type", "unknown")

    logger.info("BugWatchdog: délégation à fix_pipeline — %s (%s - %s)",
                error_id[:8], agent_name, err_type)

    # Registry-first repo resolution (multi-repo RUN recipe)
    repo_slug = error.get("repo_slug")
    try:
        from services.run_watchdog_registry import resolve_repo_path_for_slug

        repo_path, github_repo = resolve_repo_path_for_slug(repo_slug, agent_name)
    except Exception:
        repo_path = AGENT_REPO_PATHS.get(agent_name, DEFAULT_REPO_PATH)
        github_repo = None

    try:
        result = await pipeline_run(
            error=error,
            repo_path=repo_path,
            github_repo=github_repo,
        )
        if result.get("resolved"):
            logger.info("BugWatchdog: ✅ erreur %s résolue en %d tentative(s)",
                        error_id[:8], result.get("attempts", 1))
        else:
            logger.warning("BugWatchdog: pipeline terminé sans résolution pour %s", error_id[:8])
    except Exception as exc:
        logger.error("BugWatchdog: fix_pipeline crash inattendu: %s", exc)


# ---------------------------------------------------------------------------
# Boucle principale
# ---------------------------------------------------------------------------

async def watchdog_loop() -> None:
    """
    Boucle infinie : poll error_journal toutes les POLL_INTERVAL secondes.
    Lance un fix async pour chaque erreur ouverte.
    """
    from database.supabase_client import get_supabase

    logger.info("BugWatchdog: démarrage (poll toutes les %ds, max %d tentatives)",
                POLL_INTERVAL, MAX_ATTEMPTS)

    # Garde une trace des erreurs déjà en cours de traitement
    processing: set[str] = set()

    while True:
        if _stop_event is not None and _stop_event.is_set():
            logger.info("BugWatchdog: arrêt demandé")
            break
        try:
            db = get_supabase()
            result = (
                db.raw.table("agent_error_journal")
                .select("id, agent_name, error_type, error_message, context, attempts, created_at")
                .eq("status", "open")
                .order("created_at", desc=False)
                .limit(5)
                .execute()
            )
            errors = result.data or []

            for error in errors:
                error_id = error["id"]
                if error_id in processing:
                    continue
                if int(error.get("attempts") or 0) >= MAX_ATTEMPTS:
                    try:
                        from skills.skill_error_journal import mark_escalated

                        mark_escalated(error_id)
                        logger.info(
                            "BugWatchdog: erreur %s déjà à %d tentatives — escalade",
                            error_id[:8],
                            MAX_ATTEMPTS,
                        )
                    except Exception as exc:
                        logger.warning("BugWatchdog: escalade skip failed: %s", exc)
                    continue
                processing.add(error_id)

                async def _run_and_release(err: dict[str, Any], eid: str) -> None:
                    try:
                        await _process_error(err)
                    finally:
                        processing.discard(eid)

                asyncio.create_task(_run_and_release(error, error_id))

        except Exception as exc:
            logger.error("BugWatchdog: erreur lors du poll: %s", exc)

        await asyncio.sleep(POLL_INTERVAL)


def start_watchdog() -> None:
    """Démarre le watchdog comme tâche asyncio. Appelé depuis main.py lifespan."""
    if not WATCHDOG_ENABLED:
        logger.info("BugWatchdog: désactivé (WATCHDOG_ENABLED=false)")
        return
    global _stop_event
    _stop_event = asyncio.Event()
    try:
        asyncio.create_task(watchdog_loop())
        logger.info("BugWatchdog: tâche démarrée")
    except RuntimeError:
        # Pas de boucle event loop active (ex: test unitaire)
        logger.warning("BugWatchdog: pas de boucle event loop — watchdog non démarré")


def stop_watchdog() -> None:
    """Signal graceful stop (lifespan shutdown)."""
    if _stop_event is not None:
        _stop_event.set()
