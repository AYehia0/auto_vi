"""Abstract base for grounding strategies."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from PIL import Image


class GroundingError(Exception):
    """Raised when no strategy can locate the target."""


class GroundingStrategy(ABC):
    """Each strategy takes a screenshot + query and returns (x, y) center coords."""

    name: str = "base"

    @abstractmethod
    def locate(self, image: Image.Image, query: str, cfg: dict[str, Any]) -> tuple[int, int]:
        """Return (x, y) center pixel of the target, or raise GroundingError."""
