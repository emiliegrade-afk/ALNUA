"""

skill_coding_agent.py



Wraps Claude Code CLI pour exécution autonome dans un git worktree isolé.



Flux :

1. Valide la spec JSON reçue

2. Crée un git worktree isolé (jamais de code dans le répertoire actif)

3. Lance `claude --print --allowedTools edit,write,bash` avec le prompt construit depuis la spec

4. Capture stdout/stderr

5. Commit + push la branche

6. Ouvre une PR via `gh pr create`

7. Nettoie le worktree

8. Retourne le résultat avec lien PR



Input (dict) :

{

  "task_id": "TASK-001",

  "title": "Ajouter endpoint /health",

  "description": "...",

  "files_to_create": ["api/health.py"],

  "files_to_modify": ["api/main.py"],

  "tests_to_pass": ["tests/test_health.py"],

  "repo_path": "/path/to/repo",

  "branch_name": "feat/task-001-health",

  "pr_title": "feat: endpoint /health",

  "pr_body": "Closes #42\n\n..."

}



Output (dict) :

{

  "success": True/False,

  "pr_url": "https://github.com/...",

  "branch": "feat/task-001-health",

  "commit_sha": "abc123",

  "claude_output": "...",

  "error": None / "message d'erreur"

}

"""




import logging

import os

import shutil

import subprocess

from datetime import datetime

from pathlib import Path



from services.coding_pipeline import (

    detect_stack,

    get_coding_config,

    resolve_default_branch,

    resolve_pr_base_branch,

    stack_expert_role,

    stack_rules_block,

)



logger = logging.getLogger(__name__)


def _resolve_cli(name: str) -> str:
    """Resolve CLI binary — uvicorn on Windows often lacks npm in PATH."""
    import os
    import sys

    if sys.platform == "win32":
        npm_bin = Path.home() / "AppData" / "Roaming" / "npm"
        if npm_bin.is_dir():
            path = os.environ.get("PATH", "")
            if str(npm_bin) not in path:
                os.environ["PATH"] = f"{npm_bin}{os.pathsep}{path}"
    resolved = shutil.which(name)
    if sys.platform == "win32":
        cmd_candidate = shutil.which(f"{name}.cmd")
        if cmd_candidate:
            resolved = cmd_candidate
        elif resolved and not resolved.lower().endswith((".exe", ".cmd", ".bat")):
            sibling = Path(resolved).with_suffix(".cmd")
            if sibling.is_file():
                resolved = str(sibling)
    if not resolved:
        raise FileNotFoundError(
            f"{name} CLI introuvable (PATH). Ex: npm i -g @anthropic-ai/claude-code"
        )
    return resolved


def _cleanup_stale_worktree(repo_path: str, branch: str, worktree_path: Path) -> None:
    """Remove leftover worktree/branch from a prior failed run (allows retry)."""
    if worktree_path.exists():
        run_command(
            ["git", "worktree", "remove", str(worktree_path), "--force"],
            cwd=repo_path,
        )
        if worktree_path.exists():
            shutil.rmtree(worktree_path, ignore_errors=True)
    run_command(["git", "worktree", "prune"], cwd=repo_path)
    _, listed, _ = run_command(["git", "branch", "--list", branch], cwd=repo_path)
    if branch in (listed or ""):
        run_command(["git", "branch", "-D", branch], cwd=repo_path)





