"""Strategy registry — tries configured strategies in order."""

from __future__ import annotations

import logging
from typing import Any

from PIL import Image

from auto_vi.grounding.base import GroundingError, GroundingStrategy
from auto_vi.grounding.ocr import OCRStrategy

log = logging.getLogger(__name__)

_STRATEGIES: dict[str, GroundingStrategy] = {
    "ocr": OCRStrategy(),
}


def register(strategy: GroundingStrategy) -> None:
    _STRATEGIES[strategy.name] = strategy


def locate(image: Image.Image, query: str, cfg: dict[str, Any]) -> tuple[int, int]:
    """Try each configured strategy in order; return first successful (x, y)."""
    strategies = cfg["grounding"]["strategies"]

    for name in strategies:
        strategy = _STRATEGIES.get(name)
        if not strategy:
            log.warning("Unknown grounding strategy: %s", name)
            continue
        try:
            x, y = strategy.locate(image, query, cfg)
            if x >= 0 and y >= 0:
                log.info("Grounded '%s' via %s → (%d, %d)", query, name, x, y)
                return x, y
        except Exception:
            log.debug("Strategy %s failed for '%s'", name, query, exc_info=True)

    raise GroundingError(f"All strategies failed for '{query}'")
