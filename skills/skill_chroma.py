"""Base de connaissance vectorielle locale via Chroma."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

CHROMA_PATH = os.getenv("CHROMA_PATH", "./data/chroma")
LIBRARY_COLLECTION = "alnua_library"
KNOWLEDGE_COLLECTION = "alnua_knowledge"


def get_chroma():
    import chromadb

    return chromadb.PersistentClient(path=CHROMA_PATH)


def get_collection(name: str = KNOWLEDGE_COLLECTION):
    client = get_chroma()
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )


def index_document(
    content: str,
    doc_id: str,
    metadata: dict | None = None,
    *,
    collection: str = KNOWLEDGE_COLLECTION,
):
    """Indexe un document dans Chroma."""
    col = get_collection(collection)
    col.upsert(
        documents=[content],
        ids=[doc_id],
        metadatas=[metadata or {}],
    )


def search_knowledge(query: str, n_results: int = 5) -> list[str]:
    """Cherche dans la base de connaissance Hub (docs repo)."""
    col = get_collection(KNOWLEDGE_COLLECTION)
    results = col.query(query_texts=[query], n_results=n_results)
    return results["documents"][0] if results["documents"] else []


def search_library(query: str, n_results: int = 5) -> list[str]:
    """Cherche dans la collection bibliothèque (notes vault library/)."""
    col = get_collection(LIBRARY_COLLECTION)
    results = col.query(query_texts=[query], n_results=n_results)
    return results["documents"][0] if results["documents"] else []


def index_project_docs():
    """Indexe tous les fichiers .md du repo."""
    root = Path(".")
    for md_file in root.rglob("*.md"):
        if "node_modules" in str(md_file) or ".git" in str(md_file):
            continue
        content = md_file.read_text(encoding="utf-8", errors="ignore")
        if len(content) > 100:
            index_document(
                content=content[:5000],
                doc_id=str(md_file),
                metadata={"file": str(md_file), "type": "markdown"},
            )
    print(f"Docs indexés dans Chroma : {Path(CHROMA_PATH)}")


def index_library_vault(
    vault: Path | None = None,
    *,
    limit: int | None = None,
    batch_size: int = 64,
) -> dict[str, Any]:
    """
    Index markdown notes under ``library/`` into Chroma collection ``alnua_library``.

    Uses batched upserts (much faster than one-doc-at-a-time).
    """
    try:
        from services.obsidian_vault import get_vault_path, iter_markdown_files, read_note
    except Exception as exc:
        return {"ok": False, "error": str(exc), "indexed": 0}

    root = vault or get_vault_path()
    col = get_collection(LIBRARY_COLLECTION)

    docs: list[str] = []
    ids: list[str] = []
    metas: list[dict[str, Any]] = []
    indexed = 0
    errors = 0

    def _flush() -> None:
        nonlocal docs, ids, metas, indexed
        if not ids:
            return
        col.upsert(documents=docs, ids=ids, metadatas=metas)
        indexed += len(ids)
        docs, ids, metas = [], [], []

    for path in iter_markdown_files(root, subdir="library"):
        if limit is not None and indexed + len(ids) >= limit:
            break
        if path.name in {"README.md", "TOPICS.md", ".gitkeep"}:
            continue
        if "_index" in path.parts and path.name != "TOPICS.md":
            # skip index stubs except we already skip TOPICS
            if path.parent.name == "_index":
                continue
        try:
            note = read_note(path, vault=root)
            body = f"{note.title}\n\n{note.content}".strip()
            if len(body) < 40:
                continue
            docs.append(body[:8000])
            ids.append(f"library:{note.rel_path}")
            metas.append(
                {
                    "file": note.rel_path,
                    "type": "library",
                    "bureau": str(note.metadata.get("bureau") or ""),
                    "timing": str(note.metadata.get("timing") or ""),
                    "entry_id": str(note.metadata.get("id") or ""),
                }
            )
            if len(ids) >= batch_size:
                _flush()
        except Exception as exc:
            errors += 1
            logger.debug("index_library_vault skip %s: %s", path, exc)

    try:
        _flush()
    except Exception as exc:
        return {
            "ok": False,
            "error": str(exc),
            "indexed": indexed,
            "errors": errors + 1,
            "collection": LIBRARY_COLLECTION,
            "vault": str(root),
        }

    return {
        "ok": True,
        "collection": LIBRARY_COLLECTION,
        "vault": str(root),
        "indexed": indexed,
        "errors": errors,
        "chroma_path": str(Path(CHROMA_PATH).resolve()),
    }
