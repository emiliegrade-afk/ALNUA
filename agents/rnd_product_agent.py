"""Orchestrate public product pages for R&D dossiers (phase 7)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from agents.rnd_social_agent import ensure_project_for_dossier
from services.beta_portal import project_slug_for
from services.rnd_product import (
    assert_product_pipeline_unlocked,
    build_product_page_payload,
    enrich_public_page,
    get_rnd_product_repository,
    is_product_pipeline_unlocked,
    product_page_public_url,
    waitlist_public_url,
)
from services.rnd_repository import get_rnd_repository
from services.rnd_schemas import RndDossierOut, RndProductPageOut

logger = logging.getLogger(__name__)


class RndProductAgent:
    AGENT_NAME = "rnd_product_agent"

    def __init__(self) -> None:
        self.repo = get_rnd_repository()
        self.product = get_rnd_product_repository()

    def product_status(self, dossier_id: str) -> dict[str, Any]:
        dossier = self._require_dossier(dossier_id)
        page = self.product.get_by_dossier_id(dossier.id)
        unlocked = is_product_pipeline_unlocked(dossier.status, dossier.ceo_status)
        project_slug = self._project_slug(dossier, page)
        return {
            "unlocked": unlocked,
            "dossier_status": dossier.status,
            "ceo_status": dossier.ceo_status,
            "message": (
                "Fiche produit disponible — génère le brouillon puis publie."
                if unlocked
                else "Fiche produit verrouillée — validation CEO requise."
            ),
            "page": self._page_response(page, dossier, project_slug) if page else None,
            "can_generate": unlocked,
            "can_publish": unlocked and page is not None and not page.published,
            "can_unpublish": bool(page and page.published),
            "public_url": product_page_public_url(dossier.slug) if page else None,
        }

    def get_product_page(self, dossier_id: str) -> dict[str, Any]:
        dossier = self._require_dossier(dossier_id)
        page = self.product.get_by_dossier_id(dossier.id)
        if not page:
            return {
                "dossier_id": dossier.id,
                "page": None,
                "message": "Aucune fiche produit — génère-la après validation CEO.",
            }
        project_slug = self._project_slug(dossier, page)
        return {
            "dossier_id": dossier.id,
            "page": self._page_response(page, dossier, project_slug),
            "message": "Fiche produit chargée.",
        }

    def generate_product_page(
        self,
        dossier_id: str,
        *,
        force: bool = False,
        waitlist_enabled: bool | None = None,
        actor: str = "rnd_product_agent",
    ) -> dict[str, Any]:
        dossier = self._require_dossier(dossier_id)
        assert_product_pipeline_unlocked(dossier)

        existing = self.product.get_by_dossier_id(dossier.id)
        if existing and existing.published and not force:
            return {
                "page": self._page_response(existing, dossier, self._project_slug(dossier, existing)),
                "created": False,
                "message": "Fiche déjà publiée — unpublish ou force=true pour regénérer.",
            }

        project_id = ensure_project_for_dossier(dossier, self.repo.db)
        hero = next(
            (a for a in self.repo.list_assets(dossier.id) if a.asset_type == "hero"),
            None,
        )
        wl = waitlist_enabled if waitlist_enabled is not None else (
            existing.waitlist_enabled if existing else True
        )
        payload = build_product_page_payload(
            dossier,
            project_id=project_id,
            hero_asset_id=hero.id if hero else None,
            waitlist_enabled=wl,
        )
        if existing and not existing.published:
            payload.pop("published", None)

        page = self.product.upsert(payload)
        local_payload = page.model_dump()
        local_payload["generated_at"] = datetime.now(timezone.utc).isoformat()
        self.product.write_local_page(dossier.slug, local_payload)

        self.repo.log_event(
            dossier.id,
            "product_page_generated",
            actor,
            {"slug": page.slug, "waitlist_enabled": page.waitlist_enabled},
        )

        project_slug = self._project_slug(dossier, page)
        return {
            "page": self._page_response(page, dossier, project_slug),
            "created": True,
            "message": f"Fiche produit « {page.title} » générée — prête à publier.",
        }

    def update_product_page(
        self,
        dossier_id: str,
        *,
        values: dict[str, Any],
        actor: str = "emilie",
    ) -> dict[str, Any]:
        dossier = self._require_dossier(dossier_id)
        page = self.product.get_by_dossier_id(dossier.id)
        if not page:
            raise ValueError("Fiche produit introuvable — génère-la d'abord.")

        allowed = {
            k: v
            for k, v in values.items()
            if k
            in (
                "tagline",
                "description_html",
                "features",
                "faq",
                "pricing_model",
                "seo_title",
                "seo_description",
                "waitlist_enabled",
            )
            and v is not None
        }
        if not allowed:
            raise ValueError("Aucun champ à mettre à jour")

        updated = self.product.update(page.id, allowed)
        self.repo.log_event(dossier.id, "product_page_updated", actor, {"fields": list(allowed)})
        project_slug = self._project_slug(dossier, updated)
        return {
            "page": self._page_response(updated, dossier, project_slug),
            "message": "Fiche produit mise à jour.",
        }

    def publish_product_page(
        self,
        dossier_id: str,
        *,
        actor: str = "emilie",
    ) -> dict[str, Any]:
        dossier = self._require_dossier(dossier_id)
        assert_product_pipeline_unlocked(dossier)
        page = self.product.get_by_dossier_id(dossier.id)
        if not page:
            raise ValueError("Fiche produit introuvable — génère-la d'abord.")
        if page.published:
            return {
                "page": self._page_response(page, dossier, self._project_slug(dossier, page)),
                "message": "Fiche déjà publique.",
                "public_url": product_page_public_url(page.slug),
            }

        now = datetime.now(timezone.utc).isoformat()
        updated = self.product.update(
            page.id,
            {"published": True, "published_at": now},
        )
        self.repo.update_dossier(
            dossier.id,
            {"status": "published"},
        )
        self.repo.log_event(
            dossier.id,
            "product_page_published",
            actor,
            {"slug": page.slug, "public_url": product_page_public_url(page.slug)},
        )
        project_slug = self._project_slug(dossier, updated)
        return {
            "page": self._page_response(updated, dossier, project_slug),
            "message": f"Fiche publiée — {product_page_public_url(page.slug)}",
            "public_url": product_page_public_url(page.slug),
        }

    def unpublish_product_page(
        self,
        dossier_id: str,
        *,
        actor: str = "emilie",
    ) -> dict[str, Any]:
        dossier = self._require_dossier(dossier_id)
        page = self.product.get_by_dossier_id(dossier.id)
        if not page:
            raise ValueError("Fiche produit introuvable")
        if not page.published:
            return {
                "page": self._page_response(page, dossier, self._project_slug(dossier, page)),
                "message": "Fiche déjà non publiée.",
            }

        updated = self.product.update(page.id, {"published": False, "published_at": None})
        if dossier.status == "published":
            self.repo.update_dossier(dossier.id, {"status": "in_conception"})
        self.repo.log_event(dossier.id, "product_page_unpublished", actor, {"slug": page.slug})
        project_slug = self._project_slug(dossier, updated)
        return {
            "page": self._page_response(updated, dossier, project_slug),
            "message": "Fiche retirée du site public.",
        }

    def get_public_page(self, slug: str) -> dict[str, Any]:
        page = self.product.get_by_slug(slug, published_only=True)
        if not page:
            raise ValueError("Fiche produit introuvable ou non publiée")

        dossier = self.repo.get_dossier(page.dossier_id)
        if not dossier:
            raise ValueError("Dossier associé introuvable")

        project_slug = self._project_slug(dossier, page)
        data = enrich_public_page(page, dossier_id=dossier.id, project_slug=project_slug)
        if page.waitlist_enabled and project_slug:
            data["waitlist_url"] = waitlist_public_url(project_slug)
        return data

    def _require_dossier(self, dossier_id: str) -> RndDossierOut:
        dossier = self.repo.get_dossier(dossier_id)
        if not dossier:
            raise ValueError("Dossier introuvable")
        return dossier

    def _project_slug(
        self,
        dossier: RndDossierOut,
        page: RndProductPageOut | None,
    ) -> str | None:
        pid = (page.project_id if page else None) or dossier.project_id
        if not pid:
            return None
        rows = self.repo.db.select("projects", filters={"id": pid}, limit=1)
        if not rows:
            return None
        return project_slug_for(rows[0])

    def _page_response(
        self,
        page: RndProductPageOut,
        dossier: RndDossierOut,
        project_slug: str | None,
    ) -> dict[str, Any]:
        return enrich_public_page(page, dossier_id=dossier.id, project_slug=project_slug)
