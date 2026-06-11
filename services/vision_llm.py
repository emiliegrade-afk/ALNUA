"""GPT-4V brand metadata via OpenRouter; bboxes from Grounding DINO."""

from __future__ import annotations

import base64
import io
import json
import logging
from pathlib import Path
from typing import Any

import httpx
from fastapi import HTTPException
from PIL import Image
from pydantic import ValidationError

from agents.base import parse_json_response
from config.settings import get_settings
from services.brand_schemas import BrandAnalysis
from services.grounding_dino import detect_brand_elements, merge_components

logger = logging.getLogger(__name__)

MAX_LLM_DIMENSION = 2048
VISION_MODEL = "openai/gpt-4o"

SYSTEM_PROMPT = (
    "Tu es un expert en brand design. Analyse cette image et retourne "
    "UNIQUEMENT un JSON valide sans markdown."
)

USER_PROMPT = (
    "Analyse cette identité visuelle (planche brand, logo sheet ou guideline). "
    "Retourne un JSON avec : "
    "{brand_name, tagline, style, mood[], typography_style, "
    "colors:[{hex, name, role}], usage_notes, "
    "components:{has_symbol, has_wordmark, has_tagline}}.\n\n"
    "Ne retourne PAS de bounding boxes ni de liste elements — "
    "la localisation des composants est gérée séparément."
)

RETRY_PROMPT_TEMPLATE = (
    "Le JSON précédent est invalide. Corrige ce JSON : {error}\n\n"
    "JSON à corriger :\n{json_payload}\n\n"
    "Retourne UNIQUEMENT le JSON corrigé, sans markdown."
)


def _resize_for_llm(image: Image.Image) -> Image.Image:
    width, height = image.size
    if max(width, height) <= MAX_LLM_DIMENSION:
        return image
    if width >= height:
        new_width = MAX_LLM_DIMENSION
        new_height = int(height * MAX_LLM_DIMENSION / width)
    else:
        new_height = MAX_LLM_DIMENSION
        new_width = int(width * MAX_LLM_DIMENSION / height)
    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)


def _to_data_url(image: Image.Image) -> str:
    buffer = io.BytesIO()
    if image.mode in ("RGBA", "LA", "P"):
        image.save(buffer, format="PNG")
        mime = "image/png"
    else:
        rgb = image.convert("RGB")
        rgb.save(buffer, format="JPEG", quality=90)
        mime = "image/jpeg"
    encoded = base64.standard_b64encode(buffer.getvalue()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _normalize_llm_payload(data: dict[str, Any]) -> dict[str, Any]:
    """Tag LLM colors with source=llm before Pydantic validation."""
    colors = data.get("colors", [])
    normalized_colors: list[dict[str, Any]] = []
    for color in colors:
        if not isinstance(color, dict):
            continue
        entry = dict(color)
        entry["source"] = "llm"
        normalized_colors.append(entry)
    data["colors"] = normalized_colors

    components = data.get("components")
    if not isinstance(components, dict):
        data["components"] = {
            "has_symbol": False,
            "has_wordmark": False,
            "has_tagline": False,
        }

    return data


def _merge_metadata_with_detections(
    metadata: dict[str, Any],
    image_path: str,
) -> BrandAnalysis:
    """Combine GPT-4V brand metadata with Grounding DINO element bboxes."""
    elements = detect_brand_elements(image_path)
    if not elements:
        raise HTTPException(
            status_code=502,
            detail="Aucun élément détecté par Grounding DINO sur cette image",
        )

    payload = dict(metadata)
    payload["elements"] = [element.model_dump() for element in elements]
    payload["components"] = merge_components(
        payload.get("components") if isinstance(payload.get("components"), dict) else None,
        elements,
    )
    return BrandAnalysis.model_validate(_normalize_llm_payload(payload))


def _call_openrouter(
    *,
    settings: Any,
    messages: list[dict[str, Any]],
) -> str:
    payload = {
        "model": VISION_MODEL,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 4096,
    }
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://alnua-hub.local",
        "X-Title": "ALNUA Hub Brand Kit",
    }

    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                f"{settings.openrouter_base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as exc:
        logger.exception("OpenRouter vision API error")
        raise HTTPException(
            status_code=502,
            detail=f"Erreur OpenRouter: {exc.response.text[:500]}",
        ) from exc
    except httpx.RequestError as exc:
        logger.exception("OpenRouter request failed")
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise HTTPException(
            status_code=502,
            detail="Réponse OpenRouter inattendue",
        ) from exc


def prepare_brand_image(image_path: str) -> tuple[str, tuple[int, int]]:
    """Resize to MAX_LLM_DIMENSION — same pixels for DINO bbox + OpenCV crop."""
    path = Path(image_path)
    if not path.is_file():
        raise HTTPException(status_code=404, detail=f"Image introuvable: {image_path}")

    with Image.open(path) as img:
        resized = _resize_for_llm(img)
        width, height = resized.size
        suffix = path.suffix.lower()
        if suffix in (".jpg", ".jpeg"):
            resized.convert("RGB").save(path, format="JPEG", quality=92)
        else:
            resized.save(path, format="PNG")

    return str(path), (width, height)


def analyze_brand_image(image_path: str) -> BrandAnalysis:
    """GPT-4V metadata + Grounding DINO bboxes on a prepared image."""
    settings = get_settings()
    if not settings.openrouter_api_key.strip():
        raise HTTPException(status_code=503, detail="OPENROUTER_API_KEY manquante")

    path = Path(image_path)
    if not path.is_file():
        raise HTTPException(status_code=404, detail=f"Image introuvable: {image_path}")

    with Image.open(path) as img:
        data_url = _to_data_url(img)

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": USER_PROMPT},
                {"type": "image_url", "image_url": {"url": data_url}},
            ],
        },
    ]

    content = _call_openrouter(settings=settings, messages=messages)

    try:
        raw_dict = parse_json_response(content)
    except json.JSONDecodeError as exc:
        logger.exception("Failed to parse LLM JSON")
        raise HTTPException(
            status_code=502,
            detail="Réponse LLM invalide (JSON non parsable)",
        ) from exc

    try:
        return _merge_metadata_with_detections(raw_dict, image_path)
    except ValidationError as first_error:
        logger.warning("BrandAnalysis validation failed, retrying once: %s", first_error)
        retry_prompt = RETRY_PROMPT_TEMPLATE.format(
            error=first_error,
            json_payload=json.dumps(raw_dict, ensure_ascii=False),
        )
        retry_messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": retry_prompt},
        ]
        retry_content = _call_openrouter(settings=settings, messages=retry_messages)

        try:
            retry_dict = parse_json_response(retry_content)
        except json.JSONDecodeError as exc:
            logger.exception("Retry LLM JSON parse failed")
            raise HTTPException(
                status_code=502,
                detail="Réponse LLM invalide après retry (JSON non parsable)",
            ) from exc

        try:
            return _merge_metadata_with_detections(retry_dict, image_path)
        except ValidationError as exc:
            logger.exception("BrandAnalysis validation failed after retry")
            raise HTTPException(
                status_code=502,
                detail=f"Analyse LLM invalide après retry: {exc}",
            ) from exc
