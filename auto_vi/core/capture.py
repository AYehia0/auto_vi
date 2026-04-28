"""Capture the primary monitor as a PIL Image."""

from __future__ import annotations

import logging
from pathlib import Path

import mss
from PIL import Image

log = logging.getLogger(__name__)


def take(save_path: str | Path | None = None, monitor: int = 1) -> tuple[Image.Image, tuple[int, int]]:
    """Return (image, (offset_x, offset_y)) for the chosen monitor."""
    with mss.mss() as sct:
        mon = sct.monitors[monitor]
        shot = sct.grab(mon)
        img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
        offset = (mon["left"], mon["top"])

    if save_path:
        p = Path(save_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(p))
        log.info("Screenshot saved → %s", p)

    return img, offset
