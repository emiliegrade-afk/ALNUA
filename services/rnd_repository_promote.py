"""Idea → dossier promote mixin."""
from __future__ import annotations

import logging
from typing import Any

from services.rnd_repository_helpers import _slugify
from services.rnd_schemas import SECTION_DEFINITIONS, RndDossierOut, RndIdeaOut

logger = logging.getLogger(__name__)


class RndPromoteMixin:
    def promote_idea_to_dossier(
        self,
        idea_id: str,
        *,
        vision_snapshot: str = "",
        competitive_context: str = "",
        actor: str = "emilie",
        seed_content_override: dict[str, str] | None = None,
        tagline: str | None = None,
    ) -> tuple[RndDossierOut, RndIdeaOut]:
        """
        Create dossier + section skeleton from an idea.
        Raises ValueError if idea not found or dossier already exists.
        """
        if not self._use_db:
            raise RuntimeError(
                "Supabase rnd_* tables unavailable. Run migration 20260613120000_rnd_dossiers.sql"
            )

        # Ensure idea is in DB
        db_row = self.get_idea_db_row(idea_id)
        if not db_row:
            json_ideas = self._load_json_ideas()
            match = next((i for i in json_ideas if i.get("id") == idea_id), None)
            if not match:
                raise ValueError(f"Idée introuvable : {idea_id}")
            db_row = self.sync_idea_to_db(match)
            if not db_row:
                raise RuntimeError("Impossible de synchroniser l'idée vers Supabase")

        if db_row.get("dossier_id"):
            existing = self.get_dossier(str(db_row["dossier_id"]))
            if existing:
                raise ValueError(f"Dossier déjà existant pour cette idée : {existing.slug}")
            # Orphan link: idea points to a deleted dossier — clear and continue.
            logger.warning(
                "rnd_repository: clearing orphan dossier_id on idea %s",
                idea_id,
            )
            self.db.update(
                "rnd_ideas",
                db_row["id"],
                {"dossier_id": None, "lifecycle_status": "raw"},
            )
            legacy_id = db_row.get("legacy_id")
            if legacy_id:
                json_ideas = self._load_json_ideas()
                for j in json_ideas:
                    if j.get("id") == legacy_id:
                        j["dossier_id"] = None
                        j["lifecycle_status"] = "raw"
                self._save_json_ideas(json_ideas)
            db_row["dossier_id"] = None
            db_row["lifecycle_status"] = "raw"

        title = db_row.get("title", "Sans titre")
        domain = db_row.get("domain") or "autre"
        base_slug = _slugify(title)[:60]

        # Unique slug
        slug = base_slug
        suffix = 1
        while self.db.select("rnd_dossiers", filters={"slug": slug}, limit=1):
            slug = f"{base_slug}-{suffix}"
            suffix += 1

        section_keys = self.section_keys_for_domain(domain)
        seed_content = self._seed_section_content(db_row)
        if seed_content_override:
            for key, text in seed_content_override.items():
                if text and str(text).strip():
                    seed_content[key] = str(text).strip()

        section_rows: list[dict[str, Any]] = []
        for key in section_keys:
            defn = SECTION_DEFINITIONS[key]
            section_rows.append({
                "section_key": key,
                "title": defn["title"],
                "sort_order": defn["sort_order"],
                "content_md": seed_content.get(key, "_À compléter lors du comité R&D._"),
                "status": "draft",
            })

        local_path = self._write_local_dossier_skeleton(slug, title, section_rows)

        dossier_row = self.db.insert(
            "rnd_dossiers",
            {
                "idea_id": db_row["id"],
                "slug": slug,
                "title": title,
                "tagline": (
                    (tagline or "").strip()[:200]
                    or (db_row.get("description") or "")[:200]
                    or None
                ),
                "domain": domain,
                "branch": self.branch_for_domain(domain),
                "status": "draft",
                "vision_snapshot": vision_snapshot[:4000] if vision_snapshot else None,
                "competitive_context": competitive_context[:4000] if competitive_context else None,
                "local_path": local_path,
            },
        )

        for sec in section_rows:
            self.db.insert(
                "rnd_dossier_sections",
                {**sec, "dossier_id": dossier_row["id"]},
            )

        self.db.update(
            "rnd_ideas",
            db_row["id"],
            {
                "dossier_id": dossier_row["id"],
                "lifecycle_status": "dossier_draft",
            },
        )

        # Update JSON mirror
        legacy_id = db_row.get("legacy_id")
        if legacy_id:
            json_ideas = self._load_json_ideas()
            for j in json_ideas:
                if j.get("id") == legacy_id:
                    j["dossier_id"] = str(dossier_row["id"])
                    j["lifecycle_status"] = "dossier_draft"
            self._save_json_ideas(json_ideas)

        self.log_event(
            str(dossier_row["id"]),
            "dossier_created",
            actor,
            {"idea_id": str(db_row["id"]), "legacy_id": legacy_id, "slug": slug},
        )

        dossier_out = self.get_dossier(str(dossier_row["id"]))
        if not dossier_out:
            raise RuntimeError("Dossier créé mais lecture échouée")

        updated_idea = self.db.select("rnd_ideas", filters={"id": db_row["id"]}, limit=1)[0]
        idea_out = self.row_to_api_idea(updated_idea)
        return dossier_out, idea_out
    @staticmethod
    def _seed_section_content(idea: dict[str, Any]) -> dict[str, str]:
        """Pre-fill sections from existing idea evaluation data."""
        desc = idea.get("description", "")
        why = idea.get("why_now", "")
        reasoning = idea.get("agent_reasoning", "")
        next_step = idea.get("next_step", "")
        effort = idea.get("effort", "?")
        score = idea.get("score")
        verdict = idea.get("agent_verdict", "")

        seeds: dict[str, str] = {}
        if desc:
            seeds["problem"] = f"**Contexte initial**\n\n{desc}"
        if desc or why:
            seeds["solution"] = f"**Proposition**\n\n{desc}"
            if why:
                seeds["solution"] += f"\n\n**Pourquoi maintenant**\n\n{why}"
        if reasoning:
            seeds["market"] = f"**Analyse agent R&D**\n\n{reasoning}"
        if next_step:
            seeds["mvp"] = f"**Prochaine étape suggérée**\n\n{next_step}\n\n**Effort estimé :** {effort}"
        if reasoning:
            seeds["feasibility"] = (
                f"**Scores agent**\n"
                f"- Marché : {idea.get('market_score', '?')}/10\n"
                f"- Faisabilité : {idea.get('feasibility_score', '?')}/10\n"
                f"- Vision : {idea.get('vision_score', '?')}/10\n\n"
                f"{reasoning}"
            )
        seeds["business_case"] = "_Business case à générer (phase 2 — agent comptable)._"
        seeds["risks"] = "_Risques à identifier en comité._"
        if score is not None and verdict:
            seeds["decision"] = (
                f"**Verdict agent (pré-comité)** : {verdict} — score {score}/30\n\n"
                f"_Décision CEO en attente._"
            )
        return seeds
