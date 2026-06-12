"""
skill_gh_issues.py

Polls GitHub Issues avec label "agent-ready" on all configured repos.
Convertit chaque issue en spec JSON pour skill_coding_agent.
Met à jour l'issue avec le lien PR une fois la tâche terminée.

Labels utilisés :
- "agent-ready" : issue prête à être prise en charge par un agent
- "in-pipeline" : issue en cours de traitement
- "agent-done" : PR créée, en attente de merge
- "agent-failed" : pipeline échoué, intervention humaine requise

Variables d'env requises :
- GITHUB_TOKEN : token GitHub avec scope repo
- GITHUB_REPO, GITHUB_REPO_NAIA, GITHUB_REPO_NOMAD : owner/repo-name
- HUB_REPO_PATH, REPO_PATH_NAIA, REPO_PATH_NOMAD : chemins locaux (worktrees)
"""

import asyncio
import logging
import re
from datetime import datetime

import httpx
from crewai.tools import tool

from config.github_repos import (
    GitHubRepoTarget,
    annotate_issue,
    get_repo_targets,
    issue_target,
    resolve_target,
)

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"
POLL_INTERVAL = 60  # secondes entre chaque vérification
RATE_LIMIT_BACKOFF = 300  # secondes après 403/429


def _github_get(client: httpx.Client, url: str, **kwargs) -> httpx.Response:
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


def _fetch_issue(issue_number: int, target: GitHubRepoTarget) -> dict:
    with httpx.Client() as client:
        resp = _github_get(
            client,
            f"{GITHUB_API}/repos/{target.github_repo}/issues/{issue_number}",
        )
        return annotate_issue(resp.json(), target)


def get_issue(
    issue_number: int,
    *,
    repo_slug: str | None = None,
    github_repo: str | None = None,
) -> dict:
    """Récupère une issue GitHub par numéro (repo explicite ou recherche multi-repo)."""
    if repo_slug or github_repo:
        target = resolve_target(repo_slug=repo_slug, github_repo=github_repo)
        return _fetch_issue(issue_number, target)

    last_error: Exception | None = None
    for target in get_repo_targets():
        try:
            return _fetch_issue(issue_number, target)
        except httpx.HTTPStatusError as exc:
            if exc.response is not None and exc.response.status_code == 404:
                last_error = exc
                continue
            raise

    raise ValueError(
        f"Issue #{issue_number} introuvable sur les repos configurés"
    ) from last_error


def _list_ready_for_target(target: GitHubRepoTarget) -> list[dict]:
    url = f"{GITHUB_API}/repos/{target.github_repo}/issues"
    params = {"labels": "agent-ready", "state": "open", "per_page": 10}

    with httpx.Client() as client:
        resp = _github_get(client, url, params=params)
        issues = resp.json()

    ready = [
        i
        for i in issues
        if not any(l["name"] == "in-pipeline" for l in i.get("labels", []))
        and "pull_request" not in i
    ]
    return [annotate_issue(i, target) for i in ready]


def list_ready_issues() -> list[dict]:
    """Issues agent-ready sur tous les repos configurés."""
    targets = get_repo_targets()
    if not targets:
        raise ValueError("Aucun repo GitHub configuré (GITHUB_REPO, GITHUB_REPO_NAIA, …)")

    all_issues: list[dict] = []
    for target in targets:
        try:
            all_issues.extend(_list_ready_for_target(target))
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "[GHIssues] Impossible de lister %s : %s",
                target.github_repo,
                exc,
            )

    all_issues.sort(key=lambda i: i.get("created_at", ""), reverse=True)
    return all_issues


