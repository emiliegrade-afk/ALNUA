"""GitHub repo targets for the autonomous coding pipeline."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class GitHubRepoTarget:
    slug: str
    name: str
    github_repo: str
    local_path: Path


def _dev_parent() -> Path:
    hub = os.getenv("HUB_REPO_PATH", str(_PROJECT_ROOT)).strip()
    return Path(hub).resolve().parent


@lru_cache
def get_repo_targets() -> tuple[GitHubRepoTarget, ...]:
    """All configured repos (hub + app projects). Empty github_repo entries are skipped."""
    targets: list[GitHubRepoTarget] = []

    hub_repo = os.getenv("GITHUB_REPO", "").strip()
    if hub_repo:
        targets.append(
            GitHubRepoTarget(
                slug="hub",
                name="ALNUA Hub",
                github_repo=hub_repo,
                local_path=Path(
                    os.getenv("HUB_REPO_PATH", str(_PROJECT_ROOT)).strip()
                ).resolve(),
            )
        )

    naia_repo = os.getenv("GITHUB_REPO_NAIA", "").strip()
    if naia_repo:
        targets.append(
            GitHubRepoTarget(
                slug="naia",
                name="Naïa",
                github_repo=naia_repo,
                local_path=Path(
                    os.getenv("REPO_PATH_NAIA", str(_dev_parent() / "naia")).strip()
                ).resolve(),
            )
        )

    nomad_repo = os.getenv("GITHUB_REPO_NOMAD", "").strip()
    if nomad_repo:
        targets.append(
            GitHubRepoTarget(
                slug="nomad",
                name="NOMAD",
                github_repo=nomad_repo,
                local_path=Path(
                    os.getenv("REPO_PATH_NOMAD", str(_dev_parent() / "nomad")).strip()
                ).resolve(),
            )
        )

    return tuple(targets)


def pipeline_enabled() -> bool:
    return bool(os.getenv("GITHUB_TOKEN", "").strip()) and bool(get_repo_targets())


def get_target_by_slug(slug: str) -> GitHubRepoTarget | None:
    for target in get_repo_targets():
        if target.slug == slug:
            return target
    return None


def get_target_by_github_repo(github_repo: str) -> GitHubRepoTarget | None:
    needle = github_repo.strip().lower()
    for target in get_repo_targets():
        if target.github_repo.lower() == needle:
            return target
    return None


def resolve_target(
    *,
    repo_slug: str | None = None,
    github_repo: str | None = None,
) -> GitHubRepoTarget:
    if repo_slug:
        target = get_target_by_slug(repo_slug)
        if target:
            return target
        raise ValueError(f"Repo inconnu : {repo_slug}")

    if github_repo:
        target = get_target_by_github_repo(github_repo)
        if target:
            return target
        raise ValueError(f"Repo GitHub non configuré : {github_repo}")

    raise ValueError("repo_slug ou github_repo requis")


def annotate_issue(issue: dict, target: GitHubRepoTarget) -> dict:
    return {
        **issue,
        "_repo_slug": target.slug,
        "_repo_name": target.name,
        "_github_repo": target.github_repo,
        "_repo_path": str(target.local_path),
    }


def issue_target(issue: dict) -> GitHubRepoTarget:
    """Resolve target from an annotated issue dict."""
    slug = issue.get("_repo_slug")
    if slug:
        target = get_target_by_slug(slug)
        if target:
            return target

    github_repo = issue.get("_github_repo")
    if github_repo:
        target = get_target_by_github_repo(github_repo)
        if target:
            return target

    raise ValueError(
        f"Issue #{issue.get('number')} sans métadonnée repo — relancer list_ready_issues"
    )