def build_claude_prompt(spec: dict) -> str:

    """

    Construit le prompt complet pour Claude Code depuis la spec JSON.

    Détecte la stack (Expo, Next.js, FastAPI) pour adapter les règles.

    """

    files_create = spec.get("files_to_create") or ["(détermine toi-même)"]

    files_modify = spec.get("files_to_modify") or ["(détermine toi-même)"]

    tests_pass = spec.get("tests_to_pass") or [

        "(aucun spécifié — crée des tests appropriés)"

    ]

    stack = detect_stack(spec)

    role = stack_expert_role(stack)

    rules = stack_rules_block(stack)



    prompt = f"""Tu es un {role} travaillant sur un projet ALNUA.



{rules}



TÂCHE : {spec['title']}

ID : {spec['task_id']}



DESCRIPTION COMPLÈTE :

{spec['description']}



FICHIERS POTENTIELLEMENT CONCERNÉS :

- À créer : {', '.join(files_create)}

- À modifier : {', '.join(files_modify)}



CRITÈRES DE SUCCÈS :

- Le code est fonctionnel et testé

- Les tests suivants passent : {', '.join(tests_pass)}

- Pas de debug oublié (print/console.log en prod)

- Gestion d'erreurs explicite



RÈGLES GÉNÉRALES ALNUA :

- Ne pas modifier les fichiers hors scope de la tâche

- Commit final avec message : "feat({spec['task_id']}): {spec['title']}"



IMPORTANT : Travaille uniquement dans le répertoire courant. Respecte la structure existante du repo.

"""

    return prompt





def run_command(

    cmd: list[str], cwd: str | None = None, timeout: int = 60

) -> tuple[int, str, str]:

    """

    Lance une commande shell et retourne (returncode, stdout, stderr).

    """

    try:

        from services.cli_paths import ensure_coding_cli_path, resolve_cli

        ensure_coding_cli_path()
        argv = list(cmd)
        if argv:
            try:
                argv[0] = resolve_cli(argv[0])
            except FileNotFoundError:
                pass

        result = subprocess.run(

            argv,

            cwd=cwd,

            capture_output=True,

            text=True,

            timeout=timeout,

        )

        return result.returncode, result.stdout, result.stderr

    except subprocess.TimeoutExpired as exc:

        logger.error("[CodingAgent] Command timeout (%ss): %s", timeout, cmd)

        stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")

        stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")

        return 124, stdout, stderr or f"Command timed out after {timeout}s"





def _prepare_worktree(spec: dict, branch: str) -> tuple[Path, str, dict]:
    """Create isolated worktree and return (path, default_branch, partial result)."""
    config = get_coding_config()
    repo_path = spec.get("repo_path")
    worktree_path = Path(repo_path) / "worktrees" / branch.replace("/", "-")
    default_branch = resolve_default_branch(repo_path)

    result: dict = {
        "success": False,
        "pr_url": None,
        "branch": branch,
        "commit_sha": None,
        "claude_output": "",
        "stack": detect_stack(spec).value,
        "backend": config.backend,
        "error": None,
    }

    logger.info("[CodingAgent] Création worktree : %s", worktree_path)
    worktree_path.parent.mkdir(parents=True, exist_ok=True)
    _cleanup_stale_worktree(repo_path, branch, worktree_path)

    code, _out, err = run_command(
        ["git", "worktree", "add", str(worktree_path), "-b", branch, default_branch],
        cwd=repo_path,
    )
    if code != 0:
        raise RuntimeError(f"Échec création worktree : {err}")

    env_src = Path(repo_path) / ".env"
    env_dst = worktree_path / ".env"
    if env_src.is_file() and not env_dst.exists():
        shutil.copy2(env_src, env_dst)

    return worktree_path, default_branch, result


def _enforce_pre_pr_qa(worktree_path: Path, default_branch: str, spec: dict) -> dict:
    """Run QA gate; raises if checks fail."""
    # Agents sometimes create placeholder filenames from issue templates.
    for junk in worktree_path.glob("(aucun)"):
        junk.unlink(missing_ok=True)
    from services.coding_qa import run_pre_pr_qa

    qa = run_pre_pr_qa(str(worktree_path), spec, default_branch)
    if not qa["passed"]:
        detail = "\n".join(qa.get("errors") or [qa.get("summary", "QA failed")])
        raise RuntimeError(f"QA pre-PR échouée ({qa.get('stack')}): {detail[:800]}")
    return qa


