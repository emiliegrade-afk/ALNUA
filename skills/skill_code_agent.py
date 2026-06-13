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

import json
import logging
import os
import urllib.request
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE = "https://openrouter.ai/api/v1/chat/completions"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
DEFAULT_AGENT_ID = "dev_app"


# ---------------------------------------------------------------------------
# LLM call direct (sans dépendance CrewAI)
# ---------------------------------------------------------------------------

def _default_model(agent_id: str = DEFAULT_AGENT_ID) -> str:
    from agents.base import resolve_openrouter_model

    return resolve_openrouter_model(agent_id)


def _llm(system: str, user: str, model: str | None = None, agent_id: str = DEFAULT_AGENT_ID) -> str:
    """Appel OpenRouter direct. Retourne le texte de la réponse."""
    resolved = model or _default_model(agent_id)
    payload = json.dumps({
        "model": resolved.replace("openrouter/", ""),
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.1,
        "max_tokens": 8000,
    }).encode()

    req = urllib.request.Request(
        OPENROUTER_BASE,
        data=payload,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.loads(r.read())
        return data["choices"][0]["message"]["content"]


# ---------------------------------------------------------------------------
# Git operations via gitpython
# ---------------------------------------------------------------------------

def _get_repo(repo_path: str):
    """Retourne un objet git.Repo. Installe gitpython si absent."""
    try:
        import git
        return git.Repo(repo_path)
    except ImportError:
        raise RuntimeError("gitpython non installé — lance : pip install gitpython")


def _create_branch(repo, branch_name: str) -> None:
    """Crée et checkout une branche depuis main."""
    try:
        origin = repo.remote("origin")
        origin.pull()
    except Exception:
        pass
    if branch_name in repo.heads:
        repo.delete_head(branch_name, force=True)
    branch = repo.create_head(branch_name)
    branch.checkout()


def _commit_and_push(repo, files_modified: list[str], message: str) -> bool:
    """Stage, commit et push les fichiers modifiés."""
    try:
        repo.index.add(files_modified)
        if not repo.index.diff("HEAD"):
            logger.info("Aucun changement à commiter")
            return False
        repo.index.commit(f"[auto-fix] {message[:72]}")
        origin = repo.remote("origin")
        origin.push(repo.active_branch.name)
        return True
    except Exception as exc:
        logger.error("Git commit/push failed: %s", exc)
        return False


# ---------------------------------------------------------------------------
# GitHub PR
# ---------------------------------------------------------------------------

def _create_pr(github_repo: str, branch: str, title: str, body: str) -> str | None:
    """Crée une PR GitHub. Retourne l'URL ou None."""
    if not GITHUB_TOKEN or not github_repo:
        return None
    payload = json.dumps({
        "title": title[:72],
        "body": body,
        "head": branch,
        "base": "main",
    }).encode()
    req = urllib.request.Request(
        f"https://api.github.com/repos/{github_repo}/pulls",
        data=payload,
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read()).get("html_url")
    except Exception as exc:
        logger.warning("PR creation failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Détection automatique des fichiers concernés
# ---------------------------------------------------------------------------

def _detect_files(error_message: str, repo_path: str, hint_files: list[str] | None) -> list[str]:
    """
    Trouve les fichiers Python probablement concernés par l'erreur.
    Priorité : hint_files > fichiers mentionnés dans l'erreur > recherche par mot-clé.
    """
    if hint_files:
        return [f for f in hint_files if Path(repo_path, f).exists()]

    found = []
    root = Path(repo_path)

    # Cherche les noms de fichiers mentionnés dans le stack trace
    import re
    for match in re.finditer(r'File "([^"]+\.py)"', error_message):
        fpath = Path(match.group(1))
        # Convertit en chemin relatif au repo
        try:
            rel = fpath.relative_to(root)
            found.append(str(rel))
        except ValueError:
            # Chemin absolu hors du repo — cherche par nom
            name = fpath.name
            for p in root.rglob(name):
                if ".git" not in str(p) and "node_modules" not in str(p):
                    found.append(str(p.relative_to(root)))
                    break

    return found[:5]  # Max 5 fichiers


# ---------------------------------------------------------------------------
# Point d'entrée principal
# ---------------------------------------------------------------------------

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

    # 1. Détecte les fichiers concernés
    files_to_fix = _detect_files(error_message, repo_path, hint_files)
    if not files_to_fix:
        return {
            "success": False,
            "summary": "Impossible de détecter les fichiers concernés par l'erreur.",
        }

    # 2. Lit le contenu des fichiers
    files_content = {}
    for rel_path in files_to_fix:
        full = Path(repo_path) / rel_path
        if full.exists():
            files_content[rel_path] = full.read_text(encoding="utf-8", errors="ignore")

    if not files_content:
        return {"success": False, "summary": "Fichiers introuvables dans le repo."}

    # 3. Construit le prompt de fix
    files_block = "\n\n".join(
        f"### {fname}\n```python\n{content[:4000]}\n```"
        for fname, content in files_content.items()
    )

    from skills.skill_agent_learning import get_learning_context, memory_agent_id

    canonical_id = memory_agent_id(agent_id)
    memory_block = get_learning_context(
        canonical_id, f"fix bug {error_message[:200]}"
    )

    # On demande UNE réponse structurée avec séparateurs clairs — plus fiable que JSON pur
    system_prompt = """Tu es un agent de correction de bugs expert Python pour ALNUA Hub.

RÈGLE : ta réponse doit suivre EXACTEMENT ce format, rien d'autre :

===SUMMARY===
Explication du fix en 1-2 phrases.
===FILE:chemin/relatif/fichier.py===
contenu complet du fichier corrigé ici
===END===

- Remplace chemin/relatif/fichier.py par le vrai chemin relatif du fichier
- Retourne le fichier COMPLET, pas juste le diff
- Fix minimal — ne change que ce qui est nécessaire
- Ajoute un commentaire # FIX: pourquoi sur la ligne corrigée"""

    user_prompt = f"""ERREUR :
{error_message[:1500]}

CONTEXTE :
{error_context[:500] if error_context else "non disponible"}
{memory_block}

FICHIERS CONCERNÉS :
{files_block}

Analyse et corrige le bug. Suis exactement le format demandé."""

    # dry_run = Phase 1 : retourne le prompt sans appliquer
    if dry_run:
        return {
            "success": True,
            "fixed_files": list(files_content.keys()),
            "pr_url": None,
            "summary": "Mode dry_run — prompt généré, non appliqué",
            "prompt": f"**Colle dans Cursor (Ctrl+K) :**\n\n{user_prompt[:2000]}",
        }

    # 4. Appelle le LLM
    try:
        raw_response = _llm(system_prompt, user_prompt, model, agent_id=agent_id)
    except Exception as exc:
        return {"success": False, "summary": f"Erreur LLM: {exc}"}

    # 5. Parse la réponse avec séparateurs ===SUMMARY=== / ===FILE:...=== / ===END===
    import re
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

    # 6. Applique les fichiers corrigés
    for rel_path, new_content in fixed_files.items():
        full_path = Path(repo_path) / rel_path
        if full_path.exists():
            full_path.write_text(new_content, encoding="utf-8")
            logger.info("Fixed: %s", rel_path)

    # 7. Commit + push + PR
    import re, time
    branch_name = f"fix/auto_{re.sub(r'[^\\w]', '_', error_message[:30].lower())}_{int(time.time()) % 10000}"

    pr_url = None
    try:
        repo = _get_repo(repo_path)
        _create_branch(repo, branch_name)
        # Re-applique les fichiers sur la nouvelle branche
        for rel_path, new_content in fixed_files.items():
            (Path(repo_path) / rel_path).write_text(new_content, encoding="utf-8")
        committed = _commit_and_push(repo, list(fixed_files.keys()), fix_summary)
        if committed and github_repo:
            pr_url = _create_pr(
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
