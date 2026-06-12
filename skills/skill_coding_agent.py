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

import json
import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

CLAUDE_CODE_TIMEOUT = 600  # 10 minutes max par tâche
MAX_WORKTREES = 8  # max 8 tâches parallèles


def build_claude_prompt(spec: dict) -> str:
    """
    Construit le prompt complet pour Claude Code depuis la spec JSON.
    Le prompt doit être précis, actionnable, avec critères de succès clairs.
    """
    files_create = spec.get("files_to_create") or ["(détermine toi-même)"]
    files_modify = spec.get("files_to_modify") or ["(détermine toi-même)"]
    tests_pass = spec.get("tests_to_pass") or [
        "(aucun spécifié — crée des tests appropriés)"
    ]

    prompt = f"""Tu es un expert développeur Python/FastAPI/React Native travaillant sur le projet Hub ALNUA.

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
- Pas de print() de debug oublié
- Docstrings sur toutes les fonctions publiques
- Gestion d'erreurs explicite (try/except avec logging)

RÈGLES ALNUA :
- Max 5-7 tools par fonction
- Logging via logger = logging.getLogger(__name__), jamais print()
- Variables d'env via os.getenv() + valeur par défaut
- Ne pas modifier les fichiers hors scope de la tâche
- Commit final avec message : "feat({spec['task_id']}): {spec['title']}"

IMPORTANT : Travaille uniquement dans le répertoire courant. N'installe pas de nouvelles dépendances sans les ajouter à requirements.txt.
"""
    return prompt


def run_command(
    cmd: list[str], cwd: str | None = None, timeout: int = 60
) -> tuple[int, str, str]:
    """
    Lance une commande shell et retourne (returncode, stdout, stderr).
    """
    try:
        result = subprocess.run(
            cmd,
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


def _execute_coding_task_core(spec: dict) -> dict:
    """
    Single coding pipeline run (worktree → Claude Code → commit → PR).
    Raises on logical failure so retry_with_learning can catch and retry.
    """
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
        "error": None,
    }

    try:
        # 1. Créer le worktree git isolé
        logger.info("[CodingAgent] Création worktree : %s", worktree_path)
        worktree_path.parent.mkdir(parents=True, exist_ok=True)
        code, _out, err = run_command(
            ["git", "worktree", "add", str(worktree_path), "-b", branch],
            cwd=repo_path,
        )
        if code != 0:
            raise RuntimeError(f"Échec création worktree : {err}")

        # 2. Construire le prompt
        prompt = build_claude_prompt(spec)

        # 3. Lancer Claude Code CLI en mode non-interactif
        logger.info("[CodingAgent] Lancement Claude Code pour %s", spec["task_id"])
        code, claude_out, claude_err = run_command(
            [
                "claude",
                "--print",
                "--allowedTools",
                "edit,write,bash,read",
                "--max-turns",
                "20",
                prompt,
            ],
            cwd=str(worktree_path),
            timeout=CLAUDE_CODE_TIMEOUT,
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

        code, pr_out, pr_err = run_command(
            [
                "gh",
                "pr",
                "create",
                "--title",
                pr_title,
                "--body",
                pr_body,
                "--head",
                branch,
                "--label",
                "auto-generated",
            ],
            cwd=repo_path,
        )
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
        enriched_spec = dict(spec)
        if learning_context:
            enriched_spec["description"] = spec["description"] + learning_context
        return _execute_coding_task_core(enriched_spec)

    retry_result = retry_with_learning(
        agent_name="DevApp",
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
