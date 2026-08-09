"""Hub + Aider coding backends — split from skill_coding_agent."""
from __future__ import annotations

import logging
import os
import subprocess
from datetime import datetime

from services.coding_pipeline import get_coding_config
from skills.coding_agent_cli import _resolve_cli, run_command
from skills.coding_agent_prompt import build_claude_prompt
from skills.coding_agent_worktree import (
    _enforce_pre_pr_qa,
    _finalize_pr,
    _prepare_worktree,
    _resolve_spec_agent_id,
    _worktree_has_changes,
)

logger = logging.getLogger(__name__)


def _execute_hub_task_core(spec: dict) -> dict:
    """Worktree → Hub Agent (Cursor-like loop) → commit → PR."""
    from services.hub_coding_agent import run_hub_coding_loop
    config = get_coding_config()
    repo_path = spec.get("repo_path")
    branch = spec.get(
        "branch_name",
        f"feat/auto-{spec['task_id'].lower()}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
    )
    agent_id = _resolve_spec_agent_id(spec)
    worktree_path, default_branch, result = _prepare_worktree(spec, branch)
    result["backend"] = "hub"
    activity_id = spec.get("activity_id")
    if activity_id:
        try:
            from services.coding_activity import set_worktree_path
            set_worktree_path(str(activity_id), str(worktree_path))
        except Exception:
            pass
    try:
        from config.agent_models import get_coding_model_for_agent
        loop_result = run_hub_coding_loop(
            worktree_path,
            spec,
            max_turns=min(config.max_turns, 40),
            timeout_s=config.timeout_s,
            activity_id=str(activity_id) if activity_id else None,
        )
        result["claude_output"] = loop_result.get("log", "")[-8000:]
        result["coding_model"] = loop_result.get("model")
        if not loop_result.get("success"):
            raise RuntimeError(loop_result.get("error") or "Hub coding loop failed")
        logger.info(
            "[CodingAgent] Hub Agent OK %s (%s turns, model=%s)",
            spec["task_id"],
            loop_result.get("turns"),
            get_coding_model_for_agent(agent_id),
        )
        if not _worktree_has_changes(worktree_path, default_branch):
            raise RuntimeError("Hub Agent n'a modifié aucun fichier")
        _, status, _ = run_command(["git", "status", "--porcelain"], cwd=str(worktree_path))
        if status.strip():
            run_command(["git", "add", "."], cwd=str(worktree_path))
            commit_msg = f"feat({spec['task_id']}): {spec['title']}"
            code, _, commit_err = run_command(
                ["git", "commit", "-m", commit_msg],
                cwd=str(worktree_path),
            )
            if code != 0:
                raise RuntimeError(f"Échec commit : {commit_err}")
        qa = _enforce_pre_pr_qa(worktree_path, default_branch, spec)
        result["qa_passed"] = True
        result["qa_summary"] = qa.get("summary", "OK")
        final = _finalize_pr(spec, repo_path, worktree_path, branch, result)
        final["qa_passed"] = True
        final["coding_model"] = result.get("coding_model")
        return final
    except Exception as e:
        result["error"] = str(e)
        logger.error("[CodingAgent] [ERREUR] Hub Agent : %s", e)
        raise
    finally:
        if worktree_path.exists():
            run_command(
                ["git", "worktree", "remove", str(worktree_path), "--force"],
                cwd=repo_path,
            )
            logger.info("[CodingAgent] Worktree nettoyé : %s", worktree_path)

def _execute_aider_task_core(spec: dict) -> dict:
    """Worktree → Aider (OpenRouter) → commit → PR."""
    config = get_coding_config()
    repo_path = spec.get("repo_path")
    branch = spec.get(
        "branch_name",
        f"feat/auto-{spec['task_id'].lower()}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
    )
    worktree_path, default_branch, result = _prepare_worktree(spec, branch)
    try:
        prompt = build_claude_prompt(spec)
        files = list(dict.fromkeys(
            (spec.get("files_to_create") or []) + (spec.get("files_to_modify") or [])
        ))
        env = os.environ.copy()
        openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        if not openrouter_key:
            raise RuntimeError("OPENROUTER_API_KEY manquant pour le backend Aider")
        env["OPENROUTER_API_KEY"] = openrouter_key
        env["OPENAI_API_KEY"] = openrouter_key
        env["OPENAI_API_BASE"] = "https://openrouter.ai/api/v1"
        from config.agent_models import get_coding_model_aider
        agent_id = _resolve_spec_agent_id(spec)
        aider_model = get_coding_model_aider(agent_id)
        config_aider = get_coding_config().aider_model
        if config_aider.strip():
            aider_model = config_aider if config_aider.startswith("openrouter/") else f"openrouter/{config_aider}"
        aider_cmd = [
            _resolve_cli("aider"),
            "--model",
            aider_model,
            "--yes",
            "--auto-commits",
            "--message",
            prompt,
        ]
        if files:
            aider_cmd.extend(files)
        logger.info(
            "[CodingAgent] Lancement Aider pour %s (model=%s, timeout=%ss)",
            spec["task_id"],
            aider_model,
            config.timeout_s,
        )
        try:
            proc = subprocess.run(
                aider_cmd,
                cwd=str(worktree_path),
                capture_output=True,
                text=True,
                timeout=config.timeout_s,
                env=env,
            )
        except subprocess.TimeoutExpired as exc:
            partial_output = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            raise RuntimeError(
                f"Aider timeout après {config.timeout_s}s"
                + (f" — sortie partielle : {partial_output[-2000:]}" if partial_output.strip() else "")
            ) from exc
        aider_out = (proc.stdout or "") + (proc.stderr or "")
        result["claude_output"] = aider_out[-8000:]
        if proc.returncode != 0:
            logger.warning("[CodingAgent] Aider exit %s : %s", proc.returncode, aider_out[-500:])
        if not _worktree_has_changes(worktree_path, default_branch):
            raise RuntimeError("Aider n'a modifié aucun fichier")
        _, status, _ = run_command(["git", "status", "--porcelain"], cwd=str(worktree_path))
        if status.strip():
            run_command(["git", "add", "."], cwd=str(worktree_path))
            commit_msg = f"feat({spec['task_id']}): {spec['title']}"
            code, _, commit_err = run_command(
                ["git", "commit", "-m", commit_msg],
                cwd=str(worktree_path),
            )
            if code != 0:
                raise RuntimeError(f"Échec commit : {commit_err}")
        qa = _enforce_pre_pr_qa(worktree_path, default_branch, spec)
        result["qa_passed"] = True
        result["qa_summary"] = qa.get("summary", "OK")
        final = _finalize_pr(spec, repo_path, worktree_path, branch, result)
        final["qa_passed"] = True
        return final
    except Exception as e:
        result["error"] = str(e)
        logger.error("[CodingAgent] [ERREUR] Aider : %s", e)
        raise
    finally:
        if worktree_path.exists():
            run_command(
                ["git", "worktree", "remove", str(worktree_path), "--force"],
                cwd=repo_path,
            )
            logger.info("[CodingAgent] Worktree nettoyé : %s", worktree_path)

