"""
sopdf.TextBlock — represents a single block of text with a bounding rect.
"""

from __future__ import annotations

from ._rect import Rect


class TextBlock:
    """A block of text extracted from a page, together with its bounding box."""

    __slots__ = ("text", "rect")

    def __init__(self, text: str, rect: Rect) -> None:
        self.text: str = text
        self.rect: Rect = rect

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "rect": {
                "x0": self.rect.x0,
                "y0": self.rect.y0,
                "x1": self.rect.x1,
                "y1": self.rect.y1,
            },
        }

    def __repr__(self) -> str:
        preview = self.text[:40].replace("\n", " ")
        if len(self.text) > 40:
            preview += "…"
        return f"TextBlock(text={preview!r}, rect={self.rect!r})"
