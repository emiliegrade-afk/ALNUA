"""Base class for Studio provider adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class StudioProvider(ABC):
    provider_id: str

    @abstractmethod
    def is_configured(self) -> bool:
        """Return True when API credentials are present."""

    @abstractmethod
    async def run_job(self, job: dict[str, Any]) -> dict[str, Any]:
        """Execute job; return {artifact_url, metadata} or raise."""
