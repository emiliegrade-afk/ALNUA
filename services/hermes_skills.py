"""Load Hermes Agent SKILL.md procedural memory from a local clone (agentskills.io format)."""

from __future__ import annotations

import logging
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Relative paths under skills/ — curated for ALNUA (no copy into repo).
ALNUA_HERMES_BUNDLES: dict[str, list[str]] = {
    "coding": [
        "github/github-pr-workflow",
        "github/github-code-review",
        "github/github-issues",
        "github/codebase-inspection",
        "software-development/systematic-debugging",
        "software-development/test-driven-development",
        "software-development/requesting-code-review",
        "software-development/plan",
        "software-development/simplify-code",
    ],
    "coach": [
        "software-development/plan",
        "software-development/spike",
        "software-development/systematic-debugging",
        "software-development/test-driven-development",
    ],
    "qa": [
        "software-development/systematic-debugging",
        "software-development/test-driven-development",
        "github/github-code-review",
    ],
    "spec": [
        "software-development/plan",
        "software-development/spike",
    ],
}

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _default_skills_root() -> Path:
    win = Path(r"C:\Dev\hermes-agent-main\skills")
    if win.is_dir():
        return win
    return Path(__file__).resolve().parents[1] / "data" / "hermes_skills"


def get_hermes_skills_root() -> Path | None:
    """Resolved skills root, or None if missing."""
    try:
        from config.settings import get_settings

        configured = (get_settings().hermes_skills_root or "").strip()
        if configured:
            p = Path(configured).expanduser().resolve()
            if p.is_dir():
                return p
    except Exception:
        pass
    env = os.getenv("HERMES_SKILLS_ROOT", "").strip()
    if env:
        p = Path(env).expanduser().resolve()
        if p.is_dir():
            return p
    fallback = _default_skills_root()
    return fallback if fallback.is_dir() else None


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    meta: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            meta[key.strip()] = val.strip().strip('"').strip("'")
    body = text[m.end() :]
    return meta, body


def _skill_md_path(root: Path, rel: str) -> Path:
    rel = rel.strip().replace("\\", "/").strip("/")
    path = (root / rel / "SKILL.md").resolve()
    if not str(path).startswith(str(root.resolve())):
        raise ValueError("skill path escape")
    return path


@lru_cache(maxsize=256)
def load_skill_body(rel: str) -> str | None:
    """Load one skill body (without YAML frontmatter)."""
    root = get_hermes_skills_root()
    if not root:
        return None
    path = _skill_md_path(root, rel)
    if not path.is_file():
        logger.debug("[HermesSkills] missing %s", rel)
        return None
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
        _, body = _parse_frontmatter(raw)
        return body.strip()
    except Exception as exc:
        logger.warning("[HermesSkills] read %s: %s", rel, exc)
        return None


def load_skill_meta(rel: str) -> dict[str, Any] | None:
    root = get_hermes_skills_root()
    if not root:
        return None
    path = _skill_md_path(root, rel)
    if not path.is_file():
        return None
    raw = path.read_text(encoding="utf-8", errors="replace")
    meta, _ = _parse_frontmatter(raw)
    return {
        "id": rel,
        "name": meta.get("name", rel.split("/")[-1]),
        "description": meta.get("description", ""),
        "path": str(path),
    }


def list_catalog() -> dict[str, Any]:
    root = get_hermes_skills_root()
    if not root:
        return {
            "available": False,
            "root": None,
            "skills": [],
            "bundles": ALNUA_HERMES_BUNDLES,
        }
    skills: list[dict[str, Any]] = []
    for rel in sorted({s for group in ALNUA_HERMES_BUNDLES.values() for s in group}):
        meta = load_skill_meta(rel)
        if meta:
            skills.append(meta)
    return {
        "available": True,
        "root": str(root),
        "skills": skills,
        "bundles": ALNUA_HERMES_BUNDLES,
    }


def load_skills_for_bundle(bundle: str, *, max_chars: int = 10_000) -> str:
    """Concatenate skill bodies for injection into agent prompts."""
    root = get_hermes_skills_root()
    if not root:
        return ""
    rels = ALNUA_HERMES_BUNDLES.get(bundle, [])
    if not rels:
        return ""
    parts: list[str] = []
    used = 0
    for rel in rels:
        body = load_skill_body(rel)
        if not body:
            continue
        chunk = f"\n\n## [Hermes skill: {rel}]\n{body}"
        if used + len(chunk) > max_chars:
            remaining = max_chars - used
            if remaining > 200:
                parts.append(chunk[:remaining] + "\n…[tronqué]")
            break
        parts.append(chunk)
        used += len(chunk)
    if not parts:
        return ""
    header = (
        f"# Compétences procédurales Hermes (bundle `{bundle}`)\n"
        f"Source: {root}\n"
    )
    return header + "".join(parts)


def inject_hermes_context(bundle: str, base_prompt: str, *, max_chars: int = 8000) -> str:
    """Append Hermes skills to a system prompt when the clone is present."""
    extra = load_skills_for_bundle(bundle, max_chars=max_chars)
    if not extra:
        return base_prompt
    return f"{base_prompt}\n\n---\n{extra}"
