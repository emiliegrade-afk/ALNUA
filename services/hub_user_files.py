"""Hub user file library — local uploads reusable across Live and Secretary (DEC-040).

Distinct from ``/library`` bureau archives (DEC-040): personal attachments under
``data/hub_uploads/`` with index ``data/hub_files.json``.
"""

from __future__ import annotations

import json
import re
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_FILES_PER_TASK = 5
MAX_EXTRACT_CHARS = 8000
MAX_STORED_FILES = 500

ALLOWED_EXTENSIONS = frozenset({".txt", ".md", ".json", ".csv", ".log", ".yaml", ".yml"})
ALLOWED_SOURCES = frozenset({"live", "secretary", "upload"})

_SAFE_NAME = re.compile(r"[^a-zA-Z0-9._-]+")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _uploads_dir() -> Path:
    from config.paths import get_hub_repo_path

    return get_hub_repo_path() / "data" / "hub_uploads"


def _index_path() -> Path:
    from config.paths import get_hub_repo_path

    return get_hub_repo_path() / "data" / "hub_files.json"


def _sanitize_display_name(name: str) -> str:
    base = Path(name or "file.txt").name
    cleaned = _SAFE_NAME.sub("_", base).strip("._") or "file.txt"
    return cleaned[:120]


def _extension_for(name: str, content_type: str) -> str:
    ext = Path(name).suffix.lower()
    if ext in ALLOWED_EXTENSIONS:
        return ext
    if content_type.startswith("text/"):
        return ".txt"
    return ""


