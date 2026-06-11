"""
skill_gh_issues.py

Polls GitHub Issues avec label "agent-ready".
Convertit chaque issue en spec JSON pour skill_coding_agent.
Met à jour l'issue avec le lien PR une fois la tâche terminée.

Labels utilisés :
- "agent-ready" : issue prête à être prise en charge par un agent
- "in-pipeline" : issue en cours de traitement
- "agent-done" : PR créée, en attente de merge
- "agent-failed" : pipeline échoué, intervention humaine requise

Variables d'env requises :
- GITHUB_TOKEN : token GitHub avec scope repo
- GITHUB_REPO : "owner/repo-name"
- HUB_REPO_PATH : chemin local du repo Hub (pour les worktrees)
"""

import asyncio
import logging
import os
import re
from datetime import datetime

import httpx

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
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN non configuré dans .env")
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def get_issue(issue_number: int) -> dict:
    """Récupère une issue GitHub par son numéro."""
    repo = os.getenv("GITHUB_REPO")
    if not repo:
        raise ValueError("GITHUB_REPO non configuré dans .env")

    with httpx.Client() as client:
        resp = _github_get(client, f"{GITHUB_API}/repos/{repo}/issues/{issue_number}")
        return resp.json()


def list_ready_issues() -> list[dict]:
    """
    Retourne toutes les issues avec le label "agent-ready" (pas "in-pipeline").
    """
    repo = os.getenv("GITHUB_REPO")
    if not repo:
        raise ValueError("GITHUB_REPO non configuré dans .env")

    url = f"{GITHUB_API}/repos/{repo}/issues"
    params = {"labels": "agent-ready", "state": "open", "per_page": 10}

    with httpx.Client() as client:
        resp = _github_get(client, url, params=params)
        issues = resp.json()

    return [
        i
        for i in issues
        if not any(l["name"] == "in-pipeline" for l in i.get("labels", []))
        and "pull_request" not in i
    ]


def get_open_prs() -> list[dict]:
    """Retourne les PRs ouvertes du repo configuré."""
    repo = os.getenv("GITHUB_REPO")
    if not repo:
        raise ValueError("GITHUB_REPO non configuré dans .env")

    url = f"{GITHUB_API}/repos/{repo}/pulls"
    params = {"state": "open", "per_page": 20}

    with httpx.Client() as client:
        resp = _github_get(client, url, params=params)
        pulls = resp.json()

    return [
        {
            "number": pr["number"],
            "title": pr["title"],
            "url": pr["html_url"],
            "auto": any(
                l["name"] in ("agent-done", "agent-ready", "in-pipeline")
                for l in pr.get("labels", [])
            ),
        }
        for pr in pulls
    ]


def issue_to_spec(issue: dict, repo_path: str) -> dict:
    """
    Convertit une GitHub Issue en JSON spec pour skill_coding_agent.
    Utilise le titre + body de l'issue.
    Le body doit suivre le template (voir section Template).
    """
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
        "task_id": f"GH-{number}",
        "title": title,
        "description": description,
        "files_to_create": files_to_create,
        "files_to_modify": files_to_modify,
        "tests_to_pass": tests_to_pass,
        "repo_path": repo_path,
        "branch_name": branch_name,
        "pr_title": f"feat(GH-{number}): {title}",
        "pr_body": (
            f"Closes #{number}\n\n"
            f"Généré automatiquement par Dev App Agent ALNUA.\n\n"
            f"**Issue :** #{number} — {title}\n"
            f"**Date :** {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        ),
    }


