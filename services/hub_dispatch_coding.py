"""After CEO-approved Hub dossier dispatch — auto-create GitHub issues on ALNUA_HUB."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_HUB_ISSUE_SPECS: tuple[tuple[str, str, str], ...] = (
    ("hub/spec-cursor-prompt.md", "Spec Hub", "[Hub dispatch] Spec — {title}"),
    (
        "hub/api-implementation-brief.md",
        "Backend Hub",
        "[Hub dispatch] API — {title}",
    ),
    (
        "hub/ui-implementation-brief.md",
        "UI Hub",
        "[Hub dispatch] UI — {title}",
    ),
)


def _workspace_root() -> Path:
    raw = os.environ.get("ALNUA_WORKSPACE", "").strip()
    if raw:
        return Path(raw)
    return Path(os.environ.get("HUB_REPO_PATH", "C:/Dev/ALUNA_HUB")).parent / "ALNUA"


def _read_brief(slug: str, rel_path: str) -> str | None:
    """Option A layout: {workspace}/hub/{slug}/{filename}."""
    pole, filename = rel_path.split("/", 1)
    path = _workspace_root() / pole / slug / filename
    if path.is_file():
        return path.read_text(encoding="utf-8").strip()
    return None


def create_hub_coding_issues(
    dossier_title: str,
    slug: str,
    *,
    dossier_id: str | None = None,
) -> dict[str, Any]:
    """
    Create agent-ready GitHub issues from hub dispatch deliverables.
    CEO already chose WHAT (dossier approved) — this automates HOW (coding).
    """
    if not os.getenv("GITHUB_TOKEN", "").strip():
        return {"success": False, "error": "GITHUB_TOKEN absent", "issues": []}

    from skills.skill_gh_issues import create_github_issue

    issues: list[dict[str, Any]] = []
    for rel, label, title_tpl in _HUB_ISSUE_SPECS:
        content = _read_brief(slug, rel_path=rel)
        if not content or len(content) < 80:
            continue

        body = (
            f"**Dispatch Hub ALNUA** — dossier `{slug}`\n"
            f"Dossier ID: {dossier_id or 'n/a'}\n\n"
            f"Emilie a validé le **quoi** (CEO). Pipeline : implémenter le **comment**.\n\n"
            f"---\n\n{content[:12000]}"
        )
        title = title_tpl.format(title=dossier_title[:60])
        try:
            raw = create_github_issue(
                title=title[:120],
                body=body,
                repo_slug="hub",
                labels="agent-ready,hub-dispatch",
            )
            if "Issue #" in raw:
                num = int(raw.split("Issue #")[1].split()[0])
                issues.append({"label": label, "number": num, "file": rel})
                logger.info("Hub dispatch issue #%s created (%s)", num, label)
        except Exception as exc:
            logger.warning("create_hub_coding_issues %s failed: %s", rel, exc)

    if not issues:
        spec = _read_brief(slug, "hub/spec-cursor-prompt.md")
        if not spec:
            return {
                "success": False,
                "error": "Aucun livrable hub trouvé dans le workspace",
                "issues": [],
            }

    return {"success": bool(issues), "issues": issues, "count": len(issues)}
