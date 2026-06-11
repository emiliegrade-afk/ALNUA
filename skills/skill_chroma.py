"""Base de connaissance vectorielle locale via Chroma."""

from __future__ import annotations

import os
from pathlib import Path

CHROMA_PATH = os.getenv("CHROMA_PATH", "./data/chroma")


def get_chroma():
    import chromadb

    return chromadb.PersistentClient(path=CHROMA_PATH)


def get_collection(name: str = "alnua_knowledge"):
    client = get_chroma()
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )


def index_document(content: str, doc_id: str, metadata: dict | None = None):
    """Indexe un document dans Chroma."""
    col = get_collection()
    col.upsert(
        documents=[content],
        ids=[doc_id],
        metadatas=[metadata or {}],
    )


def search_knowledge(query: str, n_results: int = 5) -> list[str]:
    """Cherche dans la base de connaissance."""
    col = get_collection()
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
