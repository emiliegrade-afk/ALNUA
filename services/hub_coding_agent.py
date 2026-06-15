"""Hub coding agent — Cursor-like tool loop (read / write / run / grep).

Model is always resolved via config.agent_models.get_coding_model_for_agent —
never chosen by Aider or an external default.
"""

from __future__ import annotations

import logging
import re
import subprocess
import time
from pathlib import Path
from typing import Any

from agents.base import LLMClient, parse_json_response, resolve_openrouter_model
from config.agent_models import get_coding_model_for_agent, normalize_agent_id
from services.coding_pipeline import detect_stack, stack_rules_block

logger = logging.getLogger(__name__)

_SYSTEM = """Tu es un agent de développement ALNUA dans un dépôt git isolé (worktree).
Tu dois livrer la tâche en agissant comme un IDE : lire, éditer, exécuter des commandes, corriger.

À CHAQUE tour, réponds UNIQUEMENT avec un objet JSON valide (pas de markdown autour).

Actions disponibles :
- list_dir   : {"action":"list_dir","path":"."}
- read_file  : {"action":"read_file","path":"chemin/relatif"}
- write_file : {"action":"write_file","path":"chemin","content":"contenu complet du fichier"}
- run_cmd    : {"action":"run_cmd","command":"npm test","cwd":"."}
- grep       : {"action":"grep","pattern":"regex","path":"."}
- done       : {"action":"done","summary":"ce qui a été fait"}

Règles :
- path et cwd sont relatifs à la racine du worktree
- Après run_cmd, lis stdout/stderr dans le message utilisateur suivant
- Ne crée jamais de fichier vide
- Pas de noms de fichiers suspects : (aucun), parenthèses seules, etc.
- Expo SDK 56 : npx expo install pour les deps expo-*
- Quand les tests/tsc passent et le code est prêt : action done
"""

_CMD_ALLOW = re.compile(
    r"^(npm|npx|node|python|pytest|git|tsc|expo|yarn|pnpm)\b",
    re.I,
)


def _safe_path(root: Path, rel: str) -> Path:
    rel = (rel or ".").strip().lstrip("/\\")
    resolved = (root / rel).resolve()
    root_res = root.resolve()
    if not str(resolved).startswith(str(root_res)):
        raise ValueError(f"Chemin hors worktree : {rel}")
    return resolved


