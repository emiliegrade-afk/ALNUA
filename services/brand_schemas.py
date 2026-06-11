"""Pydantic models for Brand Kit analysis pipeline."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class BoundingBox(BaseModel):
    x1: int = Field(ge=0, le=1000)
    y1: int = Field(ge=0, le=1000)
    x2: int = Field(ge=0, le=1000)
    y2: int = Field(ge=0, le=1000)


class BrandElement(BaseModel):
    label: str
    type: str
    bbox: BoundingBox
    description: str


class ColorInfo(BaseModel):
    hex: str
    name: str
    role: str
    source: Literal["llm", "kmeans", "merged"]

    @field_validator("hex")
    @classmethod
    def normalize_hex(cls, value: str) -> str:
        cleaned = value.strip().upper()
        if not cleaned.startswith("#"):
            cleaned = f"#{cleaned}"
        return cleaned


class BrandAnalysis(BaseModel):
    brand_name: str
    tagline: str | None = None
    style: str
    mood: list[str]
    typography_style: str
    colors: list[ColorInfo]
    elements: list[BrandElement]
    usage_notes: str
    components: dict[str, bool]
