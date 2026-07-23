"""SAV lite — Nadia drafts support replies; CEO validates sensitive cases."""

from __future__ import annotations

import logging
import re
from typing import Any, Literal

from pydantic import BaseModel, Field

from services.product_kb import build_kb_context, ensure_kb

logger = logging.getLogger(__name__)

SavCategory = Literal["bug", "howto", "billing", "complaint", "feature", "other"]
SavStatus = Literal[
    "open", "draft_ready", "awaiting_ceo", "replied", "escalated", "closed"
]

_CEO_REQUIRED_CATEGORIES = frozenset({"billing", "complaint"})
_SENSITIVE_PATTERNS = re.compile(
    r"remboursement|refund|facture|paiement|rgpd|données personnelles|"
    r"avocat|plainte|harcèlement|menace|juridique",
    re.I,
)


class SavCaseIn(BaseModel):
    product_slug: str = Field(..., min_length=1, max_length=64)
    subject: str = Field(..., min_length=1, max_length=300)
    body: str = Field(..., min_length=1, max_length=8000)
    channel: str = "manual"
    customer_ref: str = ""


class SavCaseOut(BaseModel):
    id: str
    product_slug: str
    channel: str
    customer_ref: str | None = None
    subject: str
    body: str
    category: str
    status: str
    draft_reply: str | None = None
    needs_ceo: bool = False
    confidence: float = 0.0
    created_at: str | None = None


def _get_db():
    from database.supabase_client import get_supabase

    return get_supabase()


def _classify_and_draft(
    *,
    product_slug: str,
    subject: str,
    body: str,
    kb_context: str,
) -> dict[str, Any]:
    from agents.base import LLMClient, parse_json_response
    from agents.secretary_agent import SecretaryAgent

    prompt = f"""Tu es Nadia, support ALNUA pour le produit « {product_slug} ».

CONTEXTE PRODUIT :
{kb_context[:4000]}

DEMANDE CLIENT :
Objet : {subject}
Message :
{body[:3000]}

Tâche :
1. Classe : bug | howto | billing | complaint | feature | other
2. Rédige une réponse client (FR) — utile, concise, pas de promesse non fondée
3. confidence 0.0-1.0 (certitude que la réponse est correcte sans CEO)
4. needs_ceo : true si remboursement, plainte grave, juridique, ou incertitude forte

JSON uniquement :
{{
  "category": "howto",
  "draft_reply": "...",
  "confidence": 0.85,
  "needs_ceo": false,
  "ceo_reason": ""
}}"""

    llm = LLMClient()
    raw = llm.complete(
        SecretaryAgent.SYSTEM_PROMPT,
        prompt,
        agent_id="secretary",
        temperature=0.35,
    )
    result = parse_json_response(raw)
    if _SENSITIVE_PATTERNS.search(f"{subject} {body}"):
        result["needs_ceo"] = True
        result["ceo_reason"] = (result.get("ceo_reason") or "") + " Mots-clés sensibles détectés."
    if result.get("category") in _CEO_REQUIRED_CATEGORIES:
        result["needs_ceo"] = True
    return result


