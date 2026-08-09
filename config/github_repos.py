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

    academy_repo = os.getenv("GITHUB_REPO_ACADEMY", "").strip()
    if academy_repo:
        targets.append(
            GitHubRepoTarget(
                slug="academy",
                name="ALNUA Academy",
                github_repo=academy_repo,
                local_path=Path(
                    os.getenv(
                        "REPO_PATH_ACADEMY",
                        str(_dev_parent() / "alnua-academy"),
                    ).strip()
                ).resolve(),
            )
        )

    resonance_repo = os.getenv("GITHUB_REPO_RESONANCE", "").strip()
    if resonance_repo:
        targets.append(
            GitHubRepoTarget(
                slug="resonance",
                name="Résonance",
                github_repo=resonance_repo,
                local_path=Path(
                    os.getenv(
                        "REPO_PATH_RESONANCE",
                        str(_dev_parent() / "RESONANCE"),
                    ).strip()
                ).resolve(),
            )
        )

    # DEC-020 — UE5.8 / Gaming studio project (Claude Code agency)
    gaming_repo = os.getenv("GITHUB_REPO_GAMING", "").strip()
    gaming_path = (
        os.getenv("UE_PROJECT_PATH", "").strip()
        or os.getenv("REPO_PATH_GAMING", "").strip()
    )
    if gaming_repo and gaming_path:
        targets.append(
            GitHubRepoTarget(
                slug="gaming",
                name="ALNUA Gaming UE5.8",
                github_repo=gaming_repo,
                local_path=Path(gaming_path).expanduser().resolve(),
            )
        )

    return tuple(targets)


def get_all_targets() -> tuple[GitHubRepoTarget, ...]:
    """Alias explicite — retourne tous les repos configurés."""
    return get_repo_targets()


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
    return _target_from_registry(github_repo=github_repo)


def _target_from_registry(
    *,
    slug: str | None = None,
    github_repo: str | None = None,
) -> GitHubRepoTarget | None:
    """Build a pipeline target from data/apps_registry.json (Phase 2)."""
    try:
        from services.app_registry import get_app, list_apps

        if slug:
            entry = get_app(slug)
            if entry and entry.github_configured and entry.enabled:
                local = (
                    Path(entry.local_path).expanduser().resolve()
                    if entry.local_path
                    else _dev_parent() / entry.slug
                )
                return GitHubRepoTarget(
                    slug=entry.slug,
                    name=entry.name,
                    github_repo=entry.github_repo.strip(),
                    local_path=local,
                )
            return None

        if github_repo:
            needle = github_repo.strip().lower()
            for entry in list_apps():
                if (
                    entry.enabled
                    and entry.github_configured
                    and entry.github_repo.strip().lower() == needle
                ):
                    local = (
                        Path(entry.local_path).expanduser().resolve()
                        if entry.local_path
                        else _dev_parent() / entry.slug
                    )
                    return GitHubRepoTarget(
                        slug=entry.slug,
                        name=entry.name,
                        github_repo=entry.github_repo.strip(),
                        local_path=local,
                    )
    except Exception:
        pass
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
        target = _target_from_registry(slug=repo_slug)
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
        reg = _target_from_registry(slug=slug)
        if reg:
            return reg

    github_repo = issue.get("_github_repo")
    if github_repo:
        target = get_target_by_github_repo(github_repo)
        if target:
            return target

    raise ValueError(
        f"Issue #{issue.get('number')} sans métadonnée repo — relancer list_ready_issues"
    )
