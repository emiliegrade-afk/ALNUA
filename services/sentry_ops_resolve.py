"""Map Sentry events to ALNUA repo slugs and owning agents."""

from __future__ import annotations

import json
import os

from config.github_repos import get_target_by_slug
from services.sentry_ops_parse import SentryIngestEvent


def resolve_repo_slug_from_sentry(event: SentryIngestEvent) -> str:
    """Map Sentry project/tags → hub repo slug."""
    raw_map = os.getenv("SENTRY_REPO_MAP", "").strip()
    if raw_map:
        try:
            mapping = json.loads(raw_map)
            for key in (
                event.project_slug,
                event.tags.get("repo_slug"),
                event.tags.get("project"),
            ):
                if key and key in mapping:
                    return str(mapping[key])
        except json.JSONDecodeError:
            pass

    haystack = " ".join(
        [
            event.project_slug,
            event.title,
            event.culprit,
            event.tags.get("project", ""),
        ]
    ).lower()

    if any(k in haystack for k in ("hub", "alnua")):
        if get_target_by_slug("hub"):
            return "hub"
    if "resonance" in haystack and get_target_by_slug("resonance"):
        return "resonance"
    if "academy" in haystack and get_target_by_slug("academy"):
        return "academy"
    if get_target_by_slug("hub"):
        return "hub"
    if get_target_by_slug("resonance"):
        return "resonance"
    if get_target_by_slug("academy"):
        return "academy"
    return "hub"


def resolve_agent_from_sentry(event: SentryIngestEvent, repo_slug: str) -> str:
    if repo_slug == "resonance":
        platform = (event.platform or "").lower()
        if platform in ("node", "python", "fastapi"):
            return "dev_backend"
        return "dev_resonance"
    if repo_slug in ("academy",):
        return "dev_app"
    platform = (event.platform or "").lower()
    if platform in ("python", "fastapi"):
        return "dev_backend"
    return "dev_backend"
