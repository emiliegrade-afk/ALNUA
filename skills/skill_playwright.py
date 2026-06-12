"""
skill_playwright.py

Lance les tests E2E et unitaires sur une branche/PR.
Poste les résultats en commentaire GitHub.

Pour l'instant : pytest + éventuellement Playwright E2E si dispo.
Évolutif : ajouter support React Native tests, UE5 tests.

Variables d'env :
- GITHUB_TOKEN, GITHUB_REPO (pour commenter la PR)
- TEST_COMMAND : commande de test (défaut: "pytest tests/ -v")
"""

import logging
import os
import re
import subprocess
import time
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)

DEFAULT_TEST_COMMAND = os.getenv("TEST_COMMAND", "pytest tests/ -v --tb=short")


def run_tests(repo_path: str, branch: str | None = None) -> dict:
    """
    Lance les tests dans le repo (sur la branche courante ou une branche spécifiée).

    Returns:
        {
            "passed": True/False,
            "total": int,
            "passed_count": int,
            "failed_count": int,
            "output": str,
            "duration_s": float
        }
    """
    # Checkout la branche si spécifiée
    if branch:
        subprocess.run(
            ["git", "checkout", branch],
            cwd=repo_path,
            capture_output=True,
        )

    start = time.time()

    # Lancer les tests
    result = subprocess.run(
        DEFAULT_TEST_COMMAND.split(),
        cwd=repo_path,
        capture_output=True,
        text=True,
        timeout=300,
    )

    duration = time.time() - start
    output = result.stdout + result.stderr

    # Parser les résultats pytest
    passed_count = 0
    failed_count = 0
    total = 0

    for line in output.split("\n"):
        if " passed" in line or " failed" in line or " error" in line:
            numbers = re.findall(r"(\d+)\s+(passed|failed|error)", line)
            for count, status in numbers:
                count = int(count)
                if status == "passed":
                    passed_count = count
                elif status in ("failed", "error"):
                    failed_count += count
            total = passed_count + failed_count

    return {
        "passed": result.returncode == 0,
        "total": total,
        "passed_count": passed_count,
        "failed_count": failed_count,
        "output": output[:3000],
        "duration_s": round(duration, 1),
    }


def post_pr_comment(
    pr_number: int,
    test_result: dict,
    *,
    github_repo: str | None = None,
) -> None:
    """
    Poste les résultats des tests en commentaire sur la PR GitHub.
    """
    repo = github_repo or os.getenv("GITHUB_REPO")
    if not repo:
        raise ValueError("github_repo ou GITHUB_REPO requis pour commenter la PR")
    status_icon = "[OK]" if test_result["passed"] else "[ERREUR]"
    status_text = "Tests passés" if test_result["passed"] else "Tests échoués"

    body = f"""## {status_icon} QA Agent — Rapport de tests

**Statut :** {status_text}
**Résultats :** {test_result['passed_count']} passés / {test_result['failed_count']} échoués / {test_result['total']} total
**Durée :** {test_result['duration_s']}s
**Date :** {datetime.now().strftime('%d/%m/%Y %H:%M')}

<details>
<summary>Détail des tests</summary>

```
{test_result['output']}
```
</details>

---
*Rapport généré automatiquement par QA Agent ALNUA*
"""

    with httpx.Client() as client:
        headers = {
            "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
            "Accept": "application/vnd.github+json",
        }
        client.post(
            f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments",
            headers=headers,
            json={"body": body},
        )


def run_and_report(
    repo_path: str,
    branch: str,
    pr_number: int,
    telegram_notify_fn=None,
    *,
    github_repo: str | None = None,
) -> dict:
    """
    Point d'entrée principal : lance les tests et reporte partout.
    """
    logger.info("[Playwright] Lancement tests sur branche %s", branch)
    result = run_tests(repo_path, branch)

    try:
        post_pr_comment(pr_number, result, github_repo=github_repo)
    except Exception as e:
        logger.warning("[Playwright] Impossible de commenter la PR : %s", e)

    if telegram_notify_fn:
        icon = "[OK]" if result["passed"] else "[ERREUR]"
        telegram_notify_fn(
            f"{icon} **Tests QA — PR #{pr_number}**\n"
            f"{result['passed_count']}/{result['total']} tests passés\n"
            f"Durée : {result['duration_s']}s"
        )

    return result
