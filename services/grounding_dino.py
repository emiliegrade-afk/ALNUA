"""Grounding DINO open-vocabulary detection for brand element bboxes."""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import torch
from fastapi import HTTPException
from torchvision.ops import box_convert

from config.settings import get_settings
from services.brand_schemas import BoundingBox, BrandElement

logger = logging.getLogger(__name__)

DETECTION_CAPTION = "logo . text . icon . background . main element"
BOX_THRESHOLD = 0.35
TEXT_THRESHOLD = 0.25
SKIP_PHRASES = frozenset({"background"})
MAX_BOX_AREA_RATIO = 0.75

PHRASE_TYPE_MAP: dict[str, str] = {
    "logo": "combined",
    "text": "text",
    "icon": "symbol",
    "main element": "combined",
    "main": "combined",
    "element": "combined",
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _resolve_weights_path() -> Path:
    settings = get_settings()
    configured = Path(settings.grounding_dino_weights_path)
    if configured.is_absolute():
        return configured
    return _repo_root() / configured


def _resolve_config_path() -> Path:
    settings = get_settings()
    configured = Path(settings.grounding_dino_config_path)
    if configured.is_file():
        return configured

    try:
        import groundingdino  # noqa: PLC0415

        bundled = (
            Path(groundingdino.__file__).resolve().parent
            / "config"
            / "GroundingDINO_SwinT_OGC.py"
        )
        if bundled.is_file():
            return bundled
    except ImportError:
        pass

    return _repo_root() / configured


def _pick_device() -> str:
    settings = get_settings()
    requested = settings.grounding_dino_device.strip().lower()
    if requested in {"cpu", "cuda", "mps"}:
        if requested == "cuda" and not torch.cuda.is_available():
            logger.warning("grounding_dino_device=cuda unavailable, falling back to cpu")
            return "cpu"
        if requested == "mps" and not torch.backends.mps.is_available():
            logger.warning("grounding_dino_device=mps unavailable, falling back to cpu")
            return "cpu"
        return requested
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


@lru_cache(maxsize=1)
def _load_detection_model() -> tuple[Any, str]:
    try:
        from groundingdino.util.inference import load_model  # noqa: PLC0415
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Grounding DINO non installé. "
                "pip install torch torchvision "
                "git+https://github.com/IDEA-Research/GroundingDINO.git"
            ),
        ) from exc

    config_path = _resolve_config_path()
    weights_path = _resolve_weights_path()
    if not config_path.is_file():
        raise HTTPException(
            status_code=503,
            detail=f"Config Grounding DINO introuvable: {config_path}",
        )
    if not weights_path.is_file():
        raise HTTPException(
            status_code=503,
            detail=(
                f"Poids Grounding DINO introuvables: {weights_path}. "
                "Téléchargez groundingdino_swint_ogc.pth dans models/groundingdino/."
            ),
        )

    device = _pick_device()
    logger.info(
        "Loading Grounding DINO (device=%s, config=%s, weights=%s)",
        device,
        config_path,
        weights_path,
    )
    model = load_model(str(config_path), str(weights_path), device=device)
    return model, device


def _cxcywh_to_bbox(box: torch.Tensor) -> BoundingBox:
    """Convert DINO cxcywh [0,1] to pipeline bbox scale 0-1000."""
    xyxy = box_convert(box.unsqueeze(0), in_fmt="cxcywh", out_fmt="xyxy").squeeze(0)
    x1, y1, x2, y2 = (xyxy * 1000).tolist()
    return BoundingBox(
        x1=int(round(max(0, min(1000, x1)))),
        y1=int(round(max(0, min(1000, y1)))),
        x2=int(round(max(0, min(1000, x2)))),
        y2=int(round(max(0, min(1000, y2)))),
    )


def _normalize_phrase(phrase: str) -> str:
    return " ".join(phrase.lower().strip().split())


def _phrase_to_type(phrase: str) -> str:
    normalized = _normalize_phrase(phrase)
    if normalized in PHRASE_TYPE_MAP:
        return PHRASE_TYPE_MAP[normalized]
    for key, element_type in PHRASE_TYPE_MAP.items():
        if key in normalized:
            return element_type
    return "combined"


def _box_area_ratio(bbox: BoundingBox) -> float:
    w = max(0, bbox.x2 - bbox.x1) / 1000
    h = max(0, bbox.y2 - bbox.y1) / 1000
    return w * h


def _infer_components(elements: list[BrandElement]) -> dict[str, bool]:
    labels = " ".join(element.label.lower() for element in elements)
    types = {element.type for element in elements}
    return {
        "has_symbol": "symbol" in types or "icon" in labels,
        "has_wordmark": "text" in types or "wordmark" in labels,
        "has_tagline": "tagline" in labels,
    }


def detect_brand_elements(image_path: str) -> list[BrandElement]:
    """Run Grounding DINO on a prepared brand image and return BrandElements."""
    path = Path(image_path)
    if not path.is_file():
        raise HTTPException(status_code=404, detail=f"Image introuvable: {image_path}")

    try:
        from groundingdino.util.inference import load_image, predict  # noqa: PLC0415
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail="Grounding DINO non installé",
        ) from exc

    model, device = _load_detection_model()
    _, image_tensor = load_image(str(path))

    boxes, logits, phrases = predict(
        model=model,
        image=image_tensor,
        caption=DETECTION_CAPTION,
        box_threshold=BOX_THRESHOLD,
        text_threshold=TEXT_THRESHOLD,
        device=device,
    )

    detections: list[tuple[float, BrandElement]] = []
    label_counts: dict[str, int] = {}

    for box, logit, phrase in zip(boxes, logits, phrases, strict=False):
        normalized_phrase = _normalize_phrase(phrase)
        if not normalized_phrase or normalized_phrase in SKIP_PHRASES:
            continue

        bbox = _cxcywh_to_bbox(box)
        if bbox.x2 <= bbox.x1 or bbox.y2 <= bbox.y1:
            continue
        if _box_area_ratio(bbox) > MAX_BOX_AREA_RATIO:
            continue

        base_label = normalized_phrase.replace(" ", "_")
        label_counts[base_label] = label_counts.get(base_label, 0) + 1
        suffix = f"_{label_counts[base_label]}" if label_counts[base_label] > 1 else ""
        label = f"{base_label}{suffix}"

        element = BrandElement(
            label=label,
            type=_phrase_to_type(normalized_phrase),
            bbox=bbox,
            description=f"Detected {normalized_phrase} (confidence {float(logit):.2f})",
        )
        detections.append((float(logit), element))

    detections.sort(key=lambda item: item[0], reverse=True)
    return [element for _, element in detections]


def merge_components(
    llm_components: dict[str, bool] | None,
    elements: list[BrandElement],
) -> dict[str, bool]:
    """Keep LLM component flags when present, otherwise infer from detections."""
    inferred = _infer_components(elements)
    if not isinstance(llm_components, dict):
        return inferred
    return {
        "has_symbol": bool(llm_components.get("has_symbol", inferred["has_symbol"])),
        "has_wordmark": bool(llm_components.get("has_wordmark", inferred["has_wordmark"])),
        "has_tagline": bool(llm_components.get("has_tagline", inferred["has_tagline"])),
    }
