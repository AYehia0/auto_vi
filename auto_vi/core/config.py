"""Load and expose the TOML configuration."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

_DEFAULT_PATH = Path(__file__).resolve().parent.parent.parent / "config.toml"


def load(path: str | Path | None = None) -> dict[str, Any]:
    p = Path(path) if path else _DEFAULT_PATH
    with p.open("rb") as f:
        return tomllib.load(f)
