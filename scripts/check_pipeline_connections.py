"""Verify Phase 2 pipeline connections (Supabase, GitHub, git, gh)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")


def _ok(msg: str) -> None:
    print(f"  OK  {msg}")


def _warn(msg: str) -> None:
    print(f"  WARN  {msg}")


def _fail(msg: str) -> None:
    print(f"  FAIL  {msg}")


def check_supabase() -> bool:
    print("\n[Supabase]")
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_KEY", "")
    if not url or not key:
        _fail("SUPABASE_URL / SUPABASE_KEY manquants")
        return False
    _ok(f"URL configurée ({url})")

    try:
        from database.supabase_client import get_supabase

        db = get_supabase()
        rows = db.select("agent_costs", limit=1)
        _ok(f"Table agent_costs accessible ({len(rows)} ligne(s) lue(s))")
        return True
    except Exception as exc:
        _fail(f"agent_costs : {exc}")
        return False


def check_github() -> bool:
    print("\n[GitHub API]")
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if not token:
        _fail("GITHUB_TOKEN vide — crée un PAT sur github.com/settings/tokens (scope repo)")
        return False

    from config.github_repos import get_repo_targets

    targets = get_repo_targets()
    if not targets:
        _fail("Aucun repo configuré — GITHUB_REPO, GITHUB_REPO_NAIA, GITHUB_REPO_NOMAD")
        return False

    ok = True
    try:
        with httpx.Client() as client:
            for target in targets:
                resp = client.get(
                    f"https://api.github.com/repos/{target.github_repo}",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": "application/vnd.github+json",
                    },
                    timeout=15,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    _ok(f"{target.name} : {data['full_name']} — {data['html_url']}")
                else:
                    _fail(f"{target.name} API {resp.status_code} : {resp.text[:120]}")
                    ok = False

                if target.local_path.is_dir() and (target.local_path / ".git").exists():
                    _ok(f"{target.name} local : {target.local_path}")
                else:
                    _warn(
                        f"{target.name} non cloné localement ({target.local_path}) — "
                        f"git clone https://github.com/{target.github_repo}.git"
                    )
        return ok
    except Exception as exc:
        _fail(str(exc))
        return False


def check_git() -> bool:
    print("\n[Git local]")
    hub_path = Path(os.getenv("HUB_REPO_PATH", str(ROOT)))
    if not hub_path.is_dir():
        _fail(f"HUB_REPO_PATH introuvable : {hub_path}")
        return False
    _ok(f"HUB_REPO_PATH = {hub_path}")

    git_dir = hub_path / ".git"
    if not git_dir.exists():
        _warn("Pas de dépôt git — lance : git init && git remote add origin <url>")
        return False

    result = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        cwd=hub_path,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        _ok(f"Remote origin : {result.stdout.strip()}")
        return True
    _warn("Pas de remote origin — git remote add origin https://github.com/owner/repo.git")
    return False


def check_gh_cli() -> bool:
    print("\n[GitHub CLI]")
    result = subprocess.run(
        ["gh", "auth", "status"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        _ok("gh authentifié")
        return True
    _warn("gh non connecté — lance : gh auth login")
    return False


def main() -> int:
    print("ALNUA Hub — vérification connexions pipeline Phase 2")
    results = [
        check_supabase(),
        check_github(),
        check_git(),
        check_gh_cli(),
    ]
    print("\n" + ("Tout est prêt." if all(results[:2]) else "Actions requises ci-dessus."))
    return 0 if results[0] else 1


if __name__ == "__main__":
    sys.exit(main())