def _finalize_pr(
    spec: dict,
    repo_path: str,
    worktree_path: Path,
    branch: str,
    result: dict,
) -> dict:
    """Push branch, open PR, set success fields."""
    config = get_coding_config()

    _, sha, _ = run_command(["git", "rev-parse", "HEAD"], cwd=str(worktree_path))
    result["commit_sha"] = sha.strip()

    code, _, push_err = run_command(
        ["git", "push", "-u", "origin", branch],
        cwd=str(worktree_path),
    )
    if code != 0:
        raise RuntimeError(f"Échec push : {push_err}")

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

    code, pr_out, pr_err = run_command(pr_cmd, cwd=repo_path)
    if code != 0:
        # Optional label — academy repo may not define it
        pr_cmd_label = pr_cmd + ["--label", "auto-generated"]
        code, pr_out, pr_err = run_command(pr_cmd_label, cwd=repo_path)
    if code != 0:
        raise RuntimeError(f"Échec création PR : {pr_err}")

    pr_url = pr_out.strip().split("\n")[-1]
    result["pr_url"] = pr_url
    result["success"] = True
    logger.info("[CodingAgent] [OK] PR créée : %s", pr_url)
    return result


def _worktree_has_changes(worktree_path: Path, default_branch: str) -> bool:
    """True if branch has file changes vs default branch."""
    _, diff_out, _ = run_command(
        ["git", "diff", default_branch, "--name-only"],
        cwd=str(worktree_path),
    )
    if diff_out.strip():
        return True
    _, status, _ = run_command(["git", "status", "--porcelain"], cwd=str(worktree_path))
    return bool(status.strip())


def _execute_hub_task_core(spec: dict) -> dict:
    """Worktree → Hub Agent (Cursor-like loop) → commit → PR."""
    from services.hub_coding_agent import run_hub_coding_loop

    config = get_coding_config()
    repo_path = spec.get("repo_path")
    branch = spec.get(
        "branch_name",
        f"feat/auto-{spec['task_id'].lower()}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
    )
    agent_id = spec.get("agent_id", "dev_app")

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

        agent_id = spec.get("agent_id", "dev_app")
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

    repo_path = spec.get("repo_path")

    branch = spec.get(

        "branch_name",

        f"feat/auto-{spec['task_id'].lower()}-{datetime.now().strftime('%Y%m%d%H%M%S')}",

    )

    worktree_path = Path(repo_path) / "worktrees" / branch.replace("/", "-")



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





def execute_coding_task(

    spec: dict,

    telegram_notify_fn=None,

) -> dict:

    """

    Point d'entrée principal — avec retry intelligent.

    Consulte le journal d'erreurs avant chaque tentative.

    """

    from skills.skill_retry_loop import retry_with_learning



    def _attempt(learning_context: str) -> dict:

        from services.coding_learning import enrich_spec_with_lessons, record_qa_failure

        enriched_spec = enrich_spec_with_lessons(dict(spec))

        if learning_context:

            enriched_spec["description"] = spec["description"] + learning_context

        try:
            return _execute_coding_task_core(enriched_spec)
        except RuntimeError as exc:
            if "QA pre-PR" in str(exc) or "QA" in str(exc):
                record_qa_failure(
                    agent_name=spec.get("agent_id", "dev_app"),
                    task_id=spec.get("task_id"),
                    repo_slug=spec.get("repo_slug"),
                    error_message=str(exc),
                    task_context=spec.get("title", ""),
                )
            raise



    retry_result = retry_with_learning(

        agent_name=spec.get("agent_id", "dev_app"),

        task_fn=_attempt,

        task_id=spec.get("task_id"),

        task_context=f"Tâche : {spec.get('title')}\nRepo : {spec.get('repo_path')}",

        max_attempts=3,

        telegram_notify_fn=telegram_notify_fn,

    )



    if retry_result["success"]:

        return retry_result["result"]



    return {

        "success": False,

        "pr_url": None,

        "branch": spec.get("branch_name"),

        "commit_sha": None,

        "claude_output": "",

        "error": retry_result["error"],

        "escalated": retry_result["escalated"],

    }