def _run_shell(command: str, cwd: Path, timeout: int = 180) -> str:
    if not _CMD_ALLOW.match(command.strip()):
        return f"[refusé] Commande non autorisée : {command[:80]}"
    try:
        proc = subprocess.run(
            command,
            cwd=str(cwd),
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        tail = out[-4000:] if len(out) > 4000 else out
        return f"exit={proc.returncode}\n{tail}"
    except subprocess.TimeoutExpired:
        return f"[timeout {timeout}s] {command[:60]}"
    except Exception as exc:
        return f"[erreur] {exc}"


def _grep(root: Path, pattern: str, subpath: str) -> str:
    try:
        base = _safe_path(root, subpath)
        proc = subprocess.run(
            ["rg", "-n", "--max-count", "30", pattern, str(base)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        out = (proc.stdout or proc.stderr or "")[:4000]
        return out or "(aucun match)"
    except FileNotFoundError:
        return "[grep] ripgrep (rg) non installé — utilise read_file / list_dir"
    except Exception as exc:
        return f"[grep erreur] {exc}"


def _execute_action(root: Path, action: dict[str, Any]) -> str:
    kind = (action.get("action") or "").strip().lower()
    if kind == "list_dir":
        base = _safe_path(root, action.get("path") or ".")
        if not base.is_dir():
            return f"Pas un dossier : {base}"
        entries = sorted(base.iterdir())[:80]
        lines = [
            f"{'[D]' if p.is_dir() else '[F]'} {p.name}"
            for p in entries
        ]
        return "\n".join(lines) or "(vide)"
    if kind == "read_file":
        path = _safe_path(root, action.get("path") or "")
        if not path.is_file():
            return f"Fichier introuvable : {path.relative_to(root)}"
        text = path.read_text(encoding="utf-8", errors="replace")
        if len(text) > 12000:
            return text[:12000] + "\n...[tronqué]"
        return text
    if kind == "write_file":
        path = _safe_path(root, action.get("path") or "")
        content = action.get("content")
        if content is None:
            return "write_file requiert content"
        if not str(content).strip():
            return "Refus : fichier vide interdit"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(content), encoding="utf-8")
        return f"OK écrit {path.relative_to(root)} ({len(str(content))} chars)"
    if kind == "run_cmd":
        cwd = _safe_path(root, action.get("cwd") or ".")
        return _run_shell(str(action.get("command") or ""), cwd)
    if kind == "grep":
        return _grep(root, str(action.get("pattern") or ""), str(action.get("path") or "."))
    if kind == "done":
        return "__DONE__"
    return f"Action inconnue : {kind}"


def _parse_action(raw: str) -> dict[str, Any]:
    try:
        return parse_json_response(raw)
    except Exception:
        m = re.search(r"\{[\s\S]*\}", raw)
        if m:
            return parse_json_response(m.group(0))
        raise ValueError(f"JSON action invalide : {raw[:200]}")


def run_hub_coding_loop(
    worktree_path: str | Path,
    spec: dict[str, Any],
    *,
    max_turns: int = 30,
    timeout_s: int = 1800,
) -> dict[str, Any]:
    """
    Cursor-like agent loop in an isolated worktree.

    Returns: {success, turns, log, summary, model, error?}
    """
    root = Path(worktree_path)
    agent_id = normalize_agent_id(spec.get("agent_id") or "dev_app")
    model_slug = get_coding_model_for_agent(agent_id)
    model_api = resolve_openrouter_model(agent_id)

    stack = detect_stack(spec)
    user_goal = f"""TÂCHE : {spec.get('title', '')}
ID : {spec.get('task_id', '')}

{spec.get('description', '')}

{stack_rules_block(stack)}

Fichiers suggérés à créer : {', '.join(spec.get('files_to_create') or [])}
Fichiers suggérés à modifier : {', '.join(spec.get('files_to_modify') or [])}
Tests : {', '.join(spec.get('tests_to_pass') or spec.get('tests') or [])}
"""

    llm = LLMClient()
    messages: list[dict[str, str]] = [{"role": "user", "content": user_goal}]
    log_lines: list[str] = []
    summary = ""
    started = time.monotonic()

    for turn in range(1, max_turns + 1):
        if time.monotonic() - started > timeout_s:
            return {
                "success": False,
                "turns": turn - 1,
                "log": "\n".join(log_lines),
                "summary": summary,
                "model": model_slug,
                "error": f"Timeout global {timeout_s}s",
            }

        logger.info("[HubCoding] %s turn %s/%s model=%s", agent_id, turn, max_turns, model_slug)
        raw = llm.chat(
            system=_SYSTEM,
            messages=messages,
            model=model_api,
            agent_id=agent_id,
            method_name="hub_coding_agent",
            temperature=0.2,
            max_tokens=8192,
        )
        log_lines.append(f"--- turn {turn} ---\n{raw[:1500]}")

        try:
            action = _parse_action(raw)
        except Exception as exc:
            messages.append({"role": "assistant", "content": raw})
            messages.append(
                {
                    "role": "user",
                    "content": f"Format invalide ({exc}). Renvoie UNIQUEMENT un JSON action valide.",
                }
            )
            continue

        if action.get("action") == "done":
            summary = str(action.get("summary") or "done")
            return {
                "success": True,
                "turns": turn,
                "log": "\n".join(log_lines),
                "summary": summary,
                "model": model_slug,
            }

        try:
            result = _execute_action(root, action)
        except Exception as exc:
            result = f"[action error] {exc}"

        if result == "__DONE__":
            summary = str(action.get("summary") or "done")
            return {
                "success": True,
                "turns": turn,
                "log": "\n".join(log_lines),
                "summary": summary,
                "model": model_slug,
            }

        messages.append({"role": "assistant", "content": raw})
        messages.append(
            {
                "role": "user",
                "content": f"Résultat de {action.get('action')}:\n{result}\n\nProchaine action JSON.",
            }
        )

    return {
        "success": False,
        "turns": max_turns,
        "log": "\n".join(log_lines),
        "summary": summary,
        "model": model_slug,
        "error": f"Max turns ({max_turns}) atteint sans done",
    }
