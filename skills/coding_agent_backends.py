"""Claude coding backend — split from skill_coding_agent."""
from __future__ import annotations

import logging
import shutil
from datetime import datetime
from pathlib import Path
from services.coding_pipeline import (
    CodingPipelineConfig,
    detect_stack,
    get_coding_config,
    resolve_default_branch,
    resolve_pr_base_branch,
)
from skills.coding_agent_cli import _resolve_cli, run_command
from skills.coding_agent_hub_aider import _execute_aider_task_core, _execute_hub_task_core
from skills.coding_agent_prompt import build_claude_prompt
from skills.coding_agent_worktree import (
    _cleanup_stale_worktree,
    _enforce_pre_pr_qa,
    _enforce_worktree_limit,
    _resolve_spec_agent_id,
)

logger = logging.getLogger(__name__)


def _execute_coding_task_core(spec: dict) -> dict:

    """

    Single coding pipeline run (worktree → executor → commit → PR).
    Raises on logical failure so retry_with_learning can catch and retry.
    """
    config = get_coding_config()
    if config.backend == "hub":
        result = _execute_hub_task_core(spec)
        if not result.get("success"):
            raise RuntimeError(result.get("error", "Échec inconnu du Hub coding agent"))
        return result
    if config.backend == "aider":
        result = _execute_aider_task_core(spec)
        if not result.get("success"):
            raise RuntimeError(result.get("error", "Échec inconnu du coding agent"))
        return result

    from services.agent_isolation import coding_isolation

    with coding_isolation(spec):
        return _execute_claude_task_core_isolated(spec, config)


def _execute_claude_task_core_isolated(
    spec: dict,
    config: CodingPipelineConfig,
) -> dict:
    repo_path = spec.get("repo_path")
    branch = spec.get(
        "branch_name",
        f"feat/auto-{spec['task_id'].lower()}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
    )
    agent_id = _resolve_spec_agent_id(spec)
    _enforce_worktree_limit(repo_path, config.max_worktrees)
    worktree_path = Path(repo_path) / "worktrees" / f"{agent_id}-{branch.replace('/', '-')}"
    result: dict = {
        "success": False,
        "pr_url": None,
        "branch": branch,
        "commit_sha": None,
        "claude_output": "",
        "stack": detect_stack(spec).value,
        "backend": "claude",
        "error": None,
    }
    try:
        # 1. Créer le worktree git isolé
        logger.info("[CodingAgent] Création worktree : %s", worktree_path)
        worktree_path.parent.mkdir(parents=True, exist_ok=True)
        _cleanup_stale_worktree(repo_path, branch, worktree_path)
        default_branch = resolve_default_branch(repo_path)
        code, _out, err = run_command(
            ["git", "worktree", "add", str(worktree_path), "-b", branch, default_branch],
            cwd=repo_path,
        )
        if code != 0:
            raise RuntimeError(f"Échec création worktree : {err}")
        # Local .env is gitignored — copy so Expo/Supabase exos can read keys in worktree
        env_src = Path(repo_path) / ".env"
        env_dst = worktree_path / ".env"
        if env_src.is_file() and not env_dst.exists():
            shutil.copy2(env_src, env_dst)
        # 2. Construire le prompt
        prompt = build_claude_prompt(spec)
        # 3. Lancer Claude Code CLI en mode non-interactif
        logger.info(
            "[CodingAgent] Lancement Claude Code pour %s (timeout=%ss, turns=%s, stack=%s)",
            spec["task_id"],
            config.timeout_s,
            config.max_turns,
            result["stack"],
        )
        code, claude_out, claude_err = run_command(
            [
                _resolve_cli("claude"),
                "--print",
                "--allowedTools",
                "edit,write,bash,read",
                "--max-turns",
                str(config.max_turns),
                prompt,
            ],
            cwd=str(worktree_path),
            timeout=config.timeout_s,
        )
        result["claude_output"] = claude_out
        if claude_err:
            logger.warning("[CodingAgent] Claude stderr : %s", claude_err[:500])
        # 4. Vérifier que des fichiers ont été modifiés
        code, diff_out, _ = run_command(
            ["git", "diff", "--name-only"],
            cwd=str(worktree_path),
        )
        if not diff_out.strip():
            raise RuntimeError("Claude Code n'a modifié aucun fichier")
        # 5. Commit
        run_command(["git", "add", "."], cwd=str(worktree_path))
        commit_msg = f"feat({spec['task_id']}): {spec['title']}"
        code, _commit_out, commit_err = run_command(
            ["git", "commit", "-m", commit_msg],
            cwd=str(worktree_path),
        )
        if code != 0:
            raise RuntimeError(f"Échec commit : {commit_err}")
        default_branch = resolve_default_branch(repo_path)
        qa = _enforce_pre_pr_qa(worktree_path, default_branch, spec)
        result["qa_passed"] = True
        result["qa_summary"] = qa.get("summary", "OK")
        # Récupérer le SHA du commit
        _, sha, _ = run_command(
            ["git", "rev-parse", "HEAD"],
            cwd=str(worktree_path),
        )
        result["commit_sha"] = sha.strip()
        # 6. Push
        code, _, push_err = run_command(
            ["git", "push", "origin", branch],
            cwd=str(worktree_path),
        )
        if code != 0:
            raise RuntimeError(f"Échec push : {push_err}")
        # 7. Ouvrir PR via gh CLI
        pr_title = spec.get("pr_title", f"[Auto] {spec['title']}")
        pr_body = spec.get(
            "pr_body",
            f"Tâche automatique générée par Dev App Agent.\n\nTask ID : `{spec['task_id']}`\n\n"
            f"Lancée le : {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        )
        pr_cmd = [
            "gh",
            "pr",
            "create",
            "--title",
            pr_title,
            "--body",
            pr_body,
            "--head",
            branch,
        ]
        pr_base = resolve_pr_base_branch(repo_path, config)
        if pr_base:
            pr_cmd.extend(["--base", pr_base])
        code, pr_out, pr_err = run_command(
            pr_cmd,
            cwd=repo_path,
        )
        if code != 0:
            pr_cmd_label = pr_cmd + ["--label", "auto-generated"]
            code, pr_out, pr_err = run_command(pr_cmd_label, cwd=repo_path)
        if code != 0:
            raise RuntimeError(f"Échec création PR : {pr_err}")
        pr_url = pr_out.strip().split("\n")[-1]
        result["pr_url"] = pr_url
        result["success"] = True
        logger.info("[CodingAgent] [OK] PR créée : %s", pr_url)
    except Exception as e:
        result["error"] = str(e)
        logger.error("[CodingAgent] [ERREUR] Erreur : %s", e)
        raise
    finally:
        # 8. Nettoyer le worktree (toujours, même en cas d'erreur)
        if worktree_path.exists():
            run_command(
                ["git", "worktree", "remove", str(worktree_path), "--force"],
                cwd=repo_path,
            )
            logger.info("[CodingAgent] Worktree nettoyé : %s", worktree_path)
    if not result.get("success"):
        raise RuntimeError(result.get("error", "Échec inconnu du coding agent"))
    return result

