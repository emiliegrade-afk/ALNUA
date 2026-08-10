"""GitHub Issues skill — thin façade (debt paydown).

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
- GITHUB_REPO, GITHUB_REPO_ACADEMY : owner/repo-name
- HUB_REPO_PATH, REPO_PATH_ACADEMY : chemins locaux (worktrees)
- CODING_TIMEOUT_S, CODING_MAX_TURNS, CODING_AUTO_MERGE, CODING_MERGE_BASE_BRANCH (Phase 1)
"""
from __future__ import annotations

from skills.gh_issues_client import (  # noqa: F401
    GITHUB_API,
    RATE_LIMIT_BACKOFF,
    get_headers,
    post_comment,
    set_label,
)
from skills.gh_issues_fetch import (  # noqa: F401
    get_issue,
    get_open_prs,
    list_ready_issues,
)
from skills.gh_issues_poll import POLL_INTERVAL, poll_issues_loop  # noqa: F401
from skills.gh_issues_process import process_issue  # noqa: F401
from skills.gh_issues_spec import issue_to_spec  # noqa: F401
from skills.gh_issues_tools import (  # noqa: F401
    comment_on_issue,
    create_github_issue,
    get_open_issues,
    label_issue,
)

__all__ = [
    "GITHUB_API",
    "POLL_INTERVAL",
    "RATE_LIMIT_BACKOFF",
    "comment_on_issue",
    "create_github_issue",
    "get_headers",
    "get_issue",
    "get_open_issues",
    "get_open_prs",
    "issue_to_spec",
    "label_issue",
    "list_ready_issues",
    "poll_issues_loop",
    "post_comment",
    "process_issue",
    "set_label",
]
