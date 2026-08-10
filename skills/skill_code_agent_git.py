"""Git and GitHub helpers for skill_code_agent."""

from __future__ import annotations

import json
import logging
import os
import re
import urllib.request
from pathlib import Path

logger = logging.getLogger(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")


def get_repo(repo_path: str):
    """Retourne un objet git.Repo. Installe gitpython si absent."""
    try:
        import git

        return git.Repo(repo_path)
    except ImportError:
        raise RuntimeError("gitpython non installé — lance : pip install gitpython")


def create_branch(repo, branch_name: str) -> None:
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


def commit_and_push(repo, files_modified: list[str], message: str) -> bool:
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


def create_pr(github_repo: str, branch: str, title: str, body: str) -> str | None:
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


def detect_files(error_message: str, repo_path: str, hint_files: list[str] | None) -> list[str]:
    """
    Trouve les fichiers Python probablement concernés par l'erreur.
    Priorité : hint_files > fichiers mentionnés dans l'erreur > recherche par mot-clé.
    """
    if hint_files:
        return [f for f in hint_files if Path(repo_path, f).exists()]

    found = []
    root = Path(repo_path)

    for match in re.finditer(r'File "([^"]+\.py)"', error_message):
        fpath = Path(match.group(1))
        try:
            rel = fpath.relative_to(root)
            found.append(str(rel))
        except ValueError:
            name = fpath.name
            for p in root.rglob(name):
                if ".git" not in str(p) and "node_modules" not in str(p):
                    found.append(str(p.relative_to(root)))
                    break

    return found[:5]