def set_label(
    issue_number: int,
    add_labels: list[str],
    remove_labels: list[str] | None = None,
) -> None:
    """
    Ajoute/retire des labels sur une issue.
    """
    repo = os.getenv("GITHUB_REPO")
    headers = get_headers()

    with httpx.Client() as client:
        resp = client.get(
            f"{GITHUB_API}/repos/{repo}/issues/{issue_number}",
            headers=headers,
        )
        current = [l["name"] for l in resp.json().get("labels", [])]

        new_labels = [l for l in current if l not in (remove_labels or [])] + add_labels
        new_labels = list(set(new_labels))

        client.patch(
            f"{GITHUB_API}/repos/{repo}/issues/{issue_number}",
            headers=headers,
            json={"labels": new_labels},
        )


def post_comment(issue_number: int, body: str) -> None:
    """Poste un commentaire sur une issue GitHub."""
    repo = os.getenv("GITHUB_REPO")
    with httpx.Client() as client:
        client.post(
            f"{GITHUB_API}/repos/{repo}/issues/{issue_number}/comments",
            headers=get_headers(),
            json={"body": body},
        )


def process_issue(
    issue: dict,
    repo_path: str,
    telegram_notify_fn=None,
) -> dict:
    """
    Traite une issue complète : spec → coding agent → update issue.
    telegram_notify_fn : fonction optionnelle pour notifier Telegram.
    """
    from skills.skill_coding_agent import execute_coding_task
    from skills.skill_playwright import run_and_report

    number = issue["number"]
    title = issue["title"]
    logger.info("[GHIssues] Traitement issue #%s : %s", number, title)

    set_label(number, ["in-pipeline"], remove_labels=["agent-ready"])
    post_comment(
        number,
        f"🤖 **Dev App Agent** prend en charge cette issue.\n\n"
        f"Pipeline démarré à {datetime.now().strftime('%H:%M')}...",
    )

    if telegram_notify_fn:
        telegram_notify_fn(f"🔧 Pipeline démarré\n**Issue #{number}** : {title}")

    spec = issue_to_spec(issue, repo_path)
    result = execute_coding_task(spec, telegram_notify_fn=telegram_notify_fn)

    if result["success"]:
        set_label(number, ["agent-done"], remove_labels=["in-pipeline"])
        commit_sha = result.get("commit_sha") or ""
        short_sha = commit_sha[:7] if commit_sha else "n/a"
        post_comment(
            number,
            f"✅ **PR créée avec succès !**\n\n"
            f"**PR :** {result['pr_url']}\n"
            f"**Branch :** `{result['branch']}`\n"
            f"**Commit :** `{short_sha}`\n\n"
            f"Les tests QA ont été lancés automatiquement.",
        )
        if telegram_notify_fn:
            telegram_notify_fn(
                f"✅ **Pipeline terminé**\n"
                f"Issue #{number} : {title}\n"
                f"PR : {result['pr_url']}"
            )

        match = re.search(r"/pull/(\d+)", result.get("pr_url") or "")
        if match:
            try:
                run_and_report(
                    repo_path,
                    result["branch"],
                    int(match.group(1)),
                    telegram_notify_fn,
                )
            except Exception as exc:
                logger.warning("[GHIssues] QA tests failed to run: %s", exc)
    else:
        set_label(number, ["agent-failed"], remove_labels=["in-pipeline"])
        post_comment(
            number,
            f"❌ **Pipeline échoué**\n\nErreur : `{result['error']}`\n\nIntervention humaine requise.",
        )
        if telegram_notify_fn:
            telegram_notify_fn(
                f"❌ **Pipeline échoué**\n"
                f"Issue #{number} : {title}\n"
                f"Erreur : {result['error']}"
            )

    return result


async def poll_issues_loop(repo_path: str, telegram_notify_fn=None):
    """
    Boucle de polling asynchrone. À lancer en background task FastAPI.
    Vérifie toutes les POLL_INTERVAL secondes.
    """
    logger.info("[GHIssues] Démarrage du polling GitHub Issues...")
    while True:
        try:
            issues = list_ready_issues()
            if issues:
                logger.info("[GHIssues] %s issue(s) trouvée(s)", len(issues))
                for issue in issues:
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
