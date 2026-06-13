"""Product page repository and builders for R&D dossiers (phase 7)."""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config.settings import get_settings
from database.supabase_client import SupabaseClient, get_supabase
from services.rnd_deck_generator import _is_placeholder, md_to_html
from services.rnd_schemas import RndDossierOut, RndProductPageOut
from services.rnd_social import SOCIAL_UNLOCK_STATUSES, is_social_pipeline_unlocked

logger = logging.getLogger(__name__)

RND_DOSSIERS_ROOT = Path(
    __import__("os").getenv("HUB_REPO_PATH", "C:/Dev/ALUNA_HUB")
) / "data" / "rnd_dossiers"


class ProductPipelineLockedError(ValueError):
    """Raised when product page actions are attempted before CEO approval."""


def is_product_pipeline_unlocked(status: str, ceo_status: str | None = None) -> bool:
    """Fiche produit : après validation CEO (même règle que social)."""
    return is_social_pipeline_unlocked(status, ceo_status)


def assert_product_pipeline_unlocked(dossier: RndDossierOut) -> None:
    if is_product_pipeline_unlocked(dossier.status, dossier.ceo_status):
        return
    raise ProductPipelineLockedError(
        "Fiche produit verrouillée pendant la phase R&D. "
        "Disponible après validation CEO du dossier "
        f"(statut actuel : {dossier.status})."
    )


def product_page_public_url(slug: str) -> str:
    base = get_settings().beta_portal_base_url.rstrip("/")
    return f"{base}/p/{slug}"


def waitlist_public_url(project_slug: str) -> str:
    base = get_settings().beta_portal_base_url.rstrip("/")
    return f"{base}/waitlist/{project_slug}"


class RndProductRepository:
    def __init__(self, db: SupabaseClient | None = None) -> None:
        self.db = db or get_supabase()

    def get_by_dossier_id(self, dossier_id: str) -> RndProductPageOut | None:
        rows = self.db.select(
            "rnd_product_pages",
            filters={"dossier_id": dossier_id},
            limit=1,
        )
        return self._to_out(rows[0]) if rows else None

    def get_by_slug(self, slug: str, *, published_only: bool = False) -> RndProductPageOut | None:
        rows = self.db.select(
            "rnd_product_pages",
            filters={"slug": slug},
            limit=1,
        )
        if not rows:
            return None
        page = self._to_out(rows[0])
        if published_only and not page.published:
            return None
        return page

    def upsert(self, values: dict[str, Any]) -> RndProductPageOut:
        dossier_id = values["dossier_id"]
        existing = self.get_by_dossier_id(dossier_id)
        if existing:
            row = self.db.update("rnd_product_pages", existing.id, values)
        else:
            row = self.db.insert("rnd_product_pages", values)
            row = row[0] if isinstance(row, list) else row
        return self._to_out(row)

    def update(self, page_id: str, values: dict[str, Any]) -> RndProductPageOut:
        row = self.db.update("rnd_product_pages", page_id, values)
        return self._to_out(row)

    def write_local_page(self, slug: str, payload: dict[str, Any]) -> str:
        folder = RND_DOSSIERS_ROOT / slug / "product"
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / "page.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return str(path.resolve())

    @staticmethod
    def _to_out(row: dict[str, Any]) -> RndProductPageOut:
        return RndProductPageOut(
            id=str(row["id"]),
            dossier_id=str(row["dossier_id"]),
            project_id=str(row["project_id"]) if row.get("project_id") else None,
            slug=row["slug"],
            title=row["title"],
            tagline=row.get("tagline"),
            description_html=row.get("description_html"),
            hero_asset_id=str(row["hero_asset_id"]) if row.get("hero_asset_id") else None,
            features=row.get("features") or [],
            pricing_model=row.get("pricing_model"),
            faq=row.get("faq") or [],
            seo_title=row.get("seo_title"),
            seo_description=row.get("seo_description"),
            waitlist_enabled=bool(row.get("waitlist_enabled")),
            published=bool(row.get("published")),
            published_at=row.get("published_at"),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )


def get_rnd_product_repository() -> RndProductRepository:
    return RndProductRepository()


def _section_text(dossier: RndDossierOut, key: str) -> str:
    sec = next((s for s in dossier.sections if s.section_key == key), None)
    if not sec or _is_placeholder(sec.content_md):
        return ""
    return sec.content_md.strip()


def _extract_bullets(md: str, limit: int = 4) -> list[str]:
    items: list[str] = []
    for line in md.splitlines():
        stripped = line.strip()
        if stripped.startswith(("- ", "* ", "• ")):
            text = re.sub(r"^[-*•]\s+", "", stripped).strip()
            text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
            if len(text) >= 8:
                items.append(text)
        if len(items) >= limit:
            break
    return items


