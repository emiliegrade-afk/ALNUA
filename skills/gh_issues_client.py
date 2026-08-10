"""GitHub Issues — HTTP client, auth headers, labels, comments."""

from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"
RATE_LIMIT_BACKOFF = 300  # secondes après 403/429


def get_headers() -> dict:
    import os

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN non configuré dans .env")
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def github_get(client: httpx.Client, url: str, **kwargs) -> httpx.Response:
    """GET GitHub API avec gestion explicite des rate limits."""
    resp = client.get(url, headers=get_headers(), **kwargs)
    if resp.status_code in (403, 429):
        retry_after = int(resp.headers.get("Retry-After", RATE_LIMIT_BACKOFF))
        logger.warning(
            "[GHIssues] Rate limit GitHub (%s) — retry dans %ss",
            resp.status_code,
            retry_after,
        )
        raise httpx.HTTPStatusError(
            f"GitHub rate limit ({resp.status_code})",
            request=resp.request,
            response=resp,
        )
    resp.raise_for_status()
    return resp


def set_label(
    issue_number: int,
    add_labels: list[str],
    remove_labels: list[str] | None = None,
    *,
    github_repo: str,
) -> None:
    """Ajoute/retire des labels sur une issue."""
    headers = get_headers()

    with httpx.Client() as client:
        resp = client.get(
            f"{GITHUB_API}/repos/{github_repo}/issues/{issue_number}",
            headers=headers,
        )
        resp.raise_for_status()
        current = [label["name"] for label in resp.json().get("labels", [])]

        new_labels = [label for label in current if label not in (remove_labels or [])]
        new_labels.extend(add_labels)
        new_labels = list(set(new_labels))

        client.patch(
            f"{GITHUB_API}/repos/{github_repo}/issues/{issue_number}",
            headers=headers,
            json={"labels": new_labels},
        )


def post_comment(issue_number: int, body: str, *, github_repo: str) -> None:
    """Poste un commentaire sur une issue GitHub."""
    with httpx.Client() as client:
        client.post(
            f"{GITHUB_API}/repos/{github_repo}/issues/{issue_number}/comments",
            headers=get_headers(),
            json={"body": body},
        )
