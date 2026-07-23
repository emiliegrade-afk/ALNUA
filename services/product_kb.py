"""Product knowledge base per app slug — SAV lite (Nadia)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ProductKbEntry(BaseModel):
    slug: str
    name: str = ""
    support_email: str = ""
    faq_md: str = ""
    tone: str = "professionnel et chaleureux"
    auto_reply_ok: bool = False
    escalation_rules: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    updated_at: str | None = None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_db():
    from database.supabase_client import get_supabase

    return get_supabase()


def sync_kb_from_registry(*, only_prod_beta: bool = False) -> dict[str, Any]:
    """Upsert product_kb rows from apps registry (enabled apps)."""
    from services.app_registry import list_apps

    db = _get_db()
    synced = 0
    for app in list_apps(include_disabled=False):
        if app.slug == "hub":
            continue
        if only_prod_beta and getattr(app, "lifecycle_status", "build") not in (
            "beta",
            "prod",
        ):
            continue
        row = {
            "slug": app.slug,
            "name": app.name,
            "support_email": "",
            "faq_md": (
                f"## {app.name}\n"
                f"- Produit ALNUA ({app.branch})\n"
                f"- Stack : {app.stack or 'n/a'}\n"
                f"- URL prod : {app.prod_url or 'non publiée'}\n"
            ),
            "updated_at": _now_iso(),
        }
        try:
            existing = db.select("product_kb", filters={"slug": app.slug}, limit=1)
            if existing:
                db.update("product_kb", existing[0]["slug"], row, id_column="slug")
            else:
                db.insert("product_kb", row)
            synced += 1
        except Exception as exc:
            logger.warning("product_kb sync %s failed: %s", app.slug, exc)
    return {"synced": synced}


def ensure_kb(slug: str) -> ProductKbEntry | None:
    """Return KB row, syncing from registry once if missing."""
    kb = get_kb(slug)
    if kb:
        return kb
    sync_kb_from_registry()
    return get_kb(slug)


def get_kb(slug: str) -> ProductKbEntry | None:
    try:
        rows = _get_db().select("product_kb", filters={"slug": slug}, limit=1)
        if not rows:
            return None
        return ProductKbEntry(**rows[0])
    except Exception as exc:
        logger.debug("get_kb failed: %s", exc)
        return None


def upsert_kb(
    slug: str,
    *,
    name: str = "",
    faq_md: str = "",
    support_email: str = "",
    auto_reply_ok: bool = False,
    tone: str = "professionnel et chaleureux",
    escalation_rules: str = "",
) -> ProductKbEntry | None:
    db = _get_db()
    payload = {
        "slug": slug,
        "name": name or slug,
        "faq_md": faq_md,
        "support_email": support_email,
        "auto_reply_ok": auto_reply_ok,
        "tone": tone,
        "escalation_rules": escalation_rules,
        "updated_at": _now_iso(),
    }
    try:
        existing = db.select("product_kb", filters={"slug": slug}, limit=1)
        if existing:
            db.update("product_kb", slug, payload, id_column="slug")
        else:
            db.insert("product_kb", payload)
        return get_kb(slug)
    except Exception as exc:
        logger.warning("upsert_kb failed: %s", exc)
        return None


def list_kb() -> list[ProductKbEntry]:
    try:
        rows = _get_db().select("product_kb", order_by="slug", ascending=True, limit=100)
        return [ProductKbEntry(**r) for r in rows]
    except Exception as exc:
        logger.debug("list_kb failed: %s", exc)
        return []


def build_kb_context(slug: str) -> str:
    """Registry + KB + optional Mem0 lessons for Nadia."""
    from services.app_registry import get_app

    parts: list[str] = []
    app = get_app(slug)
    if app:
        parts.append(
            f"Produit : {app.name} ({app.branch}) — lifecycle {getattr(app, 'lifecycle_status', 'build')}"
        )
        if app.prod_url:
            parts.append(f"URL : {app.prod_url}")
        if app.description:
            parts.append(f"Description : {app.description[:400]}")

    kb = get_kb(slug)
    if kb:
        if kb.faq_md:
            parts.append(f"## FAQ produit\n{kb.faq_md[:3000]}")
        if kb.escalation_rules:
            parts.append(f"## Règles escalade CEO\n{kb.escalation_rules[:800]}")
        parts.append(f"Ton réponse : {kb.tone}")
        parts.append(f"Auto-réponse autorisée : {'oui' if kb.auto_reply_ok else 'non — brouillon pour Emilie'}")

    try:
        from skills.skill_mem0 import recall

        mem = recall(f"support SAV {slug} FAQ réponses clients", agent_id="secretary", limit=3)
        if mem and len(mem) > 30:
            parts.append(f"## Leçons SAV (mémoire)\n{mem[:1200]}")
    except Exception:
        pass

    return "\n\n".join(parts) if parts else f"Produit {slug} — peu de contexte KB."