@dataclass
class HubUserFile:
    id: str
    name: str
    size_bytes: int
    content_type: str
    source: str
    created_at: str = field(default_factory=_now)
    storage_name: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class HubUserFileStore:
    def __init__(self, index_path: Path | None = None, uploads_dir: Path | None = None) -> None:
        self._index_path = index_path
        self._uploads_dir = uploads_dir
        self._lock = threading.RLock()
        self._files: dict[str, HubUserFile] = {}
        self._loaded = False

    @property
    def index_path(self) -> Path:
        return self._index_path or _index_path()

    @property
    def uploads_dir(self) -> Path:
        return self._uploads_dir or _uploads_dir()

    def _load(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        try:
            raw = json.loads(self.index_path.read_text(encoding="utf-8"))
            for item in raw.get("files", []):
                record = HubUserFile(**item)
                self._files[record.id] = record
        except FileNotFoundError:
            return
        except (OSError, ValueError, TypeError):
            return

    def _save(self) -> None:
        self._trim()
        payload = {"files": [f.to_dict() for f in self._files.values()]}
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.index_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(self.index_path)

    def _trim(self) -> None:
        overflow = len(self._files) - MAX_STORED_FILES
        if overflow <= 0:
            return
        oldest = sorted(self._files.values(), key=lambda f: f.created_at)
        for record in oldest[:overflow]:
            self._delete_disk(record)
            del self._files[record.id]

    def _disk_path(self, record: HubUserFile) -> Path:
        return self.uploads_dir / record.storage_name

    def _delete_disk(self, record: HubUserFile) -> None:
        try:
            self._disk_path(record).unlink(missing_ok=True)
        except OSError:
            pass

    def save_bytes(
        self,
        data: bytes,
        filename: str,
        content_type: str,
        source: str = "upload",
    ) -> HubUserFile:
        if len(data) > MAX_FILE_BYTES:
            raise ValueError(f"Fichier trop volumineux (max {MAX_FILE_BYTES // (1024 * 1024)} Mo).")
        if source not in ALLOWED_SOURCES:
            raise ValueError("Source invalide.")
        ext = _extension_for(filename, content_type or "")
        if not ext:
            raise ValueError("Type de fichier non autorisé (texte uniquement pour l'instant).")

        safe_name = _sanitize_display_name(filename)
        if not safe_name.lower().endswith(ext):
            safe_name = f"{safe_name}{ext}"

        file_id = uuid.uuid4().hex[:12]
        storage_name = f"{file_id}_{safe_name}"

        with self._lock:
            self._load()
            self.uploads_dir.mkdir(parents=True, exist_ok=True)
            (self.uploads_dir / storage_name).write_bytes(data)

            record = HubUserFile(
                id=file_id,
                name=safe_name,
                size_bytes=len(data),
                content_type=content_type or "text/plain",
                source=source,
                storage_name=storage_name,
            )
            self._files[file_id] = record
            self._save()
            return record

    def list_files(
        self,
        query: str = "",
        source: str | None = None,
        limit: int = 50,
    ) -> list[HubUserFile]:
        with self._lock:
            self._load()
            items = sorted(self._files.values(), key=lambda f: f.created_at, reverse=True)
            if source:
                items = [f for f in items if f.source == source]
            q = query.strip().lower()
            if q:
                items = [f for f in items if q in f.name.lower()]
            return items[: max(1, min(limit, 200))]

    def get(self, file_id: str) -> HubUserFile | None:
        with self._lock:
            self._load()
            return self._files.get(file_id)

    def read_bytes(self, file_id: str) -> bytes:
        record = self.get(file_id)
        if record is None:
            raise ValueError("Fichier introuvable.")
        path = self._disk_path(record)
        if not path.is_file():
            raise ValueError("Fichier manquant sur le disque.")
        return path.read_bytes()

    def delete(self, file_id: str) -> bool:
        with self._lock:
            self._load()
            record = self._files.pop(file_id, None)
            if record is None:
                return False
            self._delete_disk(record)
            self._save()
            return True


_store = HubUserFileStore()


def get_store() -> HubUserFileStore:
    return _store


def build_attachment_context(file_ids: list[str]) -> str:
    """Load and sanitize file excerpts for LLM prompts."""
    from services.input_sanitizer import sanitize_user_input

    if not file_ids:
        return ""
    if len(file_ids) > MAX_FILES_PER_TASK:
        raise ValueError(f"Maximum {MAX_FILES_PER_TASK} fichiers par tâche.")

    blocks: list[str] = []
    store = get_store()
    for fid in file_ids:
        record = store.get(fid.strip())
        if record is None:
            raise ValueError(f"Fichier introuvable : {fid}")
        raw = store.read_bytes(record.id)
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            raise ValueError(f"Fichier non texte : {record.name}")
        excerpt = text[:MAX_EXTRACT_CHARS]
        if len(text) > MAX_EXTRACT_CHARS:
            excerpt += "\n[… tronqué …]"
        safe = sanitize_user_input(excerpt, max_length=MAX_EXTRACT_CHARS + 64, redact_pii_enabled=False)
        blocks.append(f"[Pièce jointe : {record.name}]\n{safe}")

    return "\n\n".join(blocks)


def merge_instruction_with_files(instruction: str, file_ids: list[str]) -> str:
    """Combine user instruction with attachment bodies (execution-time expansion)."""
    body = build_attachment_context(file_ids)
    if not body:
        return instruction
    return f"{instruction.strip()}\n\n{body}".strip()


def prepare_user_prompt_with_files(
    message: str,
    file_ids: list[str] | None,
    *,
    max_message_chars: int = 4000,
) -> str:
    """Validate ids, sanitize the user message, merge attachment excerpts (assistant + Live)."""
    from services.input_sanitizer import sanitize_user_input

    ids = [f.strip() for f in (file_ids or []) if f and f.strip()]
    if len(ids) > MAX_FILES_PER_TASK:
        raise ValueError(f"Maximum {MAX_FILES_PER_TASK} fichiers par tâche.")
    safe = sanitize_user_input(message, max_length=max_message_chars, redact_pii_enabled=False)
    if not safe and not ids:
        raise ValueError("Message vide après nettoyage")
    if ids:
        build_attachment_context(ids)
    return merge_instruction_with_files(safe or "Voir les pièces jointes.", ids)
