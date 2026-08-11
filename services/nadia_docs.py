"""Nadia document workspace — traitement de texte (markdown + export)."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT / "data" / "nadia_docs"
INDEX_FILE = DOCS_DIR / "index.json"


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slug(title: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9\-]+", "-", (title or "document").strip().lower())
    s = re.sub(r"-+", "-", s).strip("-") or "document"
    return s[:80]


def _load_index() -> list[dict[str, Any]]:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    if not INDEX_FILE.is_file():
        return []
    try:
        raw = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
        return raw if isinstance(raw, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def _save_index(entries: list[dict[str, Any]]) -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")


def list_documents() -> list[dict[str, Any]]:
    return _load_index()


def create_document(title: str, content: str = "", *, doc_type: str = "note") -> dict[str, Any]:
    """Create a Hub document.

    Notes stay markdown for editing; **contracts** are saved as `.docx`
    (Word) — never as the primary contract artifact in `.md`.
    """
    title = (title or "Sans titre").strip()[:200]
    slug = _slug(title)
    is_contract = doc_type in {"contrat", "contract", "nda", "partenariat", "influenceur", "pub", "prestation", "affiliation"}

    if is_contract:
        return _create_contract_docx(title, content, slug=slug, doc_type=doc_type)

    path = DOCS_DIR / f"{slug}.md"
    n = 1
    while path.exists():
        path = DOCS_DIR / f"{slug}-{n}.md"
        n += 1
    body = content.strip() or f"# {title}\n\n"
    if not body.startswith("#"):
        body = f"# {title}\n\n{body}"
    path.write_text(body, encoding="utf-8")
    entry = {
        "id": path.stem,
        "title": title,
        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "doc_type": doc_type,
        "format": "md",
        "updated_at": _utc(),
        "created_at": _utc(),
    }
    entries = _load_index()
    entries = [e for e in entries if e.get("id") != entry["id"]]
    entries.insert(0, entry)
    _save_index(entries[:200])
    return entry


def _create_contract_docx(
    title: str,
    content: str,
    *,
    slug: str,
    doc_type: str,
) -> dict[str, Any]:
    """Write contract body to Word (.docx) under data/nadia_docs/contracts/."""
    contracts_dir = DOCS_DIR / "contracts"
    contracts_dir.mkdir(parents=True, exist_ok=True)
    path = contracts_dir / f"{slug}.docx"
    n = 1
    while path.exists():
        path = contracts_dir / f"{slug}-{n}.docx"
        n += 1

    try:
        from docx import Document  # type: ignore
    except ImportError as exc:
        raise RuntimeError("python-docx requis pour les contrats Word") from exc

    document = Document()
    document.add_heading(title, level=1)
    for line in (content or "").splitlines():
        if line.startswith("## "):
            document.add_heading(line[3:].strip(), level=2)
        elif line.startswith("# "):
            document.add_heading(line[2:].strip(), level=1)
        elif line.strip():
            document.add_paragraph(line)
        else:
            document.add_paragraph("")
    document.save(str(path))

    # Keep a short .txt sidecar for Hub preview / LLM re-read
    preview = contracts_dir / f"{path.stem}.txt"
    preview.write_text(f"# {title}\n\n{content}", encoding="utf-8")

    entry = {
        "id": path.stem,
        "title": title,
        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "preview_path": str(preview.relative_to(ROOT)).replace("\\", "/"),
        "doc_type": doc_type if doc_type != "contrat" else "contrat",
        "format": "docx",
        "updated_at": _utc(),
        "created_at": _utc(),
    }
    entries = _load_index()
    entries = [e for e in entries if e.get("id") != entry["id"]]
    entries.insert(0, entry)
    _save_index(entries[:200])
    return entry


def read_document(doc_id: str) -> dict[str, Any] | None:
    meta = next((e for e in _load_index() if e.get("id") == doc_id), None)
    if meta and meta.get("format") == "docx":
        preview = ROOT / str(meta.get("preview_path") or "")
        text = ""
        if preview.is_file():
            text = preview.read_text(encoding="utf-8")
        return {**meta, "content": text}

    path = DOCS_DIR / f"{doc_id}.md"
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    meta = meta or {
        "id": doc_id,
        "title": doc_id,
        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "format": "md",
    }
    return {**meta, "content": text}


def update_document(doc_id: str, content: str, *, title: str | None = None) -> dict[str, Any] | None:
    path = DOCS_DIR / f"{doc_id}.md"
    if not path.is_file():
        return None
    path.write_text(content, encoding="utf-8")
    entries = _load_index()
    for e in entries:
        if e.get("id") == doc_id:
            e["updated_at"] = _utc()
            if title:
                e["title"] = title[:200]
            break
    else:
        entries.insert(
            0,
            {
                "id": doc_id,
                "title": title or doc_id,
                "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "doc_type": "note",
                "updated_at": _utc(),
                "created_at": _utc(),
            },
        )
    _save_index(entries)
    return read_document(doc_id)


def export_txt(doc_id: str) -> Path | None:
    doc = read_document(doc_id)
    if not doc:
        return None
    out = DOCS_DIR / f"{doc_id}.txt"
    out.write_text(doc.get("content") or "", encoding="utf-8")
    return out


def export_docx(doc_id: str) -> Path | None:
    """Export Word if python-docx available; else None."""
    doc = read_document(doc_id)
    if not doc:
        return None
    try:
        from docx import Document  # type: ignore
    except ImportError:
        return None
    document = Document()
    for line in (doc.get("content") or "").splitlines():
        if line.startswith("# "):
            document.add_heading(line[2:].strip(), level=1)
        elif line.startswith("## "):
            document.add_heading(line[2:].strip(), level=2)
        elif line.strip():
            document.add_paragraph(line)
        else:
            document.add_paragraph("")
    out = DOCS_DIR / f"{doc_id}.docx"
    document.save(str(out))
    return out
