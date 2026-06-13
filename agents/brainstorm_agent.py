"""Brainstorm Agent — partner d'idéation conversationnel pour Emilie."""

from __future__ import annotations

import json
import re
import unicodedata
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from agents.base import LLMClient, log_agent_action, parse_json_response
from database.supabase_client import SupabaseClient, get_supabase
from skills.skill_langfuse import trace_agent

# Racine des exports markdown
BRAINSTORM_NOTES_ROOT = Path(__file__).resolve().parent.parent / "brainstorm_notes"

# Correspondance noms de projets → dossiers sur disque
PROJECT_FOLDER_SLUGS: dict[str, str] = {
    "naïa": "naia",
    "naia": "naia",
    "wyrdheim online": "wyrdheim",
    "wyrdheim": "wyrdheim",
    "eve": "eve",
    "alnua global": "alnua_global",
}

WELCOME_MESSAGE = (
    "Bonjour Emilie. Sur quoi tu veux brainstormer aujourd'hui ? Je peux t'aider à explorer "
    "des idées de features, de nouveaux produits, des mécaniques de jeu, ou n'importe quelle "
    "direction stratégique pour ALNUA."
)

CHAT_SYSTEM_PROMPT = """Tu es le partenaire d'idéation d'Emilie pour ALNUA, sa société solo tech.
Elle te parle en dehors de la chaîne de commandement — ici, c'est un espace libre de réflexion.

Ton rôle :
- Explorer des idées de features, nouveaux produits, mécaniques de jeu, stratégie
- Poser des questions stimulantes, challenger gentiment, proposer des angles inattendus
- Rester concret et actionnable malgré la créativité
- Répondre en français, ton chaleureux et direct, comme un co-fondateur créatif

Format : texte conversationnel (pas de JSON). Structure avec des paragraphes courts.
Quand pertinent, termine par 2-3 pistes concrètes numérotées."""

SUMMARIZE_SYSTEM_PROMPT = """Tu es un assistant de synthèse pour ALNUA. Analyse cette session de brainstorm
et génère une fiche de compte-rendu en markdown, claire et scannable.
Utilise EXACTEMENT ce template (remplace les [placeholders]) :

---
session: [NNN]
projet: [Nom du projet]
date: [DD/MM/YYYY]
tags: [2-4 mots-clés]
---

# [Titre descriptif et accrocheur — 5-8 mots]
*Session #[NNN] · [Projet] · [Date longue]*

---

## 📋 Contexte
[2-3 phrases sur le sujet exploré et pourquoi]

---

## 💡 Idées explorées
[Liste numérotée de TOUTES les idées abordées, même les rejetées]
1. ...
2. ...

---

## [OK] Idees retenues
[Seulement les idées validées ou intéressantes, avec une phrase d'explication chacune]
- **[Idée]** → [Pourquoi c'est retenu]

---

## 🎯 Décisions prises
[Ce qui a été acté, orienté, ou écarté définitivement]
- ...

---

## ❓ Questions ouvertes
[Ce qui reste à explorer, trancher ou creuser]
- ...

---

## 🚀 Prochaines étapes
[Actions concrètes et actionnables]
- [ ] ...
- [ ] ...

---
*Compte-rendu généré automatiquement par ALNUA Hub*"""


