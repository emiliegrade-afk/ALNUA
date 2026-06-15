"""Supabase + JSON persistence for R&D ideas and dossiers."""

from __future__ import annotations

import json
import logging
import os
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from config.paths import data_dir, get_hub_repo_path
from database.supabase_client import SupabaseClient, get_supabase
from services.rnd_schemas import (
    DOMAIN_TO_BRANCH,
    SECTION_DEFINITIONS,
    RndDossierAssetOut,
    RndDossierEventOut,
    RndDossierListItem,
    RndDossierOut,
    RndDossierSectionOut,
    RndIdeaOut,
)

logger = logging.getLogger(__name__)

RND_IDEAS_FILE = get_hub_repo_path() / "data" / "rnd_ideas.json"
RND_DOSSIERS_ROOT = data_dir("rnd_dossiers")


def _slugify(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
    return slug or "dossier"


def _is_uuid(value: str) -> bool:
    try:
        UUID(value)
        return True
    except ValueError:
        return False


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def _db_available(db: SupabaseClient | None) -> bool:
    if db is None:
        return False
    try:
        db.select("rnd_ideas", limit=1)
        return True
    except Exception as exc:
        logger.warning("rnd_repository: Supabase rnd_ideas unavailable: %s", exc)
        return False


class RndRepository:
    """CRUD for rnd_ideas and rnd_dossiers with JSON fallback."""

    def __init__(self, db: SupabaseClient | None = None) -> None:
        self.db = db or get_supabase()
        self._use_db = _db_available(self.db)

    # ------------------------------------------------------------------
    # JSON file helpers
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Idea mapping
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Ideas — read / sync
    # ------------------------------------------------------------------

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
        """Propositions actives — exclut dossiers promus et idées archivées."""
        if idea.dossier_id:
            return False
        if (idea.lifecycle_status or "raw") == "archived":
            return False
        return True

    def archive_idea(self, idea_id: str) -> bool:
        """Soft-delete a proposal (not allowed if already linked to a dossier)."""
        db_row = self.get_idea_db_row(idea_id)
        legacy_id: str | None = None

        if db_row:
            if db_row.get("dossier_id"):
                raise ValueError("Impossible de supprimer une idée déjà promue en dossier.")
            legacy_id = db_row.get("legacy_id")
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
                raise ValueError("Impossible de supprimer une idée déjà promue en dossier.")
            legacy_id = match.get("id")
            match["lifecycle_status"] = "archived"

        if legacy_id:
            json_ideas = self._load_json_ideas()
            for j in json_ideas:
                if j.get("id") == legacy_id:
                    j["lifecycle_status"] = "archived"
            self._save_json_ideas(json_ideas)

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

    # ------------------------------------------------------------------
    # Dossier helpers
    # ------------------------------------------------------------------

    @staticmethod
    def section_keys_for_domain(domain: str | None) -> list[str]:
        domain_norm = (domain or "autre").lower()
        keys = [
            "problem", "solution", "market", "mvp", "feasibility",
            "business_case", "risks", "decision",
        ]
        if domain_norm in ("hardware", "robotique", "robotics"):
            keys.insert(6, "manufacturing")
        if domain_norm in ("jeu", "game", "gaming"):
            keys.insert(6, "lore")
        keys.extend(["visual_identity", "social_strategy"])
        # Deduplicate while preserving order
        seen: set[str] = set()
        ordered: list[str] = []
        for k in keys:
            if k not in seen:
                seen.add(k)
                ordered.append(k)
        return ordered

    @staticmethod
    def branch_for_domain(domain: str | None) -> str:
        return DOMAIN_TO_BRANCH.get((domain or "").lower(), "other")

    def _ensure_local_dossier_dir(self, slug: str) -> Path:
        path = RND_DOSSIERS_ROOT / slug
        (path / "sections").mkdir(parents=True, exist_ok=True)
        return path

    def _write_local_dossier_skeleton(self, slug: str, title: str, sections: list[dict]) -> str:
        path = self._ensure_local_dossier_dir(slug)
        md_lines = [f"# {title}", "", f"*Dossier R&D ALNUA — {slug}*", "", "---", ""]
        for sec in sections:
            md_lines.append(f"## {sec['title']}")
            md_lines.append("")
            md_lines.append(sec.get("content_md") or "_À compléter._")
            md_lines.append("")
            sec_path = path / "sections" / f"{sec['section_key']}.md"
            sec_path.write_text(
                f"# {sec['title']}\n\n{sec.get('content_md') or '_À compléter._'}\n",
                encoding="utf-8",
            )
        dossier_md = path / "dossier.md"
        dossier_md.write_text("\n".join(md_lines), encoding="utf-8")
        return str(dossier_md.resolve())

    def _section_out(self, row: dict[str, Any]) -> RndDossierSectionOut:
        return RndDossierSectionOut(
            id=str(row["id"]),
            dossier_id=str(row["dossier_id"]),
            section_key=row["section_key"],
            title=row["title"],
            content_md=row.get("content_md", ""),
            status=row.get("status", "draft"),
            sort_order=row.get("sort_order", 0),
            validated_by=row.get("validated_by"),
            validated_at=row.get("validated_at"),
            revision_note=row.get("revision_note"),
        )

    def _dossier_out(
        self,
        row: dict[str, Any],
        sections: list[dict[str, Any]] | None = None,
        idea_legacy_id: str | None = None,
    ) -> RndDossierOut:
        sec_rows = sections or []
        sec_out = [self._section_out(s) for s in sec_rows]
        validated = sum(1 for s in sec_out if s.status == "validated")
        return RndDossierOut(
            id=str(row["id"]),
            idea_id=str(row["idea_id"]),
            idea_legacy_id=idea_legacy_id,
            slug=row["slug"],
            title=row["title"],
            tagline=row.get("tagline"),
            domain=row.get("domain", "autre"),
            branch=row.get("branch"),
            status=row.get("status", "draft"),
            ceo_status=row.get("ceo_status", "pending"),
            ceo_note=row.get("ceo_note"),
            committee_team=row.get("committee_team") or [],
            vision_snapshot=row.get("vision_snapshot"),
            competitive_context=row.get("competitive_context"),
            finance_json=row.get("finance_json"),
            deck_html_path=row.get("deck_html_path"),
            deck_pdf_path=row.get("deck_pdf_path"),
            one_pager_md=row.get("one_pager_md"),
            ceo_package_json=row.get("ceo_package_json"),
            committee_report_md=row.get("committee_report_md"),
            dispatch_json=row.get("dispatch_json"),
            dispatch_status=row.get("dispatch_status", "pending"),
            project_id=str(row["project_id"]) if row.get("project_id") else None,
            local_path=row.get("local_path"),
            sections=sec_out,
            sections_validated_count=validated,
            sections_total_count=len(sec_out),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )

    def log_event(
        self,
        dossier_id: str,
        event_type: str,
        actor: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        if not self._use_db:
            return
        try:
            self.db.insert(
                "rnd_dossier_events",
                {
                    "dossier_id": dossier_id,
                    "event_type": event_type,
                    "actor": actor,
                    "payload": payload or {},
                },
            )
        except Exception as exc:
            logger.warning("rnd_repository: log_event failed: %s", exc)

    # ------------------------------------------------------------------
    # Dossier CRUD
    # ------------------------------------------------------------------

    def list_dossiers(
        self,
        status: str | None = None,
        domain: str | None = None,
        limit: int = 50,
    ) -> list[RndDossierListItem]:
        if not self._use_db:
            return []
        try:
            rows = self.db.select("rnd_dossiers", order_by="updated_at", ascending=False, limit=limit)
            if status:
                rows = [r for r in rows if r.get("status") == status]
            if domain:
                rows = [r for r in rows if r.get("domain") == domain]

            items: list[RndDossierListItem] = []
            for row in rows:
                sections = self.db.select(
                    "rnd_dossier_sections",
                    filters={"dossier_id": row["id"]},
                )
                validated = sum(1 for s in sections if s.get("status") == "validated")
                idea_rows = self.db.select("rnd_ideas", filters={"id": row["idea_id"]}, limit=1)
                legacy = idea_rows[0].get("legacy_id") if idea_rows else None
                items.append(
                    RndDossierListItem(
                        id=str(row["id"]),
                        slug=row["slug"],
                        title=row["title"],
                        domain=row.get("domain", "autre"),
                        status=row.get("status", "draft"),
                        ceo_status=row.get("ceo_status", "pending"),
                        idea_legacy_id=legacy,
                        sections_validated_count=validated,
                        sections_total_count=len(sections),
                        created_at=row.get("created_at"),
                        updated_at=row.get("updated_at"),
                    )
                )
            return items
        except Exception as exc:
            logger.warning("rnd_repository: list_dossiers failed: %s", exc)
            return []

    def get_dossier(self, dossier_id: str) -> RndDossierOut | None:
        if not self._use_db:
            return None
        try:
            row = self._resolve_dossier_row(dossier_id)
            if not row:
                return None
            sections = self.db.select(
                "rnd_dossier_sections",
                filters={"dossier_id": row["id"]},
                order_by="sort_order",
                ascending=True,
            )
            idea_rows = self.db.select("rnd_ideas", filters={"id": row["idea_id"]}, limit=1)
            legacy = idea_rows[0].get("legacy_id") if idea_rows else None
            dossier = self._dossier_out(row, sections, legacy)
            return self._heal_dossier_status(dossier)
        except Exception as exc:
            logger.warning("rnd_repository: get_dossier failed: %s", exc)
            return None

    def _resolve_dossier_row(self, ref: str) -> dict[str, Any] | None:
        """Resolve dossier by UUID, slug (exact or slugified), or legacy idea id."""
        key = (ref or "").strip()
        if not key:
            return None

        if _is_uuid(key):
            rows = self.db.select("rnd_dossiers", filters={"id": key}, limit=1)
            if rows:
                return rows[0]

        for slug_candidate in (key, _slugify(key)[:60]):
            if not slug_candidate:
                continue
            rows = self.db.select("rnd_dossiers", filters={"slug": slug_candidate}, limit=1)
            if rows:
                return rows[0]

        idea_row = self.get_idea_db_row(key)
        if idea_row and idea_row.get("dossier_id"):
            rows = self.db.select(
                "rnd_dossiers",
                filters={"id": str(idea_row["dossier_id"])},
                limit=1,
            )
            if rows:
                return rows[0]

        return None

    def _heal_dossier_status(self, dossier: RndDossierOut) -> RndDossierOut:
        """Upgrade legacy statuses when a committee CR exists and no session is active."""
        if dossier.status not in ("draft", "committee_active"):
            return dossier
        if not dossier.committee_report_md or len(dossier.committee_report_md.strip()) < 40:
            return dossier
        try:
            from services.rnd_committee import get_committee_repository

            if get_committee_repository().get_active_session(dossier.id):
                return dossier
            healed = self.update_dossier(dossier.id, {"status": "partial_validated"})
            return healed or dossier
        except Exception as exc:
            logger.warning("rnd_repository: heal dossier status failed: %s", exc)
            return dossier

    def get_dossier_events(self, dossier_id: str, limit: int = 50) -> list[RndDossierEventOut]:
        if not self._use_db:
            return []
        try:
            rows = self.db.select(
                "rnd_dossier_events",
                filters={"dossier_id": dossier_id},
                order_by="created_at",
                ascending=False,
                limit=limit,
            )
            return [
                RndDossierEventOut(
                    id=str(r["id"]),
                    dossier_id=str(r["dossier_id"]),
                    event_type=r["event_type"],
                    actor=r["actor"],
                    payload=r.get("payload"),
                    created_at=r.get("created_at", ""),
                )
                for r in rows
            ]
        except Exception as exc:
            logger.warning("rnd_repository: get_dossier_events failed: %s", exc)
            return []

    def update_dossier(self, dossier_id: str, values: dict[str, Any]) -> RndDossierOut | None:
        if not self._use_db:
            return None
        try:
            row = self.db.update("rnd_dossiers", dossier_id, values)
            return self.get_dossier(str(row["id"]))
        except Exception as exc:
            logger.warning("rnd_repository: update_dossier failed: %s", exc)
            return None

    def load_competitive_context(self, limit_chars: int = 3000) -> str:
        """Load latest competitive anti-patterns from data/rnd_competitive/."""
        comp_dir = data_dir("rnd_competitive")
        if not comp_dir.exists():
            return ""
        parts: list[str] = []
        for path in sorted(comp_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)[:3]:
            try:
                parts.append(path.read_text(encoding="utf-8")[:1200])
            except Exception:
                pass
        return "\n\n---\n\n".join(parts)[:limit_chars]

    def update_section_content(
        self,
        dossier_id: str,
        section_key: str,
        content_md: str,
        *,
        status: str | None = None,
        revision_note: str | None = None,
    ) -> None:
        if not self._use_db:
            return
        rows = self.db.select(
            "rnd_dossier_sections",
            filters={"dossier_id": dossier_id, "section_key": section_key},
            limit=1,
        )
        if not rows:
            return
        values: dict[str, Any] = {"content_md": content_md}
        if status:
            values["status"] = status
        if revision_note is not None:
            values["revision_note"] = revision_note
        self.db.update("rnd_dossier_sections", rows[0]["id"], values)
        dossier = self.get_dossier(dossier_id)
        if dossier:
            self._write_local_dossier_skeleton(
                dossier.slug,
                dossier.title,
                [
                    {
                        "section_key": s.section_key,
                        "title": s.title,
                        "content_md": content_md if s.section_key == section_key else s.content_md,
                    }
                    for s in dossier.sections
                ],
            )

    def set_finance_json(self, dossier_id: str, finance: dict[str, Any]) -> None:
        if not self._use_db:
            return
        self.db.update("rnd_dossiers", dossier_id, {"finance_json": finance})

    def list_assets(self, dossier_id: str) -> list[RndDossierAssetOut]:
        if not self._use_db:
            return []
        try:
            rows = self.db.select(
                "rnd_dossier_assets",
                filters={"dossier_id": dossier_id},
                order_by="created_at",
                ascending=False,
            )
            return [
                RndDossierAssetOut(
                    id=str(r["id"]),
                    dossier_id=str(r["dossier_id"]),
                    section_key=r.get("section_key"),
                    asset_type=r["asset_type"],
                    file_path=r["file_path"],
                    public_url=r.get("public_url"),
                    image_prompt=r.get("image_prompt"),
                    generation_model=r.get("generation_model"),
                    width=r.get("width"),
                    height=r.get("height"),
                    metadata=r.get("metadata"),
                    created_at=r.get("created_at"),
                )
                for r in rows
            ]
        except Exception as exc:
            logger.warning("rnd_repository: list_assets failed: %s", exc)
            return []

    def create_asset(self, values: dict[str, Any]) -> RndDossierAssetOut | None:
        if not self._use_db:
            return None
        try:
            row = self.db.insert("rnd_dossier_assets", values)
            row = row[0] if isinstance(row, list) else row
            return RndDossierAssetOut(
                id=str(row["id"]),
                dossier_id=str(row["dossier_id"]),
                section_key=row.get("section_key"),
                asset_type=row["asset_type"],
                file_path=row["file_path"],
                public_url=row.get("public_url"),
                image_prompt=row.get("image_prompt"),
                generation_model=row.get("generation_model"),
                width=row.get("width"),
                height=row.get("height"),
                metadata=row.get("metadata"),
                created_at=row.get("created_at"),
            )
        except Exception as exc:
            logger.warning("rnd_repository: create_asset failed: %s", exc)
            return None

    def delete_assets(self, dossier_id: str) -> None:
        if not self._use_db:
            return
        try:
            rows = self.db.select("rnd_dossier_assets", filters={"dossier_id": dossier_id})
            for row in rows:
                self.db.delete("rnd_dossier_assets", row["id"])
        except Exception as exc:
            logger.warning("rnd_repository: delete_assets failed: %s", exc)

    def set_deck_paths(
        self,
        dossier_id: str,
        *,
        html_path: str | None,
        pdf_path: str | None = None,
        one_pager_md: str | None = None,
    ) -> RndDossierOut | None:
        if not self._use_db:
            return None
        values: dict[str, Any] = {}
        if html_path is not None:
            values["deck_html_path"] = html_path
        if pdf_path is not None:
            values["deck_pdf_path"] = pdf_path
        if one_pager_md is not None:
            values["one_pager_md"] = one_pager_md
        if not values:
            return self.get_dossier(dossier_id)
        try:
            self.db.update("rnd_dossiers", dossier_id, values)
            return self.get_dossier(dossier_id)
        except Exception as exc:
            logger.warning("rnd_repository: set_deck_paths failed: %s", exc)
            return None

    def validate_section(
        self,
        dossier_id: str,
        section_key: str,
        actor: str,
        note: str | None = None,
    ) -> RndDossierOut | None:
        if not self._use_db:
            return None
        rows = self.db.select(
            "rnd_dossier_sections",
            filters={"dossier_id": dossier_id, "section_key": section_key},
            limit=1,
        )
        if not rows:
            return None
        self.db.update(
            "rnd_dossier_sections",
            rows[0]["id"],
            {
                "status": "validated",
                "validated_by": actor,
                "validated_at": _now_iso(),
                "revision_note": note,
            },
        )
        self.log_event(
            dossier_id,
            "section_validated",
            actor,
            {"section_key": section_key, "note": note},
        )
        return self.get_dossier(dossier_id)

    def request_section_revision(
        self,
        dossier_id: str,
        section_key: str,
        revision_note: str,
        actor: str,
    ) -> RndDossierOut | None:
        if not self._use_db:
            return None
        rows = self.db.select(
            "rnd_dossier_sections",
            filters={"dossier_id": dossier_id, "section_key": section_key},
            limit=1,
        )
        if not rows:
            return None
        self.db.update(
            "rnd_dossier_sections",
            rows[0]["id"],
            {
                "status": "needs_revision",
                "revision_note": revision_note,
                "validated_by": None,
                "validated_at": None,
            },
        )
        self.log_event(
            dossier_id,
            "section_revision_requested",
            actor,
            {"section_key": section_key, "revision_note": revision_note},
        )
        return self.get_dossier(dossier_id)

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
        title = idea.get("title", "")
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


def get_rnd_repository() -> RndRepository:
    return RndRepository()
