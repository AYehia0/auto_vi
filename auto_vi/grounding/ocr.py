"""OCR-based grounding strategy using EasyOCR.

Scans the screenshot for text, matches against the query,
and returns the center of the icon above the matched label.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
from PIL import Image

from auto_vi.grounding.base import GroundingError, GroundingStrategy

log = logging.getLogger(__name__)

_reader = None


def _get_reader(languages: list[str]):
    global _reader
    if _reader is None:
        import easyocr
        import torch
        use_gpu = torch.cuda.is_available()
        _reader = easyocr.Reader(languages, gpu=use_gpu)
        log.info("EasyOCR initialized (%s)", "GPU" if use_gpu else "CPU")
    return _reader


class OCRStrategy(GroundingStrategy):
    name = "ocr"

    def locate(self, image: Image.Image, query: str, cfg: dict[str, Any]) -> tuple[int, int]:
        ocfg = cfg["grounding"]["ocr"]
        reader = _get_reader(ocfg.get("languages", ["en"]))
        results = reader.readtext(np.array(image))

        query_lower = query.lower()
        log.debug("OCR detected %d text regions:", len(results))
        for bbox, text, conf in results:
            log.debug("  '%s' (conf=%.2f)", text.strip(), conf)

        for bbox, text, conf in results:
            if text.strip().lower() == query_lower and conf >= ocfg.get("confidence_min", 0.3):
                cx = int(sum(p[0] for p in bbox) / 4)
                cy = int(sum(p[1] for p in bbox) / 4)
                # offset upward to hit the icon above the label
                cy -= ocfg.get("icon_offset_y", 30)
                log.info("OCR found '%s' (conf=%.2f) → (%d, %d)", text, conf, cx, cy)
                return cx, cy

        raise GroundingError(f"OCR: '{query}' not found (min_conf={ocfg.get('confidence_min', 0.3)})")
