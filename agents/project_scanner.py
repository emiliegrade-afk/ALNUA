"""
ProjectScanner — Auto-discovery des projets ALNUA.

Lit GitHub (commits, README, issues, structure) + fichiers locaux
et indexe tout dans Chroma + Mem0 pour que les agents puissent
interroger la base de connaissance sans intervention humaine.

Déclenché :
- Au démarrage de l'API
- Toutes les 6h via le scheduler
- Manuellement : POST /agents/scan
"""

from __future__ import annotations

import json
import logging
import os
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Any

from skills.skill_chroma import index_document
from skills.skill_mem0 import remember

logger = logging.getLogger(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_API = "https://api.github.com"

# Repos à scanner : (repo_slug, agent_id, local_path)
REPOS = [
    (os.getenv("GITHUB_REPO", "emiliegrade-afk/ALNUA"), "coo", os.getenv("HUB_REPO_PATH", "")),
    (os.getenv("GITHUB_REPO_NOMAD", "emiliegrade-afk/NUAWAY"), "dev_app", os.getenv("REPO_PATH_NOMAD", "")),
    (os.getenv("GITHUB_REPO_NAIA", "emiliegrade-afk/naia"), "dev_gaming", os.getenv("REPO_PATH_NAIA", "")),
]

# Fichiers clés à lire dans les repos locaux
KEY_FILES = [
    "README.md", "README.rst",
    "package.json", "requirements.txt", "pyproject.toml",
    "CHANGELOG.md", "ROADMAP.md", "TODO.md",
    ".env.example",
]


# ---------------------------------------------------------------------------
# GitHub API helpers
# ---------------------------------------------------------------------------

def _gh_get(path: str) -> Any:
    """GET GitHub API avec le token. Retourne le JSON parsé ou None."""
    if not GITHUB_TOKEN:
        return None
    url = f"{GITHUB_API}{path}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as exc:
        logger.debug("GitHub API %s failed: %s", path, exc)
        return None


def _get_readme(repo: str) -> str:
    """Récupère le contenu du README depuis GitHub."""
    data = _gh_get(f"/repos/{repo}/readme")
    if not data:
        return ""
    import base64
    try:
        return base64.b64decode(data.get("content", "")).decode("utf-8", errors="ignore")[:8000]
    except Exception:
        return ""


def _get_recent_commits(repo: str, n: int = 15) -> list[str]:
    """Récupère les N derniers commits."""
    data = _gh_get(f"/repos/{repo}/commits?per_page={n}")
    if not data or not isinstance(data, list):
        return []
    commits = []
    for c in data:
        msg = c.get("commit", {}).get("message", "").split("\n")[0]
        sha = c.get("sha", "")[:7]
        date = c.get("commit", {}).get("author", {}).get("date", "")[:10]
        commits.append(f"[{sha}] {date} — {msg}")
    return commits


def _get_open_issues(repo: str, n: int = 20) -> list[str]:
    """Récupère les issues ouvertes."""
    data = _gh_get(f"/repos/{repo}/issues?state=open&per_page={n}")
    if not data or not isinstance(data, list):
        return []
    issues = []
    for i in data:
        if i.get("pull_request"):
            continue  # Ignore PRs
        labels = [l["name"] for l in i.get("labels", [])]
        issues.append(f"#{i['number']} [{', '.join(labels)}] {i['title']}")
    return issues


def _get_repo_tree(repo: str) -> list[str]:
    """Structure de fichiers du repo (premier niveau)."""
    data = _gh_get(f"/repos/{repo}/contents")
    if not data or not isinstance(data, list):
        return []
    return [f["name"] for f in data if isinstance(f, dict)]


# ---------------------------------------------------------------------------
# Local file scanner
# ---------------------------------------------------------------------------

def _scan_local_repo(local_path: str) -> dict[str, str]:
    """Lit les fichiers clés d'un repo local. Retourne {filename: content}."""
    if not local_path or not Path(local_path).exists():
        return {}
    results = {}
    root = Path(local_path)
    for fname in KEY_FILES:
        fpath = root / fname
        if fpath.exists():
            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")[:6000]
                results[fname] = content
            except Exception:
                pass

    # Git log local (plus détaillé que l'API)
    try:
        import subprocess
        log = subprocess.run(
            ["git", "log", "--oneline", "-20"],
            cwd=local_path,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if log.returncode == 0 and log.stdout:
            results["git_log"] = log.stdout
    except Exception:
        pass

    return results


# ---------------------------------------------------------------------------
# Scanner principal
# ---------------------------------------------------------------------------

def scan_repo(repo_slug: str, agent_id: str, local_path: str = "") -> int:
    """
    Scanne un repo GitHub + local et indexe dans Chroma + Mem0.
    Retourne le nombre de documents indexés.
    """
    project_name = repo_slug.split("/")[-1].upper()
    indexed = 0
    now = datetime.now().strftime("%Y-%m-%d")

    logger.info("ProjectScanner: scanning %s (agent=%s)", repo_slug, agent_id)

    # --- README ---
    readme = _get_readme(repo_slug)
    if readme:
        index_document(
            content=readme,
            doc_id=f"{repo_slug}:README:{now}",
            metadata={"repo": repo_slug, "type": "readme", "project": project_name},
        )
        # Résumé dans Mem0 (premiers 600 chars)
        remember(
            f"README {project_name} : {readme[:600]}",
            agent_id=agent_id,
        )
        indexed += 1

    # --- Commits récents ---
    commits = _get_recent_commits(repo_slug)
    if commits:
        commit_text = f"Commits récents {project_name} :\n" + "\n".join(commits)
        index_document(
            content=commit_text,
            doc_id=f"{repo_slug}:commits:{now}",
            metadata={"repo": repo_slug, "type": "commits", "project": project_name},
        )
        remember(
            f"Derniers commits {project_name} (au {now}) :\n" + "\n".join(commits[:5]),
            agent_id=agent_id,
        )
        indexed += 1

    # --- Issues ouvertes ---
    issues = _get_open_issues(repo_slug)
    if issues:
        issues_text = f"Issues ouvertes {project_name} :\n" + "\n".join(issues)
        index_document(
            content=issues_text,
            doc_id=f"{repo_slug}:issues:{now}",
            metadata={"repo": repo_slug, "type": "issues", "project": project_name},
        )
        remember(
            f"Issues ouvertes {project_name} ({len(issues)}) :\n" + "\n".join(issues[:8]),
            agent_id=agent_id,
        )
        indexed += 1
        # Le COO doit aussi savoir
        if agent_id != "coo":
            remember(
                f"Issues ouvertes {project_name} : {', '.join(issues[:5])}",
                agent_id="coo",
            )

    # --- Structure du repo ---
    tree = _get_repo_tree(repo_slug)
    if tree:
        tree_text = f"Structure {project_name} : {', '.join(tree)}"
        index_document(
            content=tree_text,
            doc_id=f"{repo_slug}:tree:{now}",
            metadata={"repo": repo_slug, "type": "tree", "project": project_name},
        )
        indexed += 1

    # --- Fichiers locaux ---
    local_files = _scan_local_repo(local_path)
    for fname, content in local_files.items():
        doc_id = f"{repo_slug}:local:{fname}:{now}"
        index_document(
            content=f"[{project_name}] {fname} :\n{content}",
            doc_id=doc_id,
            metadata={"repo": repo_slug, "type": "local_file", "file": fname, "project": project_name},
        )
        indexed += 1
        # Git log → Mem0 pour contexte récent
        if fname == "git_log":
            remember(
                f"Git log local {project_name} (récent) :\n{content[:400]}",
                agent_id=agent_id,
            )

    logger.info("ProjectScanner: %s — %d documents indexés", project_name, indexed)
    return indexed


def scan_all_projects() -> None:
    """Scanne tous les projets ALNUA. Appelé au startup + toutes les 6h."""
    logger.info("ProjectScanner: démarrage scan complet...")
    total = 0
    for repo_slug, agent_id, local_path in REPOS:
        if not repo_slug or "/" not in repo_slug:
            continue
        try:
            n = scan_repo(repo_slug, agent_id, local_path)
            total += n
        except Exception as exc:
            logger.error("ProjectScanner: erreur sur %s: %s", repo_slug, exc)

    # Mise à jour Mem0 COO avec date du dernier scan
    try:
        remember(
            f"Dernier scan automatique des projets ALNUA : {datetime.now().strftime('%Y-%m-%d %H:%M')}. "
            f"{total} documents indexés dans Chroma.",
            agent_id="coo",
        )
    except Exception:
        pass

    logger.info("ProjectScanner: scan terminé — %d documents au total", total)
