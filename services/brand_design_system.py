"""ALNUA transversal design system + brand voice (Phase 35 / Vague D).

Merges visual tokens (kit palette or Hub defaults) with content_company voice
guide. No silent stubs — review returns explicit flags.
"""
from __future__ import annotations

import logging
from typing import Any

from skills.skill_content_company import BRAND_VOICE_GUIDE, review_post_for_brand_voice

logger = logging.getLogger(__name__)

# Hub UI defaults (globals.css) — used when no brand kit palette is available.
DEFAULT_COLOR_TOKENS: list[dict[str, str]] = [
    {"token": "copper", "hex": "#C08A72", "role": "accent"},
    {"token": "copper-light", "hex": "#D9A88F", "role": "accent_light"},
    {"token": "obsidian", "hex": "#0F1215", "role": "bg"},
    {"token": "ivory", "hex": "#E8E2DA", "role": "text"},
    {"token": "titanium", "hex": "#8E949C", "role": "muted"},
]

DEFAULT_TYPE_SCALE: dict[str, str] = {
    "display": "Syne / title — headlines",
    "body": "DM Sans / UI body",
    "label": "uppercase tracked labels (dept chrome)",
    "mono": "optional code / IDs",
}

DEFAULT_GUIDELINES: list[str] = [
    "Copper accent on dark obsidian — never purple SaaS defaults.",
    "Brand name visible at hero level on branded surfaces.",
    "No corporate slop; build-in-public tone (see voice.forbidden).",
    "Visual kits from /brand feed color tokens when a kit exists.",
]


def _colors_from_kit_analysis(analysis: dict[str, Any] | None) -> list[dict[str, str]]:
    if not analysis:
        return []
    colors = analysis.get("colors") or analysis.get("palette") or []
    out: list[dict[str, str]] = []
    for i, c in enumerate(colors):
        if not isinstance(c, dict):
            continue
        hex_v = str(c.get("hex") or c.get("value") or "").strip()
        if not hex_v:
            continue
        out.append(
            {
                "token": str(c.get("role") or c.get("name") or f"kit_{i}"),
                "hex": hex_v if hex_v.startswith("#") else f"#{hex_v}",
                "role": str(c.get("role") or "brand"),
            }
        )
    return out


def _latest_kit_analysis() -> tuple[dict[str, Any] | None, str | None]:
    try:
        from database.supabase_client import get_supabase

        rows = get_supabase().select(
            "brand_kits",
            order_by="created_at",
            ascending=False,
            limit=1,
        )
        if not rows:
            return None, None
        row = rows[0]
        analysis = row.get("analysis")
        if isinstance(analysis, str):
            import json

            analysis = json.loads(analysis)
        if not isinstance(analysis, dict):
            analysis = None
        return analysis, str(row.get("id") or "")
    except Exception as exc:
        logger.debug("brand kit load skipped: %s", exc)
        return None, None


def get_design_system() -> dict[str, Any]:
    """Merged tokens + voice + guidelines for agents and Brand Center."""
    analysis, kit_id = _latest_kit_analysis()
    kit_colors = _colors_from_kit_analysis(analysis)
    typo_from_kit = ""
    if analysis:
        typo_from_kit = str(
            analysis.get("typography_style") or analysis.get("typography") or ""
        ).strip()

    color_tokens = kit_colors or list(DEFAULT_COLOR_TOKENS)
    type_scale = dict(DEFAULT_TYPE_SCALE)
    if typo_from_kit:
        type_scale["kit_style"] = typo_from_kit

    return {
        "ok": True,
        "source": {
            "colors": "brand_kit" if kit_colors else "hub_defaults",
            "kit_id": kit_id,
            "voice": "content_company.BRAND_VOICE_GUIDE",
        },
        "color_tokens": color_tokens,
        "typography": type_scale,
        "voice": dict(BRAND_VOICE_GUIDE),
        "guidelines": list(DEFAULT_GUIDELINES),
        "reviewers": ["brand", "content_company"],
    }


def review_brand_coherence(
    text: str,
    *,
    sector: str = "",
    department: str = "",
) -> dict[str, Any]:
    """Structural brand review — voice keywords + light guideline checks."""
    from services.input_sanitizer import sanitize_user_input

    cleaned = sanitize_user_input(text or "", max_length=8000, redact_pii_enabled=False)
    voice = review_post_for_brand_voice(cleaned, sector=sector or department)
    flags = list(voice.get("flags") or [])

    # Extra coherence: empty / too thin for a brandable surface
    if len(cleaned.strip()) < 12:
        flags.append("too_thin:content_under_12_chars")

    lower = cleaned.lower()
    # Only branded go-to-market surfaces — sector content may omit the company name.
    if "alnua" not in lower and department in ("marketing", "brand", "comms"):
        flags.append("missing_brand_mention:alnua")

    ok = len(flags) == 0
    return {
        "ok": ok,
        "reviewer": "brand",
        "flags": flags,
        "voice_ok": bool(voice.get("ok")),
        "department": department,
        "sector": sector,
        "preview": cleaned[:200],
        "recommendation": "approve" if ok else "revise",
    }


def artifact_text(artifact: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("title", "name", "body", "description", "content", "caption"):
        val = artifact.get(key)
        if isinstance(val, str) and val.strip():
            parts.append(val.strip())
    return "\n".join(parts)
