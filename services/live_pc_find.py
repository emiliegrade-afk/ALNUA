"""Find a folder or file on this PC — user profile roots only (DEC-039)."""

from __future__ import annotations

import json
import logging
import os
import re
import threading
from pathlib import Path
from typing import Any

from config.settings import get_settings
from services.input_sanitizer import sanitize_user_input

logger = logging.getLogger(__name__)

BUDGET_SECONDS = 8
MAX_DEPTH = 5
MAX_HITS = 8
MAX_VISITS = 4000
BLOCKED = frozenset(
    {
        ".git",
        ".ssh",
        ".gnupg",
        "appdata",
        "ntuser.dat",
        "system volume information",
        "$recycle.bin",
        "node_modules",
        "__pycache__",
    }
)
DANGEROUS_SUFFIX = frozenset(
    {".exe", ".bat", ".cmd", ".ps1", ".msi", ".scr", ".com", ".vbs", ".js"}
)
_VERB_RE = re.compile(
    r"\b(cherche|trouve|retrouve|où\s+est|ou\s+est|ouvre(?:-moi)?|ouvrir|affiche|montre)\b",
    re.IGNORECASE,
)
_PLACE_RE = re.compile(
    r"(dossier|fichier|explorateur|sur le pc|sur mon pc|sur l['’ ]ordinateur|sur mon ordinateur)",
    re.IGNORECASE,
)
_EXTRACT_NAMED = re.compile(
    r"(?:dossier|fichier)(?:\s+nommé)?\s+(?:le\s+|la\s+|l['’]|un\s+|une\s+)?"
    r"[«\"']?([^»\"'\n,]{2,80})",
    re.IGNORECASE,
)
_EXTRACT_ON_PC = re.compile(
    r"(?:cherche|trouve|retrouve|où\s+est|ou\s+est|ouvre(?:-moi)?|ouvrir)\s+"
    r"(?:le\s+|la\s+|l['’]|un\s+|une\s+)?"
    r"[«\"']?([^»\"'\n,]{2,80}?)\s+sur\s+(?:le\s+|mon\s+|l['’])?(?:pc|ordinateur)",
    re.IGNORECASE,
)
_OPEN_VERB_RE = re.compile(r"\b(ouvre(?:-moi)?|ouvrir|affiche|montre)\b", re.IGNORECASE)
_TRAIL_RE = re.compile(
    r"\s+(s['’]il te pla[iî]t|stp|merci|sur (?:le |mon )?(?:pc|ordinateur))\s*$",
    re.IGNORECASE,
)


def wants_find(instruction: str) -> bool:
    text = instruction or ""
    return bool(_VERB_RE.search(text) and _PLACE_RE.search(text))


def maybe_find(instruction: str) -> str | None:
    if not wants_find(instruction):
        return None
    return run_find(instruction)


def run_find(instruction: str, *, roots: list[Path] | None = None) -> str:
    settings = get_settings()
    if not settings.live_pc_actions_enabled:
        return (
            "Je ne parcours pas ce PC tant que LIVE_PC_ACTIONS_ENABLED n'est pas à 1. "
            "Même alors : Bureau, Documents, Téléchargements seulement — pas tout le disque."
        )
    query = extract_find_query(instruction)
    if not query:
        return (
            "Dis le nom du dossier ou du fichier. "
            "Exemple : « cherche le dossier factures » ou « ouvre le dossier ALNUA »."
        )
    hits = search_roots(query, roots=roots or default_roots(settings))
    if not hits:
        return (
            f"Rien trouvé pour « {query} » dans Bureau / Documents / Téléchargements "
            "(et le dossier extra si LIVE_PC_ALLOWED_DIR est défini)."
        )
    opened = ""
    should_open = bool(_OPEN_VERB_RE.search(instruction)) or len(hits) == 1
    if should_open:
        opened = _open_best(hits)
    return _format(query, hits, opened)


