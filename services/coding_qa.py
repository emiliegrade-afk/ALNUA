"""Pre-PR quality gate for the autonomous coding pipeline."""

from __future__ import annotations

import logging
import re
import subprocess
from pathlib import Path

from services.coding_pipeline import DevStack, detect_stack, get_coding_config

logger = logging.getLogger(__name__)

_SOURCE_EXTENSIONS = {".ts", ".tsx", ".js", ".jsx", ".py"}
_JUNK_NAME_RE = re.compile(r"[\(\)]|déterminer|todo fixme", re.I)


def _changed_files(worktree_path: Path, default_branch: str) -> list[Path]:
    try:
        result = subprocess.run(
            ["git", "diff", f"{default_branch}...HEAD", "--name-only"],
            cwd=str(worktree_path),
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return []
        names = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        return [worktree_path / n for n in names]
    except Exception as exc:
        logger.warning("[CodingQA] diff failed: %s", exc)
        return []


def _check_empty_or_junk_files(
    worktree_path: Path,
    default_branch: str,
) -> list[str]:
    errors: list[str] = []
    for path in _changed_files(worktree_path, default_branch):
        if not path.is_file():
            continue
        name = path.name
        if _JUNK_NAME_RE.search(name) or _JUNK_NAME_RE.search(str(path)):
            errors.append(f"Fichier suspect rejeté : {path.relative_to(worktree_path)}")
            continue
        if path.suffix.lower() not in _SOURCE_EXTENSIONS:
            continue
        try:
            if path.stat().st_size == 0:
                errors.append(f"Fichier vide : {path.relative_to(worktree_path)}")
        except OSError:
            pass
    return errors


def _run_command(cmd: list[str], cwd: str, timeout: int = 180) -> tuple[int, str]:
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        out = ((result.stdout or "") + (result.stderr or "")).strip()
        return result.returncode, out[-2000:]
    except subprocess.TimeoutExpired:
        return 124, f"Timeout après {timeout}s: {' '.join(cmd[:4])}"
    except Exception as exc:
        return 1, str(exc)


def _qa_expo(worktree: str) -> list[str]:
    errors: list[str] = []
    root = Path(worktree)
    if not (root / "tsconfig.json").is_file():
        return errors
    code, out = _run_command(["npx", "tsc", "--noEmit"], cwd=worktree)
    if code != 0:
        errors.append(f"tsc --noEmit échoué:\n{out}")
    pkg = root / "package.json"
    if pkg.is_file():
        text = pkg.read_text(encoding="utf-8", errors="ignore")
        if re.search(r'"expo-[^"]+":\s*"~12\.', text):
            errors.append(
                "expo-* en version ~12.x incompatible avec SDK 56 — utiliser npx expo install <pkg>"
            )
    return errors


def _qa_nextjs(worktree: str) -> list[str]:
    if not Path(worktree, "tsconfig.json").is_file():
        return []
    code, out = _run_command(["npx", "tsc", "--noEmit"], cwd=worktree)
    if code != 0:
        return [f"tsc --noEmit échoué:\n{out}"]
    return []


def _qa_python(worktree: str) -> list[str]:
    tests_dir = Path(worktree) / "tests"
    if not tests_dir.is_dir():
        return []
    code, out = _run_command(
        ["python", "-m", "pytest", "tests/", "-q", "--tb=line"],
        cwd=worktree,
        timeout=300,
    )
    if code != 0:
        return [f"pytest échoué:\n{out}"]
    return []


def run_pre_pr_qa(
    worktree_path: str,
    spec: dict,
    default_branch: str,
) -> dict:
    """
    Run mandatory checks before opening a PR.

    Returns: {passed, errors, summary, stack}
    """
    cfg = get_coding_config()
    if not cfg.qa_required:
        return {"passed": True, "errors": [], "summary": "QA désactivée", "stack": ""}

    root = Path(worktree_path)
    stack = detect_stack(spec)
    errors: list[str] = []

    errors.extend(_check_empty_or_junk_files(root, default_branch))

    if stack == DevStack.REACT_NATIVE_EXPO:
        errors.extend(_qa_expo(worktree_path))
    elif stack == DevStack.NEXTJS:
        errors.extend(_qa_nextjs(worktree_path))
    elif stack == DevStack.PYTHON_FASTAPI:
        errors.extend(_qa_python(worktree_path))

    passed = len(errors) == 0
    summary = "; ".join(e.split("\n")[0][:120] for e in errors[:3]) if errors else "OK"
    if not passed:
        logger.warning("[CodingQA] Échec %s: %s", spec.get("task_id"), summary)

    return {
        "passed": passed,
        "errors": errors,
        "summary": summary,
        "stack": stack.value,
    }