class BrainstormAgent:
    AGENT_NAME = "brainstorm_agent"

    SYSTEM_PROMPT = """Tu es l'agent brainstorming d'ALNUA. Génère des idées créatives et
actionnables pour Emilie (solo dev / CEO).
Réponds UNIQUEMENT en JSON valide :
{
  "ideas": [
    {
      "title": "string",
      "description": "string",
      "category": "feature|content|marketing|monetization|tech",
      "effort": "low|medium|high",
      "impact": "low|medium|high"
    }
  ],
  "theme": "string"
}"""

    SESSION_ACTIONS = ("session_start", "brainstorm_chat")

    def __init__(self, db: SupabaseClient | None = None, llm: LLMClient | None = None) -> None:
        self.db = db or get_supabase()
        self.llm = llm or LLMClient()

    # ------------------------------------------------------------------
    # Session storage (agent_logs)
    # ------------------------------------------------------------------
    @staticmethod
    def _parse_input(raw: str) -> dict[str, Any]:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"session_id": None, "user": raw}

    def _fetch_brainstorm_logs(self, limit: int = 500) -> list[dict[str, Any]]:
        logs = self.db.select(
            "agent_logs",
            filters={"agent_name": self.AGENT_NAME},
            order_by="created_at",
            ascending=True,
            limit=limit,
        )
        return [log for log in logs if log.get("action") in self.SESSION_ACTIONS]

    def list_sessions(self, limit: int = 30) -> list[dict[str, Any]]:
        logs = self._fetch_brainstorm_logs(limit=500)
        sessions: dict[str, dict[str, Any]] = {}

        for log in logs:
            meta = self._parse_input(log.get("input_summary", "{}"))
            session_id = meta.get("session_id")
            if not session_id:
                continue

            if session_id not in sessions:
                title = meta.get("title") or meta.get("user") or "Session brainstorm"
                sessions[session_id] = {
                    "session_id": session_id,
                    "title": str(title)[:80],
                    "project_id": log.get("project_id"),
                    "created_at": log.get("created_at"),
                    "updated_at": log.get("created_at"),
                    "message_count": 0,
                }

            sessions[session_id]["updated_at"] = log.get("created_at")
            if log.get("action") == "brainstorm_chat":
                sessions[session_id]["message_count"] += 1
                if meta.get("user") and sessions[session_id]["title"] == "Session brainstorm":
                    sessions[session_id]["title"] = str(meta["user"])[:80]

        result = sorted(
            sessions.values(),
            key=lambda s: s.get("updated_at") or "",
            reverse=True,
        )
        return result[:limit]

    def get_session(self, session_id: str) -> dict[str, Any]:
        logs = self._fetch_brainstorm_logs()
        messages: list[dict[str, Any]] = []
        project_id: str | None = None
        found = False

        for log in logs:
            meta = self._parse_input(log.get("input_summary", "{}"))
            if meta.get("session_id") != session_id:
                continue

            found = True
            if log.get("project_id"):
                project_id = log["project_id"]

            if log.get("action") == "session_start":
                continue

            user_text = meta.get("user", "")
            assistant_text = log.get("output_summary", "")
            if user_text:
                messages.append(
                    {
                        "id": f"{log['id']}-user",
                        "role": "user",
                        "content": user_text,
                        "created_at": log.get("created_at"),
                    }
                )
            if assistant_text:
                messages.append(
                    {
                        "id": f"{log['id']}-assistant",
                        "role": "assistant",
                        "content": assistant_text,
                        "created_at": log.get("created_at"),
                    }
                )

        if not found:
            raise ValueError(f"Session {session_id} not found")

        if not messages:
            messages.append(
                {
                    "id": "welcome",
                    "role": "assistant",
                    "content": WELCOME_MESSAGE,
                    "created_at": datetime.utcnow().isoformat(),
                }
            )

        return {
            "session_id": session_id,
            "project_id": project_id,
            "messages": messages,
        }

    def create_session(self, project_id: str | None = None, title: str = "Nouvelle session") -> str:
        session_id = str(uuid.uuid4())
        self.db.insert(
            "agent_logs",
            {
                "agent_name": self.AGENT_NAME,
                "action": "session_start",
                "project_id": project_id,
                "input_summary": json.dumps(
                    {"session_id": session_id, "title": title},
                    ensure_ascii=False,
                )[:2000],
                "output_summary": WELCOME_MESSAGE[:2000],
                "status": "success",
            },
        )
        return session_id

    # ------------------------------------------------------------------
    # Mémoire cross-sessions & comptes-rendus
    # ------------------------------------------------------------------
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

        summary_md = self.llm.complete(
            SUMMARIZE_SYSTEM_PROMPT,
            user_prompt,
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

    def _build_project_context(self, project_id: str | None) -> str:
        if not project_id:
            return (
                "\n\nContexte : ALNUA Global — vision multi-branches "
                "(App Naïa, Gaming Wyrdheim, Robotique Eve)."
            )

        project = self.db.select("projects", filters={"id": project_id})
        if not project:
            return "\n\nContexte : nouveau projet en exploration."

        p = project[0]
        roadmap = self.db.select("roadmap", filters={"project_id": project_id}, limit=5)
        feedback = self.db.select(
            "feedback",
            filters={"project_id": project_id},
            order_by="created_at",
            ascending=False,
            limit=5,
        )
        return f"""

Contexte projet actif :
- Nom : {p['name']}
- Branche : {p['branch']}
- Statut : {p['status']}
- Description : {p['description']}
- Roadmap récente : {json.dumps(roadmap, ensure_ascii=False)[:800]}
- Feedback récent : {json.dumps(feedback, ensure_ascii=False)[:800]}
"""

    def _history_to_messages(self, session_id: str) -> list[dict[str, str]]:
        session = self.get_session(session_id)
        history: list[dict[str, str]] = []
        for msg in session["messages"]:
            if msg["id"] == "welcome":
                continue
            history.append({"role": msg["role"], "content": msg["content"]})
        return history

    @trace_agent("brainstorm_agent")
    def chat(
        self,
        message: str,
        project_id: str | None = None,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        message = message.strip()
        if not message:
            raise ValueError("Message vide")

        is_new = not session_id
        if is_new:
            session_id = self.create_session(
                project_id,
                title=message[:80],
            )

        system = CHAT_SYSTEM_PROMPT + self._build_project_context(project_id)

        from skills.skill_agent_learning import get_learning_context, record_task_learning

        mem0_block = get_learning_context("brainstorm", message)
        if mem0_block:
            system += mem0_block

        # Mémoire cross-sessions Supabase au premier message
        if is_new:
            memory = self.get_project_memory(project_id)
            if memory:
                system += f"\n\n{memory}"

        history = self._history_to_messages(session_id)
        history.append({"role": "user", "content": message})

        try:
            response = self.llm.chat(
                system=system,
                messages=history,
                agent_id="brainstorm",
                temperature=0.85,
                max_tokens=4096,
            )
            self.db.insert(
                "agent_logs",
                {
                    "agent_name": self.AGENT_NAME,
                    "action": "brainstorm_chat",
                    "project_id": project_id,
                    "input_summary": json.dumps(
                        {"session_id": session_id, "user": message},
                        ensure_ascii=False,
                    )[:2000],
                    "output_summary": response[:2000],
                    "status": "success",
                },
            )
            try:
                record_task_learning(
                    agent_id="brainstorm",
                    task=f"brainstorm {session_id}",
                    outcome=str({"response": response[:500], "session_id": session_id}),
                    success=True,
                )
            except Exception:
                pass
            return {"response": response, "session_id": session_id}
        except Exception as exc:
            log_agent_action(
                self.db,
                self.AGENT_NAME,
                "brainstorm_chat",
                input_summary=message[:200],
                output_summary=str(exc),
                status="error",
                project_id=project_id,
            )
            raise

    # ------------------------------------------------------------------
    # Legacy one-shot brainstorm (JSON ideas)
    # ------------------------------------------------------------------
    def brainstorm(
        self,
        project_id: str,
        topic: str,
        context_notes: str = "",
    ) -> dict[str, Any]:
        project = self.db.select("projects", filters={"id": project_id})
        if not project:
            raise ValueError(f"Project {project_id} not found")

        roadmap = self.db.select("roadmap", filters={"project_id": project_id}, limit=10)
        recent_feedback = self.db.select(
            "feedback",
            filters={"project_id": project_id},
            order_by="created_at",
            ascending=False,
            limit=10,
        )

        user_prompt = f"""Projet : {project[0]['name']} — {project[0]['description']}
Branche : {project[0]['branch']}
Sujet : {topic}
Notes : {context_notes}
Roadmap actuelle : {roadmap}
Feedback récent : {recent_feedback}

Génère 5 à 8 idées originales."""

        try:
            raw = self.llm.complete(
                self.SYSTEM_PROMPT, user_prompt, agent_id="brainstorm", temperature=0.9
            )
            result = parse_json_response(raw)
            log_agent_action(
                self.db,
                self.AGENT_NAME,
                "brainstorm",
                input_summary=f"topic={topic}",
                output_summary=f"{len(result.get('ideas', []))} idées",
                status="success",
                project_id=project_id,
            )
            return result
        except Exception as exc:
            log_agent_action(
                self.db,
                self.AGENT_NAME,
                "brainstorm",
                input_summary=f"topic={topic}",
                output_summary=str(exc),
                status="error",
                project_id=project_id,
            )
            raise

    def add_top_idea_to_roadmap(
        self,
        project_id: str,
        idea: dict[str, Any],
        phase: str = "backlog",
    ) -> dict[str, Any]:
        impact_map = {"low": "low", "medium": "medium", "high": "high"}
        priority = impact_map.get(idea.get("impact", "medium"), "medium")
        return self.db.insert(
            "roadmap",
            {
                "project_id": project_id,
                "title": idea["title"],
                "description": idea.get("description", ""),
                "phase": phase,
                "priority": priority,
                "status": "idea",
            },
        )
