"""Notepad automation workflow: fetch posts → type → save → close, repeat."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

import requests

from auto_vi.core import automation as auto
from auto_vi.core import capture
from auto_vi.grounding import GroundingError, locate

log = logging.getLogger(__name__)


def _fallback_posts(count: int) -> list[dict]:
    return [
        {"id": i, "title": f"Sample post {i}", "body": f"Body of sample post {i}.\n"}
        for i in range(1, count + 1)
    ]


def fetch_posts(cfg: dict[str, Any]) -> list[dict]:
    wf = cfg["workflow"]
    url = wf["api_url"]
    for attempt in range(1, 4):
        try:
            log.info("Fetching posts from %s (attempt %d)", url, attempt)
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            return resp.json()[: wf["post_count"]]
        except requests.RequestException as exc:
            log.warning("API attempt %d failed: %s", attempt, exc)
            time.sleep(2)
    log.warning("API unavailable — using fallback posts")
    return _fallback_posts(wf["post_count"])


def _ensure_output_dir(cfg: dict[str, Any]) -> Path:
    out = Path.home() / cfg["workflow"]["output_dir"]
    out.mkdir(parents=True, exist_ok=True)
    return out


def _ground_and_launch(cfg: dict[str, Any], attempt: int) -> bool:
    """Kill leftover Notepad, minimize windows, screenshot, ground icon, launch."""
    retry = cfg["retry"]
    wf = cfg["workflow"]

    # 1. Kill any lingering Notepad (cached sessions, unsaved prompts, etc.)
    auto.kill_notepad()

    # 2. Minimize everything so desktop icons are visible
    auto.minimize_all()

    # 3. Screenshot the clean desktop
    ss_dir = cfg["logging"].get("screenshots_dir", "screenshots")
    img, offset = capture.take(
        save_path=Path(ss_dir) / f"desktop_attempt_{attempt}.png",
        monitor=cfg["display"].get("monitor", 1),
    )

    # 4. Ground and double-click the Notepad icon
    x, y = locate(img, wf["target_icon"], cfg)
    auto.double_click(x + offset[0], y + offset[1], cfg)
    auto.pause(cfg)

    # 5. Wait for Notepad window
    if not auto.wait_for_window(wf["window_title"], retry["window_timeout"]):
        return False

    # 6. Win11 Notepad may restore a previous session — force a blank document
    time.sleep(0.5)
    auto.hotkey("ctrl", "n")
    time.sleep(0.5)

    return True


def _type_and_save(post: dict, cfg: dict[str, Any]) -> None:
    wf = cfg["workflow"]
    out_dir = _ensure_output_dir(cfg)
    filepath = str(out_dir / wf["filename_fmt"].format(id=post["id"]))

    if Path(filepath).exists():
        log.warning("File already exists, will overwrite: %s", filepath)

    # Select all + delete to guarantee empty editor (in case Ctrl+N didn't work)
    auto.hotkey("ctrl", "a")
    time.sleep(0.1)
    auto.hotkey("delete")
    time.sleep(0.1)

    # Type post content
    content = f"Title: {post['title']}\n\n{post['body']}"
    auto.type_text(content, cfg)
    auto.pause(cfg)

    # Open Save As dialog (Ctrl+Shift+S always opens Save As, even if file exists)
    auto.hotkey("ctrl", "shift", "s")
    time.sleep(1.5)

    # Type full path into filename field
    auto.hotkey("ctrl", "a")
    time.sleep(0.2)
    auto.type_text(filepath, cfg)
    time.sleep(0.3)

    # Confirm save
    auto.hotkey("enter")
    time.sleep(1.0)

    # Handle "already exists — overwrite?" (Yes button)
    auto.hotkey("alt", "y")
    time.sleep(0.5)

    # Force-kill Notepad to avoid any "do you want to save" on close
    auto.kill_notepad()


def run(cfg: dict[str, Any]) -> None:
    posts = fetch_posts(cfg)
    retry = cfg["retry"]

    for post in posts:
        log.info("── Post %d: %s", post["id"], post["title"][:50])

        launched = False
        for attempt in range(1, retry["max_attempts"] + 1):
            try:
                launched = _ground_and_launch(cfg, attempt)
                if launched:
                    break
            except GroundingError:
                log.warning("Attempt %d: grounding failed", attempt)
            time.sleep(retry["delay_seconds"])

        if not launched:
            log.error("Could not launch Notepad for post %d, skipping.", post["id"])
            continue

        _type_and_save(post, cfg)
        log.info("✓ Post %d saved", post["id"])

    # Final cleanup
    auto.kill_notepad()
    log.info("── All %d posts processed.", len(posts))
