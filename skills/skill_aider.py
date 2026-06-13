"""
skill_aider.py — Agent de codage autonome via Aider.

Aider est l'équivalent open source de Cursor, pilotable par les agents.
Il lit le repo, comprend le contexte, applique les diffs et commite.

Flow typique :
    1. spec_agent génère le message de fix
    2. skill_aider applique le fix sur une branche dédiée
    3. skill_aider crée la PR GitHub
    4. Telegram notifie Emilie

Modèles supportés via OpenRouter :
    - openrouter/anthropic/claude-sonnet-4-5 (défaut)
    - openrouter/minimax/minimax-m1
    - openrouter/openai/gpt-4o
"""
from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

# Modèle utilisé par Aider (via OpenRouter)
DEFAULT_MODEL = os.getenv("AIDER_MODEL", "openrouter/anthropic/claude-sonnet-4-5")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")


def _git(args: list[str], cwd: str) -> tuple[bool, str]:
    """Exécute une commande git. Retourne (success, output)."""
    try:
        r = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return r.returncode == 0, (r.stdout + r.stderr).strip()
    except Exception as exc:
        return False, str(exc)


def _create_fix_branch(repo_path: str, branch_name: str) -> bool:
    """Crée et checkout une branche de fix."""
    # S'assure d'être sur main/master
    _git(["checkout", "main"], repo_path)
    _git(["pull", "origin", "main"], repo_path)
    # Crée la branche
    ok, out = _git(["checkout", "-b", branch_name], repo_path)
    if not ok:
        logger.warning("Branch creation failed: %s", out)
    return ok


def _push_and_create_pr(
    repo_path: str,
    branch_name: str,
    pr_title: str,
    pr_body: str,
    github_repo: str,
) -> str | None:
    """Push la branche et crée une PR GitHub. Retourne l'URL de la PR ou None."""
    import json
    import urllib.request

    # Push
    ok, out = _git(["push", "-u", "origin", branch_name], repo_path)
    if not ok:
        logger.warning("Push failed: %s", out)
        return None

    # Crée la PR via GitHub API
    if not GITHUB_TOKEN or not github_repo:
        return None

    payload = json.dumps({
        "title": pr_title,
        "body": pr_body,
        "head": branch_name,
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
            data = json.loads(r.read())
            return data.get("html_url")
    except Exception as exc:
        logger.warning("PR creation failed: %s", exc)
        return None


def run_aider_fix(
    message: str,
    repo_path: str,
    files: list[str] | None = None,
    branch_name: str | None = None,
    github_repo: str | None = None,
    model: str | None = None,
    auto_commit: bool = True,
    create_pr: bool = True,
) -> dict:
    """
    Lance Aider pour appliquer un fix, commit et créer une PR.

    Args:
        message     : Description du fix en langage naturel
        repo_path   : Chemin local du repo (ex: C:/Dev/ALUNA_HUB)
        files       : Fichiers spécifiques à modifier (optionnel — Aider cherche tout seul)
        branch_name : Nom de la branche fix (auto-généré si None)
        github_repo : Slug GitHub ex: emiliegrade-afk/ALNUA (pour la PR)
        model       : Modèle LLM (défaut: DEFAULT_MODEL)
        auto_commit : Commite automatiquement (True recommandé)
        create_pr   : Crée une PR GitHub après le fix

    Returns:
        {
            "success": bool,
            "output": str,
            "branch": str | None,
            "pr_url": str | None,
        }
    """
    model = model or DEFAULT_MODEL
    repo_path = str(Path(repo_path).resolve())

    # Crée la branche de fix
    if not branch_name:
        import re, time
        slug = re.sub(r"[^\w]", "_", message[:40].lower())
        branch_name = f"fix/auto_{slug}_{int(time.time()) % 10000}"

    if auto_commit:
        _create_fix_branch(repo_path, branch_name)

    # Construit la commande Aider
    cmd = [
        "aider",
        "--model", model,
        "--yes",                    # Pas de confirmation interactive
        "--message", message,
    ]

    if auto_commit:
        cmd += ["--auto-commits"]   # Commit chaque modification
    else:
        cmd += ["--no-auto-commits"]

    if files:
        cmd += files

    # Variables d'environnement pour OpenRouter
    env = os.environ.copy()
    env["OPENROUTER_API_KEY"] = OPENROUTER_API_KEY
    env["OPENAI_API_KEY"] = OPENROUTER_API_KEY  # Aider utilise le nom OpenAI
    env["OPENAI_API_BASE"] = "https://openrouter.ai/api/v1"

    logger.info("Aider: démarrage fix sur %s (branche: %s)", repo_path, branch_name)

    try:
        result = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=300,
            env=env,
        )
        success = result.returncode == 0
        output = (result.stdout[-3000:] if success else result.stderr[-1500:]).strip()

        pr_url = None
        if success and create_pr and github_repo:
            pr_url = _push_and_create_pr(
                repo_path=repo_path,
                branch_name=branch_name,
                pr_title=f"[Auto-fix] {message[:72]}",
                pr_body=(
                    f"## Fix automatique par ALNUA Hub\n\n"
                    f"**Message :** {message}\n\n"
                    f"**Output Aider :**\n```\n{output[:1000]}\n```\n\n"
                    f"*Généré automatiquement par spec_agent + Aider.*"
                ),
                github_repo=github_repo,
            )

        logger.info("Aider: %s (PR: %s)", "✅ succès" if success else "❌ échec", pr_url)
        return {
            "success": success,
            "output": output,
            "branch": branch_name if success else None,
            "pr_url": pr_url,
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": "Timeout 5min — fix trop complexe, escalade COO",
            "branch": None,
            "pr_url": None,
        }
    except FileNotFoundError:
        return {
            "success": False,
            "output": "Aider non installé. Lance : pip install aider-chat",
            "branch": None,
            "pr_url": None,
        }
    except Exception as exc:
        return {"success": False, "output": str(exc), "branch": None, "pr_url": None}


def run_aider_prompt_only(
    message: str,
    repo_path: str,
    files: list[str] | None = None,
) -> str:
    """
    Mode Phase 1 : génère le prompt Cursor/Aider sans l'exécuter.
    Utile quand Emilie veut review avant d'appliquer.

    Retourne le prompt formaté prêt à coller dans Cursor.
    """
    file_list = "\n".join(f"- {f}" for f in (files or ["(Aider détecte automatiquement]"]))
    return (
        f"## Prompt Cursor / Aider\n\n"
        f"**Repo :** `{repo_path}`\n"
        f"**Fichiers :** \n{file_list}\n\n"
        f"**Instruction :**\n{message}\n\n"
        f"---\n"
        f"*Colle ça dans Cursor (Ctrl+K) ou dans Aider : `aider --message \"{message[:100]}...\"`*"
    )