def extract_find_query(instruction: str) -> str:
    text = sanitize_user_input(instruction or "", max_length=200, redact_pii_enabled=False)
    match = _EXTRACT_ON_PC.search(text) or _EXTRACT_NAMED.search(text)
    raw = match.group(1) if match else ""
    raw = _TRAIL_RE.sub("", raw).strip(" .,:;«»\"'")
    if ".." in raw or "/" in raw or "\\" in raw:
        return ""
    return raw[:80]


def default_roots(settings: object | None = None) -> list[Path]:
    cfg = settings or get_settings()
    home = Path.home()
    candidates = [
        home / "Desktop",
        home / "Documents",
        home / "Downloads",
        home / "OneDrive" / "Desktop",
        home / "OneDrive" / "Documents",
        home / "OneDrive" / "Bureau",
    ]
    extra = str(getattr(cfg, "live_pc_allowed_dir", "") or "").strip()
    if extra:
        candidates.append(Path(extra).expanduser())
    out: list[Path] = []
    seen: set[str] = set()
    for path in candidates:
        try:
            resolved = path.resolve()
        except OSError:
            continue
        if not resolved.is_dir():
            continue
        key = str(resolved).lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(resolved)
    return out


def search_roots(query: str, *, roots: list[Path]) -> list[dict[str, Any]]:
    needle = query.casefold()
    holder: list[list[dict[str, Any]]] = [[]]

    def _run() -> None:
        found: list[dict[str, Any]] = []
        visits = 0
        for root in roots:
            visits = _walk(root, root, needle, found, 0, visits)
            if len(found) >= MAX_HITS or visits >= MAX_VISITS:
                break
        found.sort(key=lambda h: (0 if h["kind"] == "folder" else 1, len(h["name"])))
        holder[0] = found[:MAX_HITS]

    thread = threading.Thread(target=_run, daemon=True, name="live-pc-find")
    thread.start()
    thread.join(BUDGET_SECONDS)
    return holder[0]


def _walk(
    root: Path,
    current: Path,
    needle: str,
    found: list[dict[str, Any]],
    depth: int,
    visits: int,
) -> int:
    if depth > MAX_DEPTH or visits >= MAX_VISITS or len(found) >= MAX_HITS:
        return visits
    try:
        entries = list(os.scandir(current))
    except OSError:
        return visits
    for entry in entries:
        visits += 1
        name = entry.name
        if name.startswith(".") or name.casefold() in BLOCKED:
            continue
        try:
            path = Path(entry.path).resolve()
        except OSError:
            continue
        if not _inside(path, root):
            continue
        kind = "folder" if entry.is_dir(follow_symlinks=False) else "file"
        if needle in name.casefold():
            found.append({"kind": kind, "name": name, "path": str(path)})
            if len(found) >= MAX_HITS:
                return visits
        if kind == "folder" and depth < MAX_DEPTH:
            visits = _walk(root, path, needle, found, depth + 1, visits)
        if visits >= MAX_VISITS:
            break
    return visits


def _inside(path: Path, root: Path) -> bool:
    try:
        return path.is_relative_to(root)
    except (OSError, ValueError):
        return False


def _open_best(hits: list[dict[str, Any]]) -> str:
    for hit in hits:
        path = Path(str(hit["path"]))
        if hit["kind"] == "file" and path.suffix.lower() in DANGEROUS_SUFFIX:
            continue
        if not path.exists():
            continue
        _reveal(path)
        return str(path)
    return ""


def _reveal(path: Path) -> None:
    if os.name == "nt":
        os.startfile(str(path))  # noqa: S606 — path already fenced to user roots
        return
    import subprocess

    subprocess.Popen(["xdg-open", str(path)], shell=False)  # noqa: S603


def _format(query: str, hits: list[dict[str, Any]], opened: str) -> str:
    items = [f"{hit['kind']} — {hit['path']}" for hit in hits]
    payload = {"title": f"Sur le PC : {query}", "items": items}
    lines = [f"Trouvé {len(hits)} résultat(s) pour « {query} »."]
    if opened:
        lines.append(f"Ouvert : {opened}")
    lines.append("")
    lines.append(f"```list\n{json.dumps(payload, ensure_ascii=False)}\n```")
    return "\n".join(lines)
