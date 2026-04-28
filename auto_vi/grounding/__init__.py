"""Grounding subpackage — strategy-based visual element location."""

from auto_vi.grounding.base import GroundingError, GroundingStrategy
from auto_vi.grounding.registry import locate

__all__ = ["GroundingError", "GroundingStrategy", "locate"]
