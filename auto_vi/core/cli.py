"""CLI entry point for auto-vi."""

from __future__ import annotations

import argparse
import logging
import sys

from auto_vi.core import config
from auto_vi.workflow import orchestrator


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Vision-Based Desktop Automation with Dynamic Icon Grounding",
    )
    parser.add_argument("-c", "--config", default=None, help="Path to config.toml")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable DEBUG logging")
    args = parser.parse_args()

    cfg = config.load(args.config)

    level = "DEBUG" if args.verbose else cfg.get("logging", {}).get("level", "INFO")
    logging.basicConfig(
        level=getattr(logging, level),
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    try:
        orchestrator.run(cfg)
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception:
        logging.getLogger(__name__).exception("Fatal error")
        sys.exit(1)
