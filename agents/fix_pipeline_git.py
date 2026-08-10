"""Git helpers for fix_pipeline merge and rollback."""
from __future__ import annotations

import logging
import subprocess

logger = logging.getLogger(__name__)


def _get_diff(repo_path: str, branch: str) -> str:
    """Récupère le diff entre la branche de fix et main."""
    try:
        r = subprocess.run(
            ["git", "diff", "main", branch, "--stat", "-p", "--no-color"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=15,
        )
        return r.stdout[:5000]
    except Exception:
        return ""


def _auto_merge(repo_path: str, branch: str) -> bool:
    """Merge automatique de la branche fix sur main (DEC-022 + DEC-025)."""
    try:
        from services.merge_policy import MergeDeniedError, assert_can_merge, merge_autonomy

        assert_can_merge("fix_pipeline", "main", repo_slug=None)
        autonomy = merge_autonomy(
            "main",
            actor_agent_id="fix_pipeline",
            producer_agent_id="fix_pipeline",
        )
        if autonomy.get("mode") != "auto":
            logger.error(
                "fix_pipeline: auto-merge blocked by autonomy: %s",
                autonomy.get("reason"),
            )
            return False
    except MergeDeniedError as exc:
        logger.error("fix_pipeline: auto-merge denied by policy: %s", exc)
        return False
    except Exception as exc:
        logger.error("fix_pipeline: merge policy check failed: %s", exc)
        return False

    try:
        import git

        repo = git.Repo(repo_path)
        repo.git.checkout("main")
        repo.git.pull("origin", "main")
        repo.git.merge(branch, "--no-ff", m=f"[auto-merge] {branch}")
        origin = repo.remote("origin")
        origin.push("main")
        logger.info("fix_pipeline: merge automatique OK — %s → main", branch)
        return True
    except Exception as exc:
        logger.error("fix_pipeline: auto-merge failed: %s", exc)
        return False


def _rollback(repo_path: str, branch: str) -> None:
    """Supprime la branche de fix sans merger."""
    try:
        import git

        repo = git.Repo(repo_path)
        repo.git.checkout("main")
        repo.delete_head(branch, force=True)
        logger.info("fix_pipeline: rollback — branche %s supprimée", branch)
    except Exception as exc:
        logger.warning("fix_pipeline: rollback failed: %s", exc)
