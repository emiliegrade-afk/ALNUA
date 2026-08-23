"""Nadia weather tool — wttr.in, no LLM, no API key (Phase 47 Lot 3)."""

from __future__ import annotations

import logging
import re
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)

DEFAULT_PLACE = "Paris"
_MAX_PLACE = 80
_WTTR_TIMEOUT_S = 8.0
_SAFE_PLACE = re.compile(r"^[A-Za-zÀ-ÿ0-9][A-Za-zÀ-ÿ0-9 ,.'\-]{0,78}$")
_TRAIL = re.compile(
    r"\s+(demain|aujourd['’]?hui|ce soir|maintenant|stp|"
    r"s['’]il te pla[iî]t)\s*$",
    re.I,
)
_PLACE_PATTERNS = (
    r"quel\s+temps(?:\s+(?:fait-il|fait il|il fait))?\s+"
    r"(?:à|a|de|pour|in|at)\s+(.+)$",
    r"(?:m[ée]t[ée]o|weather|temps|temp[ée]rature|pleut)\s+"
    r"(?:à|a|de|pour|in|at|for)\s+(.+)$",
    r"(?:m[ée]t[ée]o|weather)\s+(.+)$",
)


def extract_weather_place(text: str) -> str:
    """City from NL; default Paris. Rejects unsafe path fragments."""
    raw = (text or "").strip()
    candidate = ""
    for pattern in _PLACE_PATTERNS:
        match = re.search(pattern, raw, flags=re.I)
        if match:
            candidate = match.group(1).strip(" :.-")
            break
    candidate = _TRAIL.sub("", candidate).strip(" :.-")
    if not candidate:
        return DEFAULT_PLACE
    if len(candidate) > _MAX_PLACE:
        candidate = candidate[:_MAX_PLACE].rstrip()
    if not _SAFE_PLACE.match(candidate):
        return DEFAULT_PLACE
    return candidate


def _desc(current: dict) -> str:
    fr = current.get("lang_fr") or []
    if fr and isinstance(fr[0], dict) and fr[0].get("value"):
        return str(fr[0]["value"]).strip()
    en = current.get("weatherDesc") or []
    if en and isinstance(en[0], dict) and en[0].get("value"):
        return str(en[0]["value"]).strip()
    return "conditions inconnues"


def format_weather_facts(place: str, payload: dict) -> str:
    """Gold-style facts line — numbers stay in text, not in the overlay."""
    rows = payload.get("current_condition") or []
    if not rows or not isinstance(rows[0], dict):
        return f"{place} — météo indisponible pour l'instant."
    current = rows[0]
    temp = str(current.get("temp_C") or "?").strip()
    desc = _desc(current).lower()
    try:
        precip = float(current.get("precipMM") or 0)
    except (TypeError, ValueError):
        precip = 0.0
    rain = "pluie possible" if precip >= 0.3 or "pluie" in desc or "rain" in desc else "pas de pluie"
    return f"{place} — {temp} °C, {desc}, {rain}."


def fetch_weather(place: str) -> str:
    """HTTP wttr.in JSON. Never raises to the caller."""
    raw = (place or "").strip()
    looks_like_sentence = any(
        m in raw.lower() for m in ("météo", "meteo", "temps", "weather", "pleut")
    )
    if looks_like_sentence or not _SAFE_PLACE.match(raw):
        city = extract_weather_place(raw)
    else:
        city = raw
    if not city:
        city = DEFAULT_PLACE
    url = f"https://wttr.in/{quote(city)}?format=j1&lang=fr"
    try:
        with httpx.Client(timeout=_WTTR_TIMEOUT_S, follow_redirects=True) as client:
            resp = client.get(url, headers={"User-Agent": "ALNUA-Hub/Nadia"})
            resp.raise_for_status()
            data = resp.json()
        if not isinstance(data, dict):
            raise ValueError("wttr payload")
        return format_weather_facts(city, data)
    except Exception:
        logger.warning("wttr.in failed for %s", city, exc_info=True)
        return (
            f"{city} — je n'ai pas pu joindre la météo (réseau).\n"
            "Réessaie dans un instant."
        )


def weather_reply(instruction: str) -> str:
    from services.input_sanitizer import sanitize_user_input

    clean = sanitize_user_input(
        instruction or "", max_length=400, redact_pii_enabled=False
    )
    place = extract_weather_place(clean)
    return fetch_weather(place)
