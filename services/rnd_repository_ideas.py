"""Ideas JSON/DB persistence mixin."""
from __future__ import annotations

import json
import logging
from typing import Any

from services.rnd_repository_helpers import (
    RND_IDEAS_FILE,
    _is_uuid,
)
from services.rnd_schemas import (
    RndIdeaOut,
)

logger = logging.getLogger(__name__)

class RndIdeasMixin:
    def _load_json_ideas(self) -> list[dict[str, Any]]:
        try:
            RND_IDEAS_FILE.parent.mkdir(parents=True, exist_ok=True)
            if RND_IDEAS_FILE.exists():
                return json.loads(RND_IDEAS_FILE.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("rnd_repository: load json failed: %s", exc)
        return []
    def _save_json_ideas(self, ideas: list[dict[str, Any]]) -> None:
        try:
            RND_IDEAS_FILE.parent.mkdir(parents=True, exist_ok=True)
            by_id: dict[str, dict] = {}
            for idea in ideas:
                idea_id = idea.get("id")
                if idea_id:
                    by_id[idea_id] = idea
            RND_IDEAS_FILE.write_text(
                json.dumps(list(by_id.values()), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as exc:
            logger.warning("rnd_repository: save json failed: %s", exc)
    @staticmethod
    def json_idea_to_row(idea: dict[str, Any]) -> dict[str, Any]:
        legacy_id = idea.get("id") or idea.get("legacy_id")
        verdict = idea.get("verdict") or idea.get("agent_verdict")
        return {
            "legacy_id": legacy_id,
            "title": idea.get("title", "")[:500],
            "description": idea.get("description", "") or idea.get("title", ""),
            "domain": idea.get("domain"),
            "effort": idea.get("effort"),
            "why_now": idea.get("why_now"),
            "source": idea.get("source", "rnd_agent"),
            "status": idea.get("status", "pending_evaluation"),
            "score": idea.get("score"),
            "market_score": idea.get("market_score"),
            "feasibility_score": idea.get("feasibility_score"),
            "vision_score": idea.get("vision_score"),
            "agent_verdict": verdict,
            "agent_reasoning": idea.get("reasoning") or idea.get("verdict_reason"),
            "next_step": idea.get("next_step"),
            "spec_file": idea.get("spec_file"),
            "lifecycle_status": idea.get("lifecycle_status", "raw"),
            "dossier_id": idea.get("dossier_id"),
            "evaluated_at": idea.get("evaluated_at"),
        }
    @staticmethod
    def row_to_api_idea(row: dict[str, Any]) -> RndIdeaOut:
        legacy = row.get("legacy_id") or str(row.get("id", ""))
        verdict = row.get("agent_verdict")
        reasoning = row.get("agent_reasoning")
        dossier_id = row.get("dossier_id")
        return RndIdeaOut(
            id=legacy,
            db_id=str(row["id"]) if row.get("id") else None,
            title=row.get("title", ""),
            description=row.get("description", ""),
            source=row.get("source", "rnd_agent"),
            status=row.get("status"),
            score=row.get("score"),
            market_score=row.get("market_score"),
            feasibility_score=row.get("feasibility_score"),
            vision_score=row.get("vision_score"),
            verdict=verdict,
            verdict_reason=reasoning,
            reasoning=reasoning,
            next_step=row.get("next_step"),
            why_now=row.get("why_now"),
            effort=row.get("effort"),
            domain=row.get("domain"),
            spec_file=row.get("spec_file"),
            lifecycle_status=row.get("lifecycle_status", "raw"),
            dossier_id=str(dossier_id) if dossier_id else None,
            incubator_stage=row.get("incubator_stage") or "idee",
            created_at=row.get("created_at"),
            evaluated_at=row.get("evaluated_at"),
        )
    def _merge_json_into_api(self, json_ideas: list[dict]) -> list[RndIdeaOut]:
        return [
            RndIdeaOut(
                id=idea.get("id", ""),
                db_id=idea.get("db_id"),
                title=idea.get("title", ""),
                description=idea.get("description", "") or idea.get("title", ""),
                source=idea.get("source", "rnd_agent"),
                status=idea.get("status"),
                score=idea.get("score"),
                market_score=idea.get("market_score"),
                feasibility_score=idea.get("feasibility_score"),
                vision_score=idea.get("vision_score"),
                verdict=idea.get("verdict"),
                verdict_reason=idea.get("reasoning") or idea.get("verdict_reason"),
                reasoning=idea.get("reasoning") or idea.get("verdict_reason"),
                next_step=idea.get("next_step"),
                why_now=idea.get("why_now"),
                effort=idea.get("effort"),
                domain=idea.get("domain"),
                spec_file=idea.get("spec_file"),
                lifecycle_status=idea.get("lifecycle_status", "raw"),
                dossier_id=idea.get("dossier_id"),
                created_at=idea.get("created_at"),
                evaluated_at=idea.get("evaluated_at"),
            )
            for idea in json_ideas
            if idea.get("id")
        ]
    def _mark_json_idea_archived(
        self,
        idea_id: str,
        *,
        legacy_id: str | None = None,
        db_id: str | None = None,
    ) -> None:
        """Persist archived status in rnd_ideas.json (prevents R&D cycle from resurrecting)."""
        json_ideas = self._load_json_ideas()
        changed = False
        for j in json_ideas:
            jid = j.get("id")
            jdb = j.get("db_id")
            if (
                jid == idea_id
                or (legacy_id and jid == legacy_id)
                or (db_id and jdb == db_id)
                or jdb == idea_id
            ):
                j["lifecycle_status"] = "archived"
                changed = True
        if changed:
            self._save_json_ideas(json_ideas)
    def sync_idea_to_db(self, idea: dict[str, Any]) -> dict[str, Any] | None:
        """Upsert one idea from JSON dict into Supabase. Returns DB row or None."""
        if not self._use_db:
            return None
        legacy_id = idea.get("id")
        if not legacy_id:
            return None
        row_data = self.json_idea_to_row(idea)
        try:
            existing = self.db.select("rnd_ideas", filters={"legacy_id": legacy_id}, limit=1)
            if existing:
                # Never resurrect an archived idea when JSON is stale (e.g. after partial archive).
                if existing[0].get("lifecycle_status") == "archived":
                    row_data["lifecycle_status"] = "archived"
                    idea["lifecycle_status"] = "archived"
                updated = self.db.update("rnd_ideas", existing[0]["id"], row_data)
                idea["db_id"] = updated["id"]
                return updated
            inserted = self.db.insert("rnd_ideas", row_data)
            idea["db_id"] = inserted["id"]
            return inserted
        except Exception as exc:
            logger.warning("rnd_repository: sync_idea_to_db failed for %s: %s", legacy_id, exc)
            return None
    def sync_all_json_to_db(self) -> int:
        """Migrate all JSON ideas to Supabase. Returns count synced."""
        ideas = self._load_json_ideas()
        count = 0
        for idea in ideas:
            if self.sync_idea_to_db(idea):
                count += 1
        self._save_json_ideas(ideas)
        return count
    def get_top_ideas(
        self,
        limit: int = 50,
        verdict: str | None = None,
        inbox_only: bool = False,
    ) -> list[RndIdeaOut]:
        """Load ideas from Supabase (preferred) merged with JSON extras."""
        json_ideas = self._load_json_ideas()
        by_legacy: dict[str, RndIdeaOut] = {
            i.id: i for i in self._merge_json_into_api(json_ideas)
        }

        if self._use_db:
            try:
                rows = self.db.select("rnd_ideas", order_by="score", ascending=False, limit=200)
                for row in rows:
                    api = self.row_to_api_idea(row)
                    key = row.get("legacy_id") or api.id
                    by_legacy[key] = api
                    # Keep JSON in sync with db_id
                    for j in json_ideas:
                        if j.get("id") == key:
                            j["db_id"] = str(row["id"])
                            j["dossier_id"] = str(row["dossier_id"]) if row.get("dossier_id") else j.get("dossier_id")
                            j["lifecycle_status"] = row.get("lifecycle_status", j.get("lifecycle_status", "raw"))
            except Exception as exc:
                logger.warning("rnd_repository: get_top_ideas db failed: %s", exc)

        result = list(by_legacy.values())
        if inbox_only:
            result = [i for i in result if self._is_inbox_idea(i)]
        if verdict:
            result = [i for i in result if (i.verdict or "").upper() == verdict.upper()]
        result.sort(key=lambda x: x.score or 0, reverse=True)
        return result[:limit]
    @staticmethod
    def _is_inbox_idea(idea: RndIdeaOut) -> bool:
        """Propositions actives ??? exclut dossiers promus et id??es archiv??es."""
        if idea.dossier_id:
            return False
        if (idea.lifecycle_status or "raw") == "archived":
            return False
        return True
    def archive_idea(self, idea_id: str) -> bool:
        """Soft-delete a proposal (not allowed if already linked to a dossier)."""
        db_row = self.get_idea_db_row(idea_id)
        legacy_id: str | None = None
        db_id: str | None = None

        if db_row:
            if db_row.get("dossier_id"):
                raise ValueError("Impossible de supprimer une id??e d??j?? promue en dossier.")
            legacy_id = db_row.get("legacy_id")
            db_id = str(db_row["id"]) if db_row.get("id") else None
            self.db.update(
                "rnd_ideas",
                db_row["id"],
                {"lifecycle_status": "archived"},
            )
        else:
            json_ideas = self._load_json_ideas()
            match = next(
                (i for i in json_ideas if i.get("id") == idea_id or i.get("db_id") == idea_id),
                None,
            )
            if not match:
                return False
            if match.get("dossier_id"):
                raise ValueError("Impossible de supprimer une id??e d??j?? promue en dossier.")
            legacy_id = match.get("id")
            db_id = match.get("db_id")

        self._mark_json_idea_archived(idea_id, legacy_id=legacy_id, db_id=db_id)
        return True
    def get_idea_by_id(self, idea_id: str) -> RndIdeaOut | None:
        """Find idea by legacy_id or UUID."""
        if self._use_db:
            try:
                if _is_uuid(idea_id):
                    rows = self.db.select("rnd_ideas", filters={"id": idea_id}, limit=1)
                else:
                    rows = self.db.select("rnd_ideas", filters={"legacy_id": idea_id}, limit=1)
                if rows:
                    return self.row_to_api_idea(rows[0])
            except Exception as exc:
                logger.warning("rnd_repository: get_idea_by_id db: %s", exc)

        for idea in self._load_json_ideas():
            if idea.get("id") == idea_id or idea.get("db_id") == idea_id:
                merged = self._merge_json_into_api([idea])
                return merged[0] if merged else None
        return None
    def get_idea_db_row(self, idea_id: str) -> dict[str, Any] | None:
        """Raw DB row for internal use."""
        if not self._use_db:
            return None
        try:
            if _is_uuid(idea_id):
                rows = self.db.select("rnd_ideas", filters={"id": idea_id}, limit=1)
            else:
                rows = self.db.select("rnd_ideas", filters={"legacy_id": idea_id}, limit=1)
            return rows[0] if rows else None
        except Exception:
            return None
    def save_ideas_json(self, ideas: list[dict[str, Any]]) -> None:
        """Save to JSON and dual-write each to Supabase."""
        for idea in ideas:
            self.sync_idea_to_db(idea)
        self._save_json_ideas(ideas)
