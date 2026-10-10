"""Model capability tiers (TwinRouterBench vocabulary, see DECISIONS D14)."""

from __future__ import annotations

from enum import IntEnum


class Tier(IntEnum):
    """Ordered capability/cost tier. Higher value means a stronger model."""

    LOW = 0
    MID = 1
    MID_HIGH = 2
    HIGH = 3

    @classmethod
    def from_label(cls, label: str) -> Tier:
        """Parse a lowercase label such as ``"mid_high"``."""
        try:
            return cls[label.upper()]
        except KeyError:
            raise ValueError(f"unknown tier label: {label!r}") from None

    @property
    def label(self) -> str:
        return self.name.lower()
