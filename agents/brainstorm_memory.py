"""Brainstorm agent — cross-session memory, summaries, markdown export."""
from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any

from agents.base import log_agent_action
from agents.brainstorm_constants import (
    BRAINSTORM_NOTES_ROOT,
    PROJECT_FOLDER_SLUGS,
    SUMMARIZE_SYSTEM_PROMPT,
)


class BrainstormMemoryMixin:
    """Requires ``self.db``, ``self.AGENT_NAME``, ``get_session`` from session mixin."""

    @staticmethod
    def _slugify(text: str) -> str:
        """Convertit un texte en slug kebab-case (ASCII)."""
        normalized = unicodedata.normalize("NFKD", text)
        ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
        slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
        return slug or "session"

    @classmethod
    def project_folder_slug(cls, project_name: str, project_id: str | None = None) -> str:
        """Retourne le nom de dossier pour les notes markdown d'un projet."""
        key = project_name.strip().lower()
        if key in PROJECT_FOLDER_SLUGS:
            return PROJECT_FOLDER_SLUGS[key]
        slug = cls._slugify(project_name)
        if project_id and slug:
            return slug
        return slug or "projet"

    @classmethod
    def ensure_project_notes_dir(cls, project_name: str, project_id: str | None = None) -> Path:
        """Crée le sous-dossier brainstorm_notes/[slug] s'il n'existe pas."""
        folder = BRAINSTORM_NOTES_ROOT / cls.project_folder_slug(project_name, project_id)
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def _fetch_summaries(
        self,
        project_id: str | None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Récupère les derniers comptes-rendus d'un projet (NULL = ALNUA Global)."""
        if project_id:
            return self.db.select(
                "brainstorm_summaries",
                filters={"project_id": project_id},
                order_by="created_at",
                ascending=False,
                limit=limit,
            )
        return self.db.select(
            "brainstorm_summaries",
            is_null=["project_id"],
            order_by="created_at",
            ascending=False,
            limit=limit,
        )

    def get_project_memory(self, project_id: str | None) -> str:
        """Construit le bloc de contexte des sessions précédentes pour un projet."""
        summaries = self._fetch_summaries(project_id, limit=5)
        if not summaries:
            return ""

        if project_id:
            rows = self.db.select("projects", filters={"id": project_id})
            project_label = rows[0]["name"] if rows else "ce projet"
        else:
            project_label = "ALNUA Global"

        lines = [f"Mémoire des sessions précédentes sur {project_label} :"]
        for item in summaries:
            created = item.get("created_at", "")[:10]
            num = item.get("session_number", 0)
            title = item.get("title", "Session")
            key_ideas = item.get("key_ideas") or []
            decisions = item.get("decisions") or []
            open_q = item.get("open_questions") or []

            lines.append(f"\nSession #{num:03d} ({created}) — {title}")
            if key_ideas:
                lines.append(f"  Idées retenues : {', '.join(key_ideas[:8])}")
            if decisions:
                lines.append(f"  Décisions : {', '.join(decisions[:6])}")
            if open_q:
                lines.append(f"  Questions ouvertes : {', '.join(open_q[:6])}")

        lines.append(
            "\nUtilise cette mémoire pour éviter de repartir de zéro : "
            "fais référence aux décisions passées et creuse les questions encore ouvertes."
        )
        return "\n".join(lines)

    def _next_session_number(self, project_id: str | None) -> int:
        """Numéro séquentiel du prochain compte-rendu pour ce projet."""
        existing = self._fetch_summaries(project_id, limit=100)
        if not existing:
            return 1
        return max(s.get("session_number", 0) for s in existing) + 1

    @staticmethod
    def _extract_markdown_title(markdown: str) -> str:
        """Extrait le titre principal (# ...) du markdown généré."""
        for line in markdown.splitlines():
            stripped = line.strip()
            if stripped.startswith("# ") and not stripped.startswith("## "):
                return stripped[2:].strip()
        return "Compte-rendu brainstorm"

    @staticmethod
    def _parse_section_items(markdown: str, heading: str) -> list[str]:
        """Extrait les puces d'une section ## heading."""
        pattern = rf"##\s*{re.escape(heading)}\s*\n(.*?)(?=\n---|\n## |\Z)"
        match = re.search(pattern, markdown, re.DOTALL | re.IGNORECASE)
        if not match:
            return []

        block = match.group(1)
        items: list[str] = []
        for line in block.splitlines():
            line = line.strip()
            if not line:
                continue
            cleaned = re.sub(r"^[-*]\s*", "", line)
            cleaned = re.sub(r"^\d+\.\s*", "", cleaned)
            cleaned = re.sub(r"^\[[ x]\]\s*", "", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"\*\*(.+?)\*\*", r"\1", cleaned)
            cleaned = re.sub(r"\s*→.*$", "", cleaned).strip()
            if cleaned and len(cleaned) > 2:
                items.append(cleaned[:500])
        return items[:30]

    def summarize_session(self, session_id: str) -> dict[str, Any]:
        """Génère une fiche markdown, l'exporte sur disque et la sauvegarde en base."""
        session = self.get_session(session_id)
        project_id = session.get("project_id")
        messages = session.get("messages", [])

        transcript_lines: list[str] = []
        for msg in messages:
            if msg.get("id") == "welcome":
                continue
            role = "Emilie" if msg["role"] == "user" else "Agent"
            transcript_lines.append(f"{role}: {msg['content']}")

        if not transcript_lines:
            raise ValueError("Session vide — impossible de générer un compte-rendu")

        project_name = "ALNUA Global"
        if project_id:
            rows = self.db.select("projects", filters={"id": project_id})
            if rows:
                project_name = rows[0]["name"]

        session_number = self._next_session_number(project_id)
        session_num_str = f"{session_number:03d}"

        user_prompt = f"""Projet : {project_name}
Numéro de session à utiliser dans le template : {session_num_str}
Date du jour : {datetime.now().strftime("%d/%m/%Y")}

TRANSCRIPT DE LA SESSION :
{chr(10).join(transcript_lines)}

Génère la fiche complète en markdown en suivant EXACTEMENT le template fourni."""

        summary_md = self._complete(
            user_prompt,
            system_prompt=SUMMARIZE_SYSTEM_PROMPT,
            agent_id="brainstorm",
            temperature=0.35,
            max_tokens=4096,
        )

        title = self._extract_markdown_title(summary_md)
        key_ideas = self._parse_section_items(summary_md, "[OK] Idees retenues")
        if not key_ideas:
            key_ideas = self._parse_section_items(summary_md, "💡 Idées explorées")[:10]

        decisions = self._parse_section_items(summary_md, "🎯 Décisions prises")
        open_questions = self._parse_section_items(summary_md, "❓ Questions ouvertes")
        next_steps = self._parse_section_items(summary_md, "🚀 Prochaines étapes")

        notes_dir = self.ensure_project_notes_dir(project_name, project_id)
        date_file = datetime.now().strftime("%Y-%m-%d")
        filename = f"{session_num_str}_{self._slugify(title)[:60]}_{date_file}.md"
        file_path = notes_dir / filename
        file_path.write_text(summary_md, encoding="utf-8")
        absolute_path = str(file_path.resolve())

        row_data = {
            "project_id": project_id,
            "session_id": session_id,
            "session_number": session_number,
            "title": title,
            "summary": summary_md,
            "key_ideas": key_ideas,
            "decisions": decisions,
            "next_steps": next_steps,
            "open_questions": open_questions,
            "file_path": absolute_path,
        }

        existing = self.db.select(
            "brainstorm_summaries",
            filters={"session_id": session_id},
            limit=1,
        )
        if existing:
            row = self.db.update("brainstorm_summaries", existing[0]["id"], row_data)
        else:
            row = self.db.insert("brainstorm_summaries", row_data)

        log_agent_action(
            self.db,
            self.AGENT_NAME,
            "session_summarize",
            input_summary=f"session={session_id}",
            output_summary=f"#{session_num_str} {title}",
            status="success",
            project_id=project_id,
        )

        return {
            "summary_md": summary_md,
            "file_path": absolute_path,
            "session_number": session_number,
            "title": title,
            "project_slug": self.project_folder_slug(project_name, project_id),
            "id": row["id"],
        }

    def get_summary_for_session(self, session_id: str) -> dict[str, Any] | None:
        """Retourne le compte-rendu existant d'une session, ou None."""
        rows = self.db.select(
            "brainstorm_summaries",
            filters={"session_id": session_id},
            limit=1,
        )
        return rows[0] if rows else None

    def attach_summaries_to_sessions(
        self,
        sessions: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Enrichit la liste de sessions avec les métadonnées de compte-rendu."""
        if not sessions:
            return sessions

        all_summaries = self.db.select(
            "brainstorm_summaries",
            order_by="created_at",
            ascending=False,
            limit=200,
        )
        by_session = {s["session_id"]: s for s in all_summaries}

        for session in sessions:
            sid = session.get("session_id")
            summary = by_session.get(sid)
            if summary:
                session["has_summary"] = True
                session["summary_title"] = summary.get("title")
                session["summary_number"] = summary.get("session_number")
                session["summary_file_path"] = summary.get("file_path")
            else:
                session["has_summary"] = False

        return sessions