def process_sav_case(payload: SavCaseIn) -> dict[str, Any]:
    """
    Create SAV case + Nadia draft.
    CEO validates when needs_ceo; ops autonomes pour howto/bug si auto_reply_ok.
    """
    slug = payload.product_slug.strip().lower()
    kb = ensure_kb(slug)
    if not kb:
        return {"success": False, "error": f"Produit inconnu : {slug}"}

    kb_context = build_kb_context(slug)
    analysis = _classify_and_draft(
        product_slug=slug,
        subject=payload.subject,
        body=payload.body,
        kb_context=kb_context,
    )

    category = str(analysis.get("category") or "other")
    confidence = float(analysis.get("confidence") or 0.5)
    needs_ceo = bool(analysis.get("needs_ceo"))
    draft = str(analysis.get("draft_reply") or "").strip()

    if not kb.auto_reply_ok:
        needs_ceo = True
    if confidence < 0.72:
        needs_ceo = True

    if needs_ceo:
        status: SavStatus = "awaiting_ceo"
    elif draft:
        status = "draft_ready"
    else:
        status = "open"

    row = {
        "product_slug": slug,
        "channel": payload.channel,
        "customer_ref": payload.customer_ref or None,
        "subject": payload.subject[:300],
        "body": payload.body[:8000],
        "category": category,
        "status": status,
        "draft_reply": draft,
        "needs_ceo": needs_ceo,
        "confidence": confidence,
    }

    try:
        created = _get_db().insert("sav_cases", row)
        case_id = str(created.get("id") if isinstance(created, dict) else created[0]["id"])
    except Exception as exc:
        logger.exception("sav_cases insert failed")
        return {"success": False, "error": str(exc)}

    notify_msg = None
    if needs_ceo:
        try:
            from skills.skill_telegram_notify import notify_telegram

            notify_msg = (
                f"📩 SAV {slug} — validation CEO requise\n"
                f"{payload.subject[:80]}\n"
                f"Catégorie : {category} · confiance {confidence:.0%}"
            )
            notify_telegram(notify_msg)
        except Exception:
            pass

    return {
        "success": True,
        "case_id": case_id,
        "status": status,
        "needs_ceo": needs_ceo,
        "category": category,
        "confidence": confidence,
        "draft_reply": draft,
        "ceo_notified": bool(notify_msg),
    }


def list_sav_cases(
    *,
    product_slug: str | None = None,
    status: str | None = None,
    needs_ceo: bool | None = None,
    limit: int = 30,
) -> list[dict[str, Any]]:
    try:
        db = _get_db()
        filters: dict[str, Any] = {}
        if product_slug:
            filters["product_slug"] = product_slug
        if status:
            filters["status"] = status
        if needs_ceo is not None:
            filters["needs_ceo"] = needs_ceo
        return db.select(
            "sav_cases",
            filters=filters or None,
            order_by="created_at",
            ascending=False,
            limit=limit,
        )
    except Exception as exc:
        logger.debug("list_sav_cases failed: %s", exc)
        return []


def approve_and_close(case_id: str, *, final_reply: str | None = None) -> dict[str, Any]:
    """CEO approved — mark replied (send via Composio optional later)."""
    db = _get_db()
    rows = db.select("sav_cases", filters={"id": case_id}, limit=1)
    if not rows:
        return {"success": False, "error": "Case introuvable"}
    reply = (final_reply or rows[0].get("draft_reply") or "").strip()
    db.update(
        "sav_cases",
        case_id,
        {"status": "replied", "draft_reply": reply, "needs_ceo": False},
    )
    try:
        from skills.skill_mem0 import remember

        remember(
            f"[SAV {rows[0].get('product_slug')}] Q: {rows[0].get('subject')} → R: {reply[:400]}",
            agent_id="secretary",
        )
    except Exception:
        pass
    return {"success": True, "status": "replied", "draft_reply": reply}


def ingest_recent_beta_feedback(*, days: int = 7, limit: int = 10) -> dict[str, Any]:
    """Create SAV cases from recent beta feedback not yet triaged."""
    db = _get_db()
    try:
        rows = db.select(
            "beta_feedback",
            order_by="created_at",
            ascending=False,
            limit=limit * 3,
        )
    except Exception as exc:
        return {"ingested": 0, "error": str(exc)}

    ingested = 0
    for fb in rows:
        if ingested >= limit:
            break
        meta_ref = f"beta:{fb.get('id')}"
        existing = db.select(
            "sav_cases",
            filters={"customer_ref": meta_ref},
            limit=1,
        )
        if existing:
            continue

        project_id = fb.get("project_id")
        slug = "app"
        if project_id:
            projects = db.select("projects", filters={"id": project_id}, limit=1)
            if projects:
                slug = (projects[0].get("slug") or projects[0].get("name") or "app").lower()
                slug = slug.replace(" ", "-")[:64]

        result = process_sav_case(
            SavCaseIn(
                product_slug=slug,
                subject=f"[Beta] {fb.get('type', 'feedback')}",
                body=str(fb.get("description") or fb.get("content") or "")[:4000],
                channel="beta",
                customer_ref=meta_ref,
            )
        )
        if result.get("success"):
            ingested += 1

    return {"ingested": ingested}
