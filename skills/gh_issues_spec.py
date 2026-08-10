"""GitHub Issues — convert issue body to coding-agent spec JSON."""

from __future__ import annotations

import re
from datetime import datetime

from config.github_repos import issue_target

_PLACEHOLDER_FILES = frozenset({"(aucun)", "aucun", "n/a", "none", "-", "—", "(none)"})


def _is_real_file_path(item: str) -> bool:
    """Ignore issue template placeholders like '(aucun)' that agents must not create."""
    normalized = item.strip().lower()
    if normalized in _PLACEHOLDER_FILES:
        return False
    if normalized.startswith("(") and normalized.endswith(")"):
        return False
    return True


def _git_branch_slug(title: str, *, max_len: int = 30) -> str:
    """Sanitize issue title for git branch names (no brackets, spaces, etc.)."""
    slug = title.lower()
    slug = re.sub(r"[\[\]~^:?*\\@/]", "", slug)
    slug = re.sub(r"[^a-z0-9._-]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-/")
    return (slug[:max_len] or "issue").strip("-")


def issue_to_spec(issue: dict, repo_path: str | None = None) -> dict:
    """
    Convertit une GitHub Issue en JSON spec pour skill_coding_agent.
    Utilise le titre + body de l'issue.
    """
    target = issue_target(issue)
    local_path = repo_path or issue.get("_repo_path") or str(target.local_path)

    number = issue["number"]
    title = issue["title"]
    body = issue.get("body", "") or ""

    description = body
    files_to_create: list[str] = []
    files_to_modify: list[str] = []
    tests_to_pass: list[str] = []
    stack: str | None = None

    lines = body.split("\n")
    current_section = None
    desc_lines: list[str] = []

    for line in lines:
        if line.startswith("## Description"):
            current_section = "description"
        elif line.startswith("## Stack"):
            current_section = "stack"
        elif line.startswith("## Fichiers à créer"):
            current_section = "create"
        elif line.startswith("## Fichiers à modifier"):
            current_section = "modify"
        elif line.startswith("## Tests"):
            current_section = "tests"
        elif line.startswith("- ") and current_section == "create":
            item = line[2:].strip()
            if item and not item.startswith("<!--") and _is_real_file_path(item):
                files_to_create.append(item)
        elif line.startswith("- ") and current_section == "modify":
            item = line[2:].strip()
            if item and not item.startswith("<!--") and _is_real_file_path(item):
                files_to_modify.append(item)
        elif line.startswith("- ") and current_section == "tests":
            item = line[2:].strip()
            if item and not item.startswith("<!--"):
                tests_to_pass.append(item)
        elif current_section == "description":
            desc_lines.append(line)
        elif current_section == "stack" and line.strip() and not line.startswith("#"):
            stack = line.strip().lower()

    if desc_lines:
        description = "\n".join(desc_lines).strip()

    slug = _git_branch_slug(title)
    branch_name = f"feat/issue-{number}-{slug}"

    spec: dict = {
        "task_id": f"GH-{target.slug}-{number}",
        "title": title,
        "description": description,
        "files_to_create": files_to_create,
        "files_to_modify": files_to_modify,
        "tests_to_pass": tests_to_pass,
        "repo_path": local_path,
        "repo_slug": target.slug,
        "github_repo": target.github_repo,
        "branch_name": branch_name,
        "agent_id": "dev_app",
        "pr_title": f"feat(GH-{number}): {title}",
        "pr_body": (
            f"Closes #{number}\n\n"
            f"Généré automatiquement par Dev App Agent ALNUA ({target.name}).\n\n"
            f"**Issue :** #{number} — {title}\n"
            f"**Repo :** {target.github_repo}\n"
            f"**Date :** {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        ),
    }
    if stack:
        spec["stack"] = stack
    return spec
