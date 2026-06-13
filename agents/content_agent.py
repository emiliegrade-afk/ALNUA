"""Content Agent — transforms dev logs into social media posts."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from crewai import Agent, LLM

from agents.base import LLMClient, log_agent_action, parse_json_response
from agents.tools.hub_tools import CONTENT_TOOLS
from database.supabase_client import SupabaseClient, get_supabase
from skills.skill_composio import get_composio_tools
from skills.skill_langfuse import trace_agent

VALID_PLATFORMS = frozenset({"instagram", "tiktok", "x", "youtube", "linkedin", "website_blog"})
VALID_CONTENT_TYPES = frozenset({
    "announcement", "teaser", "tutorial", "behind_scenes", "short_video",
})

PLATFORM_RULES: dict[str, str] = {
    "instagram": (
        "Instagram : texte 150-300 mots, émojis naturels, 20-25 hashtags en fin de post."
    ),
    "tiktok": (
        "TikTok : hook percutant en 1ère ligne, texte court (caption), 5-8 hashtags tendance."
    ),
    "x": "X (Twitter) : max 280 caractères, punch direct, 2-3 hashtags max.",
    "youtube": (
        "YouTube Shorts : titre accrocheur en 1ère ligne, puis description + tags/hashtags."
    ),
    "linkedin": (
        "LinkedIn : ton professionnel, 100-200 mots, pas d'émojis excessifs, 3-5 hashtags."
    ),
}

CONTENT_TYPE_HINTS: dict[str, str] = {
    "announcement": "Annonce de feature — clair, enthousiaste, orienté bénéfice utilisateur.",
    "teaser": "Teaser mystère — intrigue sans tout révéler, crée de la curiosité.",
    "behind_scenes": "Behind the scenes — authenticité solo dev, coulisses du build.",
    "tutorial": "Tutoriel court — une astuce actionnable, étapes concises.",
    "short_video": "Hype / engagement — énergie, question à la communauté, CTA.",
    "lore": "Lore / univers (Wyrdheim) — immersion, worldbuilding, ton épique.",
}


class ContentAgent:
    AGENT_NAME = "content_agent"

    SYSTEM_PROMPT = """Tu es l'agent contenu d'ALNUA. Transforme les dev logs d'Emilie en posts