def build_features(dossier: RndDossierOut) -> list[dict[str, str]]:
    mvp = _section_text(dossier, "mvp")
    solution = _section_text(dossier, "solution")
    bullets = _extract_bullets(mvp) or _extract_bullets(solution)
    features: list[dict[str, str]] = []
    for i, text in enumerate(bullets[:4]):
        title = text.split("—")[0].split(":")[0].strip()[:72]
        features.append({"title": title or f"Feature {i + 1}", "description": text[:280]})
    if not features:
        features = [
            {
                "title": "Proposition de valeur",
                "description": (dossier.tagline or dossier.title)[:280],
            },
            {
                "title": "MVP ciblé",
                "description": "Scope v1 défini en comité R&D — pas de sur-promesse.",
            },
        ]
    return features


def build_faq(dossier: RndDossierOut) -> list[dict[str, str]]:
    risks = _section_text(dossier, "risks")
    decision = _section_text(dossier, "decision")
    faq: list[dict[str, str]] = [
        {
            "question": "Quand sera-t-il disponible ?",
            "answer": (
                "Inscription waitlist ouverte — lancement progressif après validation CEO "
                "et phase de conception ALNUA."
            ),
        },
        {
            "question": "Pour qui est ce produit ?",
            "answer": (_section_text(dossier, "problem") or dossier.tagline or dossier.title)[:400],
        },
    ]
    if risks:
        faq.append({
            "question": "Quels sont les principaux risques ?",
            "answer": risks[:500],
        })
    if decision:
        faq.append({
            "question": "Quelle est la recommandation R&D ?",
            "answer": decision[:500],
        })
    return faq[:5]


def build_pricing_label(dossier: RndDossierOut) -> str | None:
    finance = dossier.finance_json or {}
    rev = finance.get("revenue_hypothesis") or {}
    pm = rev.get("pricing_model") or {}
    if pm.get("model_type") == "subscription" and pm.get("tiers"):
        tiers = pm["tiers"]
        prices = [t.get("price_eur") for t in tiers if t.get("price_eur")]
        if prices:
            lo, hi = min(prices), max(prices)
            return f"Abonnement dès {lo:.0f}€/mois" if lo != hi else f"Abonnement {lo:.0f}€/mois"
    if pm.get("blended_arpu_eur"):
        return f"À partir de {pm['blended_arpu_eur']:.0f}€/mois (estimation R&D)"
    return None


def build_description_html(dossier: RndDossierOut) -> str:
    parts: list[str] = []
    problem = _section_text(dossier, "problem")
    solution = _section_text(dossier, "solution")
    market = _section_text(dossier, "market")

    if problem:
        parts.append(f"## Le problème\n\n{problem}")
    if solution:
        parts.append(f"## La solution\n\n{solution}")
    if market:
        parts.append(f"## Marché\n\n{market[:1200]}")

    if not parts:
        tagline = dossier.tagline or dossier.title
        parts.append(f"## {dossier.title}\n\n{tagline}")

    return md_to_html("\n\n".join(parts))


def build_product_page_payload(
    dossier: RndDossierOut,
    *,
    project_id: str | None,
    hero_asset_id: str | None,
    waitlist_enabled: bool = True,
) -> dict[str, Any]:
    tagline = dossier.tagline or _first_line(_section_text(dossier, "solution")) or dossier.title
    seo_title = f"{dossier.title} — ALNUA"
    seo_desc = tagline[:155]
    return {
        "dossier_id": dossier.id,
        "project_id": project_id,
        "slug": dossier.slug,
        "title": dossier.title,
        "tagline": tagline[:240],
        "description_html": build_description_html(dossier),
        "hero_asset_id": hero_asset_id,
        "features": build_features(dossier),
        "pricing_model": build_pricing_label(dossier),
        "faq": build_faq(dossier),
        "seo_title": seo_title,
        "seo_description": seo_desc,
        "waitlist_enabled": waitlist_enabled,
        "published": False,
    }


def _first_line(md: str) -> str:
    for line in md.splitlines():
        t = line.strip().lstrip("#").strip()
        if len(t) >= 12:
            return t[:240]
    return ""


def enrich_public_page(
    page: RndProductPageOut,
    *,
    dossier_id: str,
    project_slug: str | None = None,
) -> dict[str, Any]:
    data = page.model_dump()
    data["public_url"] = product_page_public_url(page.slug)
    data["hero_url"] = (
        f"/rnd/dossiers/{dossier_id}/assets/file?asset_type=hero"
        if page.hero_asset_id
        else None
    )
    if page.waitlist_enabled and project_slug:
        data["waitlist_url"] = waitlist_public_url(project_slug)
        data["project_slug"] = project_slug
    return data
