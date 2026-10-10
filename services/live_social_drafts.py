"""Two-step LinkedIn drafts for Nadia Live — never publish without a later confirm."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from services.input_sanitizer import sanitize_user_input
from services.live_cards_format import draft_card


@dataclass
class SocialDraft:
    id: str
    platform: str
    body: str
    created_at: str


_drafts: dict[str, SocialDraft] = {}
_last_id: str | None = None


def store_linkedin_draft(text: str) -> SocialDraft:
    clean = sanitize_user_input(text, max_length=2800, redact_pii_enabled=False).strip()
    draft = SocialDraft(
        id=uuid.uuid4().hex[:16],
        platform="linkedin",
        body=clean,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    _drafts[draft.id] = draft
    global _last_id
    _last_id = draft.id
    return draft


def get_draft(draft_id: str) -> SocialDraft | None:
    return _drafts.get(draft_id)


def latest_draft_id() -> str | None:
    return _last_id


def pop_draft(draft_id: str) -> SocialDraft | None:
    return _drafts.pop(draft_id, None)


def draft_linkedin_sofia(brief: str) -> str:
    """Sofia (content) + voix marque Anouk — brouillon seulement."""
    from agents.content_agent import ContentAgent
    from agents.content_agent_constants import PLATFORM_RULES
    from skills.skill_content_company import BRAND_VOICE_GUIDE, review_post_for_brand_voice

    clean = sanitize_user_input(brief, max_length=500, redact_pii_enabled=False).strip()
    prompt = (
        "Tu es Sofia Reyes, content ALNUA. Brouillon LinkedIn seulement, jamais publié.\n"
        f"Voix marque : {BRAND_VOICE_GUIDE}\n"
        f"{PLATFORM_RULES['linkedin']}\n"
        f"Brief : {clean}\n"
        "Français, 100-200 mots, texte brut, pas de JSON, 3-5 hashtags max."
    )
    try:
        raw = (ContentAgent()._complete(prompt, temperature=0.5, max_tokens=700) or "").strip()
    except Exception:
        return ""
    review = review_post_for_brand_voice(raw, "company")
    if raw and not review.get("ok"):
        raw = raw.replace("revolutionize", "").replace("disrupt", "").replace("synergy", "")
    return raw.strip()


def format_linkedin_draft(text: str) -> str:
    draft = store_linkedin_draft(text)
    return draft_card(
        kind="linkedin",
        title="Brouillon LinkedIn",
        body=draft.body,
        draft_id=draft.id,
        lead="Brouillon prêt — rien n'est publié. Clique Valider ou dis « publie ».",
    )


def publish_linkedin_draft(draft_id: str) -> dict[str, Any]:
    draft = get_draft(draft_id)
    if draft is None:
        return {"success": False, "message": "Aucun brouillon LinkedIn avec cet id."}
    from services.secretary_composio_oauth import is_connected
    from skills.skill_composio import composio_execute

    if not is_connected("linkedin"):
        return {
            "success": False,
            "message": "LinkedIn n'est pas connecté (Composio). Le brouillon reste à l'écran.",
        }
    result = composio_execute(
        "LINKEDIN_CREATE_LINKED_IN_POST",
        {"text": draft.body},
        agent_name="secretary_agent",
        user_id="alnua_coo",
    )
    if result.get("success"):
        pop_draft(draft_id)
        return {"success": True, "message": "Publié sur LinkedIn."}
    return {
        "success": False,
        "message": f"Publication refusée : {result.get('error') or 'erreur Composio'}",
    }


def reset_for_tests() -> None:
    global _last_id
    _drafts.clear()
    _last_id = None