réseaux sociaux authentiques, en français, adaptés à la marque ALNUA.
Réponds UNIQUEMENT en JSON valide :
{
  "posts": [
    {
      "platform": "instagram|tiktok|x|youtube|linkedin",
      "content_type": "announcement|teaser|tutorial|behind_scenes|short_video",
      "text_content": "string",
      "image_prompt": "string or null",
      "video_script": "string or null",
      "hashtags": ["string"]
    }
  ]
}
Ton : professionnel mais humain, behind-the-scenes solo dev.
Respecte STRICTEMENT les contraintes de chaque plateforme."""

    def __init__(self, db: SupabaseClient | None = None, llm: LLMClient | None = None) -> None:
        self.db = db or get_supabase()
        self.llm = llm or LLMClient()
        self._crew_llm: LLM | None = None
        self._crew_agent: Agent | None = None

    def _build_crew_llm(self) -> LLM:
        from agents.base import build_crewai_llm

        return build_crewai_llm("content", temperature=0.85)

    def _ensure_crew_agent(self) -> Agent:
        if self._crew_agent is None:
            self._crew_llm = self._build_crew_llm()
            self._crew_agent = Agent(
                role="Content ALNUA",
                goal="Générer et suivre le contenu social via l'API Hub",
                backstory=self.SYSTEM_PROMPT,
                tools=[
                    *CONTENT_TOOLS,
                    *get_composio_tools(agent_name="content_agent", user_id="alnua_content"),
                ],
                llm=self._crew_llm,
                allow_delegation=False,
                max_iter=10,
            )
        return self._crew_agent

    @trace_agent("content_agent")
    def generate_posts(
        self,
        project_id: str,
        dev_log: str,
        content_types: list[str],
        platforms: list[str],
        *,
        alnua_global: bool = False,
        save_dev_log: bool = True,
    ) -> list[dict[str, Any]]:
        """Génère des posts à partir d'un dev log libre (types + plateformes choisis)."""
        dev_log = dev_log.strip()
        if not dev_log:
            raise ValueError("Le dev log est vide.")
        if not content_types:
            raise ValueError("Sélectionne au moins un type de contenu.")
        if not platforms:
            raise ValueError("Sélectionne au moins une plateforme.")

        for p in platforms:
            if p not in VALID_PLATFORMS:
                raise ValueError(f"Plateforme invalide : {p}")
        normalized_types: list[str] = []
        for ct in content_types:
            db_type = "teaser" if ct == "lore" else ct
            if db_type not in VALID_CONTENT_TYPES:
                raise ValueError(f"Type de contenu invalide : {ct}")
            normalized_types.append(ct)

        project_rows = self.db.select("projects", filters={"id": project_id})
        if not project_rows:
            raise ValueError("Projet introuvable.")
        project = project_rows[0]
        project_label = "ALNUA (global)" if alnua_global else project["name"]

        if save_dev_log:
            self.db.insert(
                "dev_log",
                {
                    "project_id": project_id,
                    "content": dev_log,
                    "date": datetime.now(timezone.utc).date().isoformat(),
                    "used_for_content": True,
                },
            )

        type_lines = "\n".join(
            f"- {ct}: {CONTENT_TYPE_HINTS.get(ct, ct)}" for ct in normalized_types
        )
        platform_lines = "\n".join(
            f"- {p}: {PLATFORM_RULES.get(p, p)}" for p in platforms
        )

        user_prompt = f"""Projet / marque : {project_label}
Branche : {project.get("branch", "global")}

Dev log d'Emilie :
{dev_log}

Types de contenu à produire :
{type_lines}

Plateformes cibles :
{platform_lines}

Génère un post adapté pour CHAQUE combinaison pertinente (type × plateforme).
Minimum 1 post, maximum {len(normalized_types) * len(platforms)} posts.
Chaque post doit respecter les contraintes de SA plateforme."""

        from skills.skill_agent_learning import inject_learning_context, record_task_learning

        user_prompt = inject_learning_context(
            user_prompt, "content", dev_log[:200] or project_label
        )

        try:
            raw = self.llm.complete(
                self.SYSTEM_PROMPT, user_prompt, agent_id="content", temperature=0.85
            )
            result = parse_json_response(raw)
            scheduled_base = datetime.now(timezone.utc) + timedelta(days=1)
            created: list[dict[str, Any]] = []

            for i, post in enumerate(result.get("posts", [])):
                platform = post.get("platform", platforms[0])
                if platform not in VALID_PLATFORMS:
                    continue
                content_type = post.get("content_type", "announcement")
                if content_type not in VALID_CONTENT_TYPES:
                    content_type = "announcement"

                scheduled_at = scheduled_base + timedelta(hours=i * 4)
                row = self.db.insert(
                    "posts_queue",
                    {
                        "project_id": project_id,
                        "platform": platform,
                        "content_type": content_type,
                        "text_content": post["text_content"],
                        "image_prompt": post.get("image_prompt"),
                        "video_script": post.get("video_script"),
                        "hashtags": post.get("hashtags", []),
                        "scheduled_at": scheduled_at.isoformat(),
                        "status": "pending_approval",
                    },
                )
                created.append(row)

            if not created:
                raise ValueError("L'agent n'a généré aucun post valide.")

            log_agent_action(
                self.db,
                self.AGENT_NAME,
                "generate_posts",
                input_summary=f"{project_label} | {len(platforms)} plateformes",
                output_summary=f"{len(created)} posts générés",
                status="success",
                project_id=project_id,
            )
            try:
                record_task_learning(
                    agent_id="content",
                    task="generate posts",
                    outcome=str(created),
                    success=True,
                )
            except Exception:
                pass
            return created
        except Exception as exc:
            log_agent_action(
                self.db,
                self.AGENT_NAME,
                "generate_posts",
                input_summary=f"project={project_id}",
                output_summary=str(exc),
                status="error",
                project_id=project_id,
            )
            raise

    def generate_from_dev_logs(self, project_id: str) -> list[dict[str, Any]]:
        dev_logs = self.db.select(
            "dev_log",
            filters={"project_id": project_id, "used_for_content": False},
            order_by="date",
            ascending=False,
            limit=5,
        )
        if not dev_logs:
            return []

        combined = "\n\n---\n\n".join(log["content"] for log in dev_logs)
        created = self.generate_posts(
            project_id,
            combined,
            content_types=["announcement", "behind_scenes"],
            platforms=["instagram", "x", "linkedin"],
            save_dev_log=False,
        )

        for log in dev_logs:
            self.db.update("dev_log", log["id"], {"used_for_content": True})

        return created

    def approve_post(self, post_id: str) -> dict[str, Any]:
        return self.db.update("posts_queue", post_id, {"status": "approved"})

    def update_post(self, post_id: str, values: dict[str, Any]) -> dict[str, Any]:
        allowed = {"status", "text_content", "hashtags", "scheduled_at", "image_prompt", "video_script"}
        payload = {k: v for k, v in values.items() if k in allowed and v is not None}
        if "status" in payload:
            valid_status = {
                "draft", "pending_approval", "approved", "published", "failed", "rejected",
            }
            if payload["status"] not in valid_status:
                raise ValueError(f"Statut invalide : {payload['status']}")
        if not payload:
            raise ValueError("Aucun champ à mettre à jour.")
        return self.db.update("posts_queue", post_id, payload)
