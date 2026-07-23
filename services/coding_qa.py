"""Pre-PR quality gate for the autonomous coding pipeline."""

from __future__ import annotations

import logging
import re
import subprocess
from pathlib import Path

from services.coding_pipeline import DevStack, detect_stack, get_coding_config

logger = logging.getLogger(__name__)

_SOURCE_EXTENSIONS = {".ts", ".tsx", ".js", ".jsx", ".py"}
# Issue-template placeholders only — Expo Router uses (tabs), (auth), etc.
_PLACEHOLDER_NAMES = frozenset(
    {"(aucun)", "(none)", "(n/a)", "aucun", "none", "n/a"}
)
_JUNK_TEXT_RE = re.compile(r"déterminer|todo fixme", re.I)


def _is_junk_path(path: Path) -> bool:
    """Reject template artifacts, not legitimate Expo route groups like (tabs)."""
    if _JUNK_TEXT_RE.search(path.name):
        return True
    for part in path.parts:
        lower = part.lower()
        if lower in _PLACEHOLDER_NAMES:
            return True
        if lower.startswith("(déterminer") or lower.startswith("(determiner"):
            return True
    return False


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
        if _is_junk_path(path):
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
        out = ((result.stdout or "") + (result.stderr or "")).strip()
        return result.returncode, out[-2000:]
    except subprocess.TimeoutExpired:
        return 124, f"Timeout après {timeout}s: {' '.join(cmd[:4])}"
    except Exception as exc:
        return 1, str(exc)


def _check_expo_scaffold(worktree: Path) -> list[str]:
    """Reject PRs that leave default Expo template screens."""
    errors: list[str] = []
    index = worktree / "app" / "(tabs)" / "index.tsx"
    if index.is_file():
        text = index.read_text(encoding="utf-8", errors="ignore")
        if "EditScreenInfo" in text or "Tab One" in text:
            errors.append(
                "Scaffold Expo dans app/(tabs)/index.tsx — remplacer par écran Accueil réel"
            )
    layout = worktree / "app" / "(tabs)" / "_layout.tsx"
    if layout.is_file():
        text = layout.read_text(encoding="utf-8", errors="ignore")
        if re.search(r"title:\s*['\"]Tab One['\"]", text):
            errors.append("Onglet encore 'Tab One' — renommer Accueil")
        if "expo-symbols" in text or "SymbolView" in text:
            errors.append(
                "expo-symbols interdit sur tab bar — utiliser TabBarIcon + MaterialIcons"
            )
    return errors


def _qa_expo(worktree: str) -> list[str]:
    errors: list[str] = []
    root = Path(worktree)
    errors.extend(_check_expo_scaffold(root))
    if not (root / "tsconfig.json").is_file():
        return errors
    code, out = _run_command(["npx", "tsc", "--noEmit"], cwd=worktree)
    if code != 0:
        errors.append(f"tsc --noEmit échoué:\n{out}")
    if (root / "package.json").is_file():
        code, out = _run_command(["npm", "test"], cwd=worktree, timeout=120)
        if code != 0:
            errors.append(f"npm test échoué:\n{out}")
        text = (root / "package.json").read_text(encoding="utf-8", errors="ignore")
        if re.search(r'"expo-[^"]+":\s*"~12\.', text):
            errors.append(
                "expo-* ~12.x incompatible SDK 56 — npx expo install <pkg>"
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
