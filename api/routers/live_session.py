"""Nadia Live — voice session endpoints (DEC-038, SPEC_JARVIS_LIVE Lots 3-4)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from api.route_common import *  # noqa: F403

router = APIRouter(tags=["live"])


class LiveSessionCreate(BaseModel):
    persona: Literal["nadia", "aria"] = "nadia"


class LiveSessionEnd(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=64)
    seconds: float = Field(..., ge=0, le=86_400)


@router.post("/live/session")
def live_session_create(body: LiveSessionCreate) -> dict[str, Any]:
    """Mint a short-lived OpenAI Realtime secret. The real API key never leaves the Hub."""
    from services.live_session import LiveSessionError, mint_client_secret
    from services.rate_limiter import ASSISTANT_LIMIT, assistant_limiter

    if not assistant_limiter.is_allowed("live:session", ASSISTANT_LIMIT):
        raise HTTPException(status_code=429, detail="Trop de sessions — pause 1 minute.")
    try:
        return mint_client_secret(body.persona)
    except LiveSessionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.post("/live/session/end")
def live_session_end(body: LiveSessionEnd) -> dict[str, int]:
    """The browser reports how long a session ran; the Hub caps it by the wall clock."""
    from services.live_session import end_session, usage_snapshot

    if not end_session(body.session_id, body.seconds):
        raise HTTPException(status_code=404, detail="Session inconnue ou déjà clôturée.")
    return usage_snapshot()


@router.get("/live/usage")
def live_usage() -> dict[str, int]:
    """Voice minutes used today versus LIVE_VOICE_MAX_MINUTES_PER_DAY."""
    from services.live_session import usage_snapshot

    return usage_snapshot()


@router.get("/live/access")
def live_access() -> dict[str, Any]:
    """Internet + Gmail/Calendar/Discord/Instagram — no secrets in the payload."""
    from services.live_access import probe_access

    return probe_access()


@router.post("/live/connect/{app_name}")
def live_connect(app_name: str) -> dict[str, str]:
    """OAuth link for a CEO app Nadia is allowed to request from Live."""
    from services.live_access import CONNECTABLE_APPS
    from services.secretary_composio import get_oauth_link_for_ceo, split_oauth_reply

    slug = app_name.strip().lower()
    if slug not in CONNECTABLE_APPS:
        raise HTTPException(status_code=400, detail="Cette app ne se connecte pas depuis Live.")
    raw = get_oauth_link_for_ceo(slug)
    url, hint = split_oauth_reply(raw)
    if slug == "instagram" and not hint:
        hint = (
            "Compte Instagram Professionnel lié à une Page Facebook "
            "(Meta refuse un compte perso)."
        )
    if not url:
        extra = (
            " Compte Instagram Professionnel + Page Facebook requis. "
            "Ou dis « ouvre Instagram » pour ouvrir le site sur ce PC."
            if slug == "instagram"
            else ""
        )
        raise HTTPException(
            status_code=409,
            detail=(hint or "Lien OAuth indisponible — réessaie dans un instant.") + extra,
        )
    return {"app": slug, "oauth_url": url, "hint": hint}


class LiveConfirm(BaseModel):
    kind: Literal["linkedin", "email", "pc_input"]
    draft_id: str = Field(..., min_length=1, max_length=64)


@router.post("/live/confirm")
def live_confirm(body: LiveConfirm) -> dict[str, str]:
    """Publish/send a draft already shown on screen. Never creates a new post."""
    if body.kind == "email":
        from services.secretary_drafts import confirm_and_send

        out = confirm_and_send(body.draft_id)
    elif body.kind == "pc_input":
        from services.live_pc_input import execute_input

        out = execute_input(body.draft_id)
    else:
        from services.live_social_drafts import publish_linkedin_draft

        out = publish_linkedin_draft(body.draft_id)
    message = str(out.get("message") or "Action impossible.")
    if not out.get("success"):
        raise HTTPException(status_code=409, detail=message)
    return {"kind": body.kind, "message": message}


@router.get("/live/media/{name}")
def live_media(name: str) -> FileResponse:
    """Serve a generated Live PNG. Name is a 32-hex stem — no path traversal."""
    from services.live_media import resolve_media

    path = resolve_media(name)
    if path is None:
        raise HTTPException(status_code=404, detail="Image introuvable.")
    return FileResponse(path, media_type="image/png")
