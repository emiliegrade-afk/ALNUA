"""Nadia Live images — generate via OpenRouter, or fetch Wikimedia with credit."""

from __future__ import annotations

import base64
import json
import logging
import re
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import quote
from urllib.request import Request, urlopen

from services.input_sanitizer import sanitize_user_input
from services.live_cards_format import image_card, list_card

logger = logging.getLogger(__name__)

IMAGES_API = "https://openrouter.ai/api/v1/images"
WIKI_API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "ALNUA-Hub/1.0 (live-media; https://alnua.local)"
HTTP_TIMEOUT = 45
GEN_TIMEOUT = 90

_GEN_RE = re.compile(
    r"^(?:génère|genere|génère-moi|genere-moi|crée|cree|fais)\s+"
    r"(?:une?\s+)?(?:image|illustration|visuel)\s*(?:de|d'|du|des|:)?\s*(.+)$",
    re.IGNORECASE,
)
_STOCK_RE = re.compile(
    r"(?:image|photo|visuel).*(?:libre|wikimedia|presse)|"
    r"(?:trouve|cherche).*(?:image|photo)",
    re.IGNORECASE,
)


def artifacts_dir() -> Path:
    from config.paths import data_dir

    folder = data_dir("live_media")
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def wants_generated_image(instruction: str) -> bool:
    lower = instruction.lower()
    if _STOCK_RE.search(instruction):
        return False
    return bool(_GEN_RE.search(instruction)) or (
        "génère" in lower or "genere" in lower
    ) and ("image" in lower or "illustration" in lower or "visuel" in lower)


def wants_stock_image(instruction: str) -> bool:
    return bool(_STOCK_RE.search(instruction))


def handle_image_request(instruction: str) -> str:
    topic = _topic(instruction)
    if wants_stock_image(instruction):
        return find_stock_images(topic)
    if wants_generated_image(instruction):
        return generate_image(topic)
    return find_stock_images(topic)


def generate_image(prompt: str) -> str:
    clean = sanitize_user_input(prompt, max_length=400, redact_pii_enabled=False).strip()
    if not clean:
        return "Dis-moi ce que l'image doit montrer."
    from config.settings import get_settings

    settings = get_settings()
    key = (getattr(settings, "openrouter_api_key", "") or "").strip()
    if not key:
        return "OPENROUTER_API_KEY manque — je ne peux pas générer d'image."
    model = str(getattr(settings, "live_image_model", "") or "google/gemini-2.5-flash-image")
    try:
        raw = _call_openrouter(key, model, clean)
        name = f"{uuid.uuid4().hex}.png"
        path = artifacts_dir() / name
        path.write_bytes(raw)
    except Exception as exc:
        logger.warning("live image generate failed: %s", type(exc).__name__)
        return f"Génération image échouée ({type(exc).__name__}). Réessaie avec un prompt plus court."
    return image_card(
        title=clean[:80],
        src=f"/api/hub/live/media/{name}",
        credit=f"Généré · {model}",
        lead=f"Image générée : {clean[:80]}",
    )


def find_stock_images(query: str) -> str:
    topic = sanitize_user_input(query, max_length=120, redact_pii_enabled=False).strip()
    if not topic:
        return "Dis-moi le sujet de la photo (Wikimedia, crédit affiché)."
    hits = _wiki_search(topic)
    if not hits:
        return (
            f"Aucune image Wikimedia pour « {topic} ». "
            "Je n'invente pas de visuel — reformule ou demande une génération."
        )
    items = [f"{h['title']} — {h['credit']}" for h in hits]
    first = hits[0]
    card = image_card(
        title=first["title"],
        src=first["src"],
        credit=first["credit"],
        href=first["href"],
        lead=f"Photo libre : {topic}",
    )
    return card + "\n\n" + list_card("Autres sources Wikimedia", items[1:], lead="")


def resolve_media(name: str) -> Path | None:
    if not re.fullmatch(r"[a-f0-9]{32}\.png", name or ""):
        return None
    path = (artifacts_dir() / name).resolve()
    root = artifacts_dir().resolve()
    if not path.is_relative_to(root) or not path.is_file():
        return None
    return path


def _topic(instruction: str) -> str:
    match = _GEN_RE.search(instruction.strip())
    if match:
        return match.group(1).strip(" :.-")
    cleaned = re.sub(
        r"(?:trouve|cherche|une?|image|photo|visuel|libre|de droits|wikimedia|presse)",
        " ",
        instruction,
        flags=re.IGNORECASE,
    )
    return re.sub(r"\s+", " ", cleaned).strip(" :.-") or instruction[:80]


def _call_openrouter(api_key: str, model: str, prompt: str) -> bytes:
    body = json.dumps(
        {
            "model": model,
            "prompt": prompt,
            "aspect_ratio": "1:1",
            "output_format": "png",
        }
    ).encode()
    req = Request(
        IMAGES_API,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://alnua.local",
            "X-Title": "ALNUA Nadia Live",
        },
        method="POST",
    )
    with urlopen(req, timeout=GEN_TIMEOUT) as resp:  # noqa: S310 — fixed OpenRouter URL
        payload = json.loads(resp.read().decode("utf-8"))
    data = payload.get("data") or []
    if not data or not isinstance(data[0], dict):
        raise RuntimeError("empty_image")
    item = data[0]
    b64 = item.get("b64_json") or item.get("b64")
    if isinstance(item.get("url"), str) and str(item["url"]).startswith("data:"):
        b64 = str(item["url"]).split(",", 1)[-1]
    if b64:
        return base64.b64decode(b64)
    url = item.get("url")
    if isinstance(url, str) and url.startswith("https://"):
        with urlopen(url, timeout=HTTP_TIMEOUT) as img:  # noqa: S310 — https image URL
            return img.read()
    raise RuntimeError("no_image_bytes")


def _wiki_search(topic: str) -> list[dict[str, str]]:
    url = (
        f"{WIKI_API}?action=query&generator=search&gsrsearch={quote(topic)}"
        "&gsrnamespace=6&gsrlimit=4&prop=imageinfo"
        "&iiprop=url|extmetadata|mime&iiurlwidth=640&format=json"
    )
    req = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(req, timeout=HTTP_TIMEOUT) as resp:  # noqa: S310 — Wikimedia API
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        logger.warning("wikimedia search failed: %s", type(exc).__name__)
        return []
    pages = ((payload.get("query") or {}).get("pages") or {})
    out: list[dict[str, str]] = []
    for page in pages.values() if isinstance(pages, dict) else []:
        if not isinstance(page, dict):
            continue
        info = (page.get("imageinfo") or [{}])[0]
        if not isinstance(info, dict):
            continue
        mime = str(info.get("mime") or "")
        if not mime.startswith("image/"):
            continue
        src = str(info.get("thumburl") or info.get("url") or "")
        if not src.startswith("https://"):
            continue
        meta = info.get("extmetadata") if isinstance(info.get("extmetadata"), dict) else {}
        artist = _meta_value(meta, "Artist") or "Wikimedia Commons"
        license_name = _meta_value(meta, "LicenseShortName") or "licence ouverte"
        title = str(page.get("title") or topic).replace("File:", "")[:80]
        href = str(info.get("descriptionurl") or src)
        out.append(
            {
                "title": title,
                "src": src,
                "href": href if href.startswith("https://") else src,
                "credit": f"{artist} · {license_name}",
            }
        )
    return out[:4]


def _meta_value(meta: dict[str, Any], key: str) -> str:
    raw = meta.get(key)
    if isinstance(raw, dict):
        return re.sub(r"<[^>]+>", "", str(raw.get("value") or "")).strip()[:80]
    return ""
