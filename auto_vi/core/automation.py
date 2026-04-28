"""Mouse / keyboard helpers wrapping pyautogui + pywinauto."""

from __future__ import annotations

import logging
import subprocess
import time
from typing import Any

import pyautogui

log = logging.getLogger(__name__)

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05


def kill_notepad() -> None:
    """Force-kill all Notepad processes so we start clean."""
    subprocess.run(
        ["taskkill", "/F", "/IM", "Notepad.exe"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    time.sleep(0.5)
    log.info("Killed all Notepad instances")


def minimize_all() -> None:
    """Win+D to show desktop — ensures icons are visible for screenshot."""
    pyautogui.hotkey("win", "d")
    time.sleep(1.0)
    log.info("Minimized all windows (Win+D)")


def double_click(x: int, y: int, cfg: dict[str, Any]) -> None:
    interval = cfg["automation"]["double_click_interval"]
    pyautogui.doubleClick(x, y, interval=interval)
    log.info("Double-clicked (%d, %d)", x, y)


def click(x: int, y: int) -> None:
    pyautogui.click(x, y)
    log.info("Clicked (%d, %d)", x, y)


def type_text(text: str, cfg: dict[str, Any]) -> None:
    """Type text. Uses clipboard paste for anything with newlines or non-ASCII."""
    if text.isascii() and "\n" not in text and "\t" not in text:
        pyautogui.typewrite(text, interval=cfg["automation"]["typing_interval"])
    else:
        import pyperclip
        pyperclip.copy(text)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.3)
    log.info("Typed %d chars", len(text))


def hotkey(*keys: str) -> None:
    pyautogui.hotkey(*keys)
    log.info("Hotkey %s", "+".join(keys))


def wait_for_window(title: str, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            from pywinauto import Desktop
            wins = Desktop(backend="uia").windows(title_re=f".*{title}.*")
            if wins:
                log.info("Window '%s' found", title)
                return True
        except Exception:
            pass
        time.sleep(0.5)
    log.warning("Window '%s' not found within %.1fs", title, timeout)
    return False


def pause(cfg: dict[str, Any]) -> None:
    time.sleep(cfg["automation"]["action_delay"])
