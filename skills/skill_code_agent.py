"""
skill_code_agent.py — Moteur de codage interne ALNUA.

Remplace Aider/OpenHands. Utilise directement OpenRouter + gitpython.
Aucune dépendance externe — tout dans le stack ALNUA.

Flow :
    1. Lit les fichiers concernés
    2. Envoie au LLM avec le contexte complet
    3. Applique le fichier corrigé
    4. Commit + push sur branche fix/
    5. Crée la PR GitHub

Dépendance unique à installer : pip install gitpython
"""
from __future__ import annotations

import logging
import re
import time
from pathlib import Path
from typing import Any

from config.agent_operating_spec import get_system_prompt
from skills.skill_code_agent_git import (
    commit_and_push,
    create_branch,
    create_pr,
    detect_files,
    get_repo,
)

logger = logging.getLogger(__name__)

DEFAULT_AGENT_ID = "dev_app"


def _llm(system: str, user: str, model: str | None = None, agent_id: str = DEFAULT_AGENT_ID) -> str:
    """OpenRouter via LLMClient — costs, retries, prompt-cache included."""
    from agents.base import LLMClient

    return LLMClient().complete(
        system,
        user,
        model=model,
        agent_id=agent_id,
        method_name="fix_bug",
        temperature=0.1,
        max_tokens=8000,
    )


def fix_bug(
    error_message: str,
    error_context: str = "",
    repo_path: str = "",
    github_repo: str | None = None,
    hint_files: list[str] | None = None,
    model: str | None = None,
    agent_id: str = DEFAULT_AGENT_ID,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Fix automatique d'un bug. Point d'entrée du BugWatchdog.

    Args:
        error_message : Le message d'erreur complet
        error_context : Contexte supplémentaire (agent, tâche)
        repo_path     : Chemin local du repo
        github_repo   : Slug GitHub pour la PR (ex: emiliegrade-afk/ALNUA)
        hint_files    : Fichiers à modifier (auto-détecté si None)
        model         : Modèle LLM à utiliser
        dry_run       : Si True, retourne le fix sans l'appliquer (Phase 1)

    Returns:
        {
            "success": bool,
            "fixed_files": list[str],
            "pr_url": str | None,
            "summary": str,
            "prompt": str  (si dry_run=True)
        }
    """
    if not repo_path or not Path(repo_path).exists():
        return {"success": False, "summary": f"Repo path invalide: {repo_path}"}

    files_to_fix = detect_files(error_message, repo_path, hint_files)
    if not files_to_fix:
        return {
            "success": False,
            "summary": "Impossible de détecter les fichiers concernés par l'erreur.",
        }

    files_content = {}
    for rel_path in files_to_fix:
        full = Path(repo_path) / rel_path
        if full.exists():
            files_content[rel_path] = full.read_text(encoding="utf-8", errors="ignore")

    if not files_content:
        return {"success": False, "summary": "Fichiers introuvables dans le repo."}

    files_block = "\n\n".join(
        f"### {fname}\n```python\n{content[:4000]}\n```"
        for fname, content in files_content.items()
    )

    from skills.skill_agent_learning import get_learning_context, memory_agent_id

    canonical_id = memory_agent_id(agent_id)
    memory_block = get_learning_context(
        canonical_id, f"fix bug {error_message[:200]}"
    )

    system_prompt = get_system_prompt("code_agent_bug_fix")

    user_prompt = f"""ERREUR :
{error_message[:1500]}

CONTEXTE :
{error_context[:500] if error_context else "non disponible"}
{memory_block}

FICHIERS CONCERNÉS :
{files_block}

Analyse et corrige le bug. Suis exactement le format demandé."""

    if dry_run:
        return {
            "success": True,
            "fixed_files": list(files_content.keys()),
            "pr_url": None,
            "summary": "Mode dry_run — prompt généré, non appliqué",
            "prompt": f"**Colle dans Cursor (Ctrl+K) :**\n\n{user_prompt[:2000]}",
        }

    try:
        raw_response = _llm(system_prompt, user_prompt, model, agent_id=agent_id)
    except Exception as exc:
        return {"success": False, "summary": f"Erreur LLM: {exc}"}

    text = raw_response.strip()

    summary_match = re.search(r'===SUMMARY===\s*(.*?)\s*(?:===FILE:|$)', text, re.DOTALL)
    fix_summary = summary_match.group(1).strip() if summary_match else "Fix appliqué"

    fixed_files = {}
    for filepath, content in re.findall(r'===FILE:([^\n=]+)===\s*(.*?)\s*===END===', text, re.DOTALL):
        filepath = filepath.strip()
        content = re.sub(r'^```\w*\n?', '', content.strip())
        content = re.sub(r'\n?```$', '', content).strip()
        if filepath and content:
            fixed_files[filepath] = content

    if not fixed_files:
        logger.debug("Réponse LLM brute : %s", raw_response[:800])
        return {"success": False, "summary": f"LLM n'a pas retourné de fichier corrigé. Résumé: {fix_summary[:200]}"}

    for rel_path, new_content in fixed_files.items():
        full_path = Path(repo_path) / rel_path
        if full_path.exists():
            full_path.write_text(new_content, encoding="utf-8")
            logger.info("Fixed: %s", rel_path)

    branch_name = f"fix/auto_{re.sub(r'[^\\w]', '_', error_message[:30].lower())}_{int(time.time()) % 10000}"

    pr_url = None
    try:
        repo = get_repo(repo_path)
        create_branch(repo, branch_name)
        for rel_path, new_content in fixed_files.items():
            (Path(repo_path) / rel_path).write_text(new_content, encoding="utf-8")
        committed = commit_and_push(repo, list(fixed_files.keys()), fix_summary)
        if committed and github_repo:
            pr_url = create_pr(
                github_repo=github_repo,
                branch=branch_name,
                title=f"[Auto-fix] {fix_summary[:60]}",
                body=(
                    f"## Fix automatique ALNUA\n\n"
                    f"**Erreur :** {error_message[:300]}\n\n"
                    f"**Fix :** {fix_summary}\n\n"
                    f"**Fichiers modifiés :** {', '.join(fixed_files.keys())}\n\n"
                    f"*Généré automatiquement par skill_code_agent.*"
                ),
            )
    except Exception as exc:
        logger.error("Git/PR failed: %s", exc)

    return {
        "success": True,
        "fixed_files": list(fixed_files.keys()),
        "pr_url": pr_url,
        "summary": fix_summary,
        "branch": branch_name,
    }


def generate_fix_prompt(error_message: str, repo_path: str, hint_files: list[str] | None = None) -> str:
    """
    Phase 1 — génère uniquement le prompt à coller dans Cursor.
    Sans LLM call, sans git. Juste le contexte formaté.
    """
    result = fix_bug(
        error_message=error_message,
        repo_path=repo_path,
        hint_files=hint_files,
        dry_run=True,
    )
    return result.get("prompt", "Erreur génération prompt")
