"""Studio job and capability types."""

from __future__ import annotations

from typing import Literal

StudioProviderId = Literal["google", "runway", "openrouter", "elevenlabs"]
StudioCapability = Literal[
    "video_generate",
    "image_generate",
    "image_edit",
    "video_upscale",
    "remove_background",
    "tts",
]
StudioJobStatus = Literal["queued", "running", "succeeded", "failed", "cancelled"]