def get_open_prs() -> list[dict]:
    """PRs ouvertes agrégées depuis tous les repos configurés."""
    targets = get_repo_targets()
    if not targets:
        raise ValueError("Aucun repo GitHub configuré")

    all_prs: list[dict] = []
    for target in targets:
        url = f"{GITHUB_API}/repos/{target.github_repo}/pulls"
        params = {"state": "open", "per_page": 20}

        with httpx.Client() as client:
            resp = _github_get(client, url, params=params)
            pulls = resp.json()

        all_prs.extend(
            {
                "number": pr["number"],
                "title": pr["title"],
                "url": pr["html_url"],
                "html_url": pr["html_url"],
                "branch": pr["head"]["ref"],
                "repo_slug": target.slug,
                "repo_name": target.name,
                "github_repo": target.github_repo,
                "repo_path": str(target.local_path),
                "auto": any(
                    l["name"] in ("agent-done", "agent-ready", "in-pipeline")
                    for l in pr.get("labels", [])
                ),
            }
            for pr in pulls
        )

    return all_prs


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

    lines = body.split("\n")
    current_section = None
    desc_lines: list[str] = []

    for line in lines:
        if line.startswith("## Description"):
            current_section = "description"
        elif line.startswith("## Fichiers à créer"):
            current_section = "create"
        elif line.startswith("## Fichiers à modifier"):
            current_section = "modify"
        elif line.startswith("## Tests"):
            current_section = "tests"
        elif line.startswith("- ") and current_section == "create":
            item = line[2:].strip()
            if item and not item.startswith("<!--"):
                files_to_create.append(item)
        elif line.startswith("- ") and current_section == "modify":
            item = line[2:].strip()
            if item and not item.startswith("<!--"):
                files_to_modify.append(item)
        elif line.startswith("- ") and current_section == "tests":
            item = line[2:].strip()
            if item and not item.startswith("<!--"):
                tests_to_pass.append(item)
        elif current_section == "description":
            desc_lines.append(line)

    if desc_lines:
        description = "\n".join(desc_lines).strip()

    slug = title.lower()[:30].replace(" ", "-").replace("/", "-")
    branch_name = f"feat/issue-{number}-{slug}"

    return {
        "task_id": f"GH-{target.slug}-{number}",
        "title": title,
        "description": description,
        "files_to_create": files_to_create,
        "files_to_modify": files_to_modify,
        "tests_to_pass": tests_to_pass,
        "repo_path": local_path,
        "github_repo": target.github_repo,
        "branch_name": branch_name,
        "pr_title": f"feat(GH-{number}): {title}",
        "pr_body": (
            f"Closes #{number}\n\n"
            f"Généré automatiquement par Dev App Agent ALNUA ({target.name}).\n\n"
            f"**Issue :** #{number} — {title}\n"
            f"**Repo :** {target.github_repo}\n"
            f"**Date :** {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        ),
    }


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
        current = [l["name"] for l in resp.json().get("labels", [])]

        new_labels = [l for l in current if l not in (remove_labels or [])] + add_labels
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


def process_issue(
    issue: dict,
    repo_path: str | None = None,
    telegram_notify_fn=None,
) -> dict:
    """
    Traite une issue complète : spec → coding agent → update issue.
    L'issue doit être annotée (_repo_slug, _github_repo) ou issue_target() échouera.
    """
    from skills.skill_coding_agent import execute_coding_task
    from skills.skill_playwright import run_and_report

    target = issue_target(issue)
    local_path = repo_path or issue.get("_repo_path") or str(target.local_path)
    number = issue["number"]
    title = issue["title"]
    github_repo = target.github_repo

    logger.info(
        "[GHIssues] Traitement issue #%s (%s) : %s",
        number,
        target.name,
        title,
    )

    if not target.local_path.is_dir():
        error = (
            f"Chemin local introuvable pour {target.name} : {target.local_path}. "
            f"Clone le repo ou configure REPO_PATH_{target.slug.upper()}."
        )
        logger.error("[GHIssues] %s", error)
        return {"success": False, "error": error, "pr_url": None, "branch": None}

    set_label(
        number,
        ["in-pipeline"],
        remove_labels=["agent-ready"],
        github_repo=github_repo,
    )
    post_comment(
        number,
        f"[BOT] **Dev App Agent** prend en charge cette issue ({target.name}).\n\n"
        f"Pipeline démarré à {datetime.now().strftime('%H:%M')}...",
        github_repo=github_repo,
    )

    if telegram_notify_fn:
        telegram_notify_fn(
            f"🔧 Pipeline démarré ({target.name})\n**Issue #{number}** : {title}"
        )

    spec = issue_to_spec(issue, local_path)
    result = execute_coding_task(spec, telegram_notify_fn=telegram_notify_fn)

    if result["success"]:
        set_label(
            number,
            ["agent-done"],
            remove_labels=["in-pipeline"],
            github_repo=github_repo,
        )
        commit_sha = result.get("commit_sha") or ""
        short_sha = commit_sha[:7] if commit_sha else "n/a"
        post_comment(
            number,
            f"[OK] **PR créée avec succès !**\n\n"
            f"**PR :** {result['pr_url']}\n"
            f"**Branch :** `{result['branch']}`\n"
            f"**Commit :** `{short_sha}`\n\n"
            f"Les tests QA ont été lancés automatiquement.",
            github_repo=github_repo,
        )
        if telegram_notify_fn:
            telegram_notify_fn(
                f"[OK] **Pipeline terminé** ({target.name})\n"
                f"Issue #{number} : {title}\n"
                f"PR : {result['pr_url']}"
            )

        match = re.search(r"/pull/(\d+)", result.get("pr_url") or "")
        if match:
            try:
                run_and_report(
                    local_path,
                    result["branch"],
                    int(match.group(1)),
                    telegram_notify_fn,
                    github_repo=github_repo,
                )
            except Exception as exc:
                logger.warning("[GHIssues] QA tests failed to run: %s", exc)
    else:
        set_label(
            number,
            ["agent-failed"],
            remove_labels=["in-pipeline"],
            github_repo=github_repo,
        )
        post_comment(
            number,
            f"[ERREUR] **Pipeline échoué**\n\nErreur : `{result['error']}`\n\nIntervention humaine requise.",
            github_repo=github_repo,
        )
        if telegram_notify_fn:
            telegram_notify_fn(
                f"[ERREUR] **Pipeline échoué** ({target.name})\n"
                f"Issue #{number} : {title}\n"
                f"Erreur : {result['error']}"
            )

    return result


def _resolve_github_repo(repo_slug: str = "hub") -> str:
    target = resolve_target(repo_slug=repo_slug)
    return target.github_repo


@tool("get_open_issues")
def get_open_issues(repo_slug: str = "hub") -> str:
    """Liste les issues GitHub ouvertes sur un repo ALNUA (hub, naia, nomad)."""
    try:
        target = resolve_target(repo_slug=repo_slug)
        url = f"{GITHUB_API}/repos/{target.github_repo}/issues"
        params = {"state": "open", "per_page": 20}

        with httpx.Client() as client:
            resp = _github_get(client, url, params=params)
            issues = [
                i
                for i in resp.json()
                if "pull_request" not in i
            ]

        if not issues:
            return f"Aucune issue ouverte sur {target.name} ({target.github_repo})."

        lines = [
            f"#{i['number']} — {i['title']} [{', '.join(l['name'] for l in i.get('labels', []))}]"
            for i in issues
        ]
        return f"Issues ouvertes ({target.name}) :\n" + "\n".join(lines)
    except Exception as exc:
        return f"Erreur get_open_issues : {exc}"


@tool("create_github_issue")
def create_github_issue(
    title: str,
    body: str = "",
    repo_slug: str = "hub",
    labels: str = "",
) -> str:
    """Crée une issue GitHub. labels: noms séparés par des virgules (ex. agent-ready,bug)."""
    try:
        target = resolve_target(repo_slug=repo_slug)
        label_list = [l.strip() for l in labels.split(",") if l.strip()] if labels else []

        with httpx.Client() as client:
            resp = client.post(
                f"{GITHUB_API}/repos/{target.github_repo}/issues",
                headers=get_headers(),
                json={
                    "title": title,
                    "body": body or "Issue créée par un agent ALNUA.",
                    "labels": label_list,
                },
            )
            resp.raise_for_status()
            issue = resp.json()

        return (
            f"Issue #{issue['number']} créée sur {target.github_repo}\n"
            f"URL : {issue['html_url']}"
        )
    except Exception as exc:
        return f"Erreur create_github_issue : {exc}"


@tool("comment_on_issue")
def comment_on_issue(issue_number: int, body: str, repo_slug: str = "hub") -> str:
    """Poste un commentaire sur une issue GitHub."""
    try:
        github_repo = _resolve_github_repo(repo_slug)
        post_comment(issue_number, body, github_repo=github_repo)
        return f"Commentaire posté sur #{issue_number} ({github_repo})."
    except Exception as exc:
        return f"Erreur comment_on_issue : {exc}"


@tool("label_issue")
def label_issue(
    issue_number: int,
    add_labels: str,
    repo_slug: str = "hub",
    remove_labels: str = "",
) -> str:
    """Ajoute ou retire des labels sur une issue. Labels séparés par des virgules."""
    try:
        github_repo = _resolve_github_repo(repo_slug)
        add = [l.strip() for l in add_labels.split(",") if l.strip()]
        remove = [l.strip() for l in remove_labels.split(",") if l.strip()] or None
        set_label(
            issue_number,
            add,
            remove_labels=remove,
            github_repo=github_repo,
        )
        return f"Labels mis à jour sur #{issue_number} ({github_repo})."
    except Exception as exc:
        return f"Erreur label_issue : {exc}"


async def poll_issues_loop(telegram_notify_fn=None):
    """
    Boucle de polling asynchrone. À lancer en background task FastAPI.
    Vérifie toutes les POLL_INTERVAL secondes sur tous les repos configurés.
    """
    logger.info("[GHIssues] Démarrage du polling GitHub Issues (multi-repo)...")
    while True:
        try:
            issues = list_ready_issues()
            if issues:
                logger.info("[GHIssues] %s issue(s) trouvée(s)", len(issues))
                for issue in issues:
                    repo_path = issue.get("_repo_path")
                    asyncio.create_task(
                        asyncio.to_thread(
                            process_issue, issue, repo_path, telegram_notify_fn
                        )
                    )
            else:
                logger.debug("[GHIssues] Aucune issue à traiter")
        except httpx.HTTPStatusError as e:
            if e.response is not None and e.response.status_code in (403, 429):
                retry_after = int(
                    e.response.headers.get("Retry-After", RATE_LIMIT_BACKOFF)
                )
                logger.warning(
                    "[GHIssues] Rate limit — pause %ss avant prochain poll",
                    retry_after,
                )
                await asyncio.sleep(retry_after)
                continue
            logger.error("[GHIssues] Erreur HTTP polling : %s", e)
        except Exception as e:
            logger.error("[GHIssues] Erreur polling : %s", e)

        await asyncio.sleep(POLL_INTERVAL)
