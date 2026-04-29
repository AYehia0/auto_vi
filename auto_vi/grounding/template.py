"""Template-matching grounding strategy using OpenCV.

Multi-scale template matching to handle slight size variations.
Fast but brittle to theme/icon-size changes.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image

from auto_vi.grounding.base import GroundingError, GroundingStrategy

log = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"


class TemplateStrategy(GroundingStrategy):
    name = "template"

    def locate(self, image: Image.Image, query: str, cfg: dict[str, Any]) -> tuple[int, int]:
        tcfg = cfg["grounding"].get("template", {})
        threshold = tcfg.get("confidence_min", 0.7)
        scales = tcfg.get("scales", [0.8, 0.9, 1.0, 1.1, 1.2])

        # Load template for the query (e.g. "Notepad" -> templates/notepad.png)
        tpl_path = _TEMPLATES_DIR / f"{query.lower()}.png"
        if not tpl_path.exists():
            raise GroundingError(f"Template not found: {tpl_path}")

        screenshot = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
        template = cv2.imread(str(tpl_path), cv2.IMREAD_GRAYSCALE)
        if template is None:
            raise GroundingError(f"Failed to read template: {tpl_path}")

        best_val, best_loc, best_size = 0.0, None, None

        for scale in scales:
            w = int(template.shape[1] * scale)
            h = int(template.shape[0] * scale)
            if w < 1 or h < 1 or w > screenshot.shape[1] or h > screenshot.shape[0]:
                continue
            scaled = cv2.resize(template, (w, h), interpolation=cv2.INTER_AREA)
            result = cv2.matchTemplate(screenshot, scaled, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            log.debug("Template scale=%.1f → conf=%.3f at %s", scale, max_val, max_loc)
            if max_val > best_val:
                best_val, best_loc, best_size = max_val, max_loc, (w, h)

        if best_val < threshold or best_loc is None or best_size is None:
            raise GroundingError(
                f"Template: '{query}' best conf={best_val:.3f} < threshold={threshold}"
            )

        cx = best_loc[0] + best_size[0] // 2
        cy = best_loc[1] + best_size[1] // 2
        log.info("Template found '%s' (conf=%.3f, scale match) → (%d, %d)", query, best_val, cx, cy)
        return cx, cy
