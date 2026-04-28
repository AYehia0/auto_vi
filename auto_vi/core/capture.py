"""Capture the primary monitor as a PIL Image."""

from __future__ import annotations

import logging
from pathlib import Path

import mss
from PIL import Image

log = logging.getLogger(__name__)


def take(save_path: str | Path | None = None) -> Image.Image:
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        shot = sct.grab(monitor)
        img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")

    if save_path:
        p = Path(save_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(p))
        log.info("Screenshot saved → %s", p)

    return img
