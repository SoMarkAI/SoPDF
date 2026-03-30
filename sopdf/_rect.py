"""
sopdf.Rect — pure-Python immutable rectangle.

All coordinates are in PDF points (1 pt = 1/72 inch).
Origin is bottom-left in PDF space, but we follow the pypdfium2/screen convention:
y0 is the top edge, y1 is the bottom edge (y increases downward).
"""

from __future__ import annotations

from typing import Union


class Rect:
    """A rectangle defined by (x0, y0, x1, y1).

    x0, y0 — top-left corner
    x1, y1 — bottom-right corner
    """

    __slots__ = ("x0", "y0", "x1", "y1")

    def __init__(self, x0: float, y0: float, x1: float, y1: float) -> None:
        self.x0 = float(x0)
        self.y0 = float(y0)
        self.x1 = float(x1)
        self.y1 = float(y1)

    # ------------------------------------------------------------------
    # Basic geometry
    # ------------------------------------------------------------------

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    @property
    def is_valid(self) -> bool:
        """True when x0 ≤ x1 and y0 ≤ y1."""
        return self.x0 <= self.x1 and self.y0 <= self.y1

    @property
    def is_empty(self) -> bool:
        """True when the rectangle has zero area."""
        return self.width == 0 or self.height == 0

    def get_area(self) -> float:
        """Return the area of this rectangle."""
        if not self.is_valid:
            return 0.0
        return self.width * self.height

    # ------------------------------------------------------------------
    # Containment & intersection tests
    # ------------------------------------------------------------------

    def contains(self, other: Union["Rect", tuple]) -> bool:
        """Return True if *other* (Rect or (x, y) point) is fully inside this rect."""
        if isinstance(other, Rect):
            return (
                self.x0 <= other.x0
                and self.y0 <= other.y0
                and self.x1 >= other.x1
                and self.y1 >= other.y1
            )
        # treat as (x, y) point
        x, y = other
        return self.x0 <= x <= self.x1 and self.y0 <= y <= self.y1

    def intersects(self, other: "Rect") -> bool:
        """Return True if this rect overlaps *other* (touching edges count)."""
        return (
            self.x0 <= other.x1
            and self.x1 >= other.x0
            and self.y0 <= other.y1
            and self.y1 >= other.y0
        )

    # ------------------------------------------------------------------
    # Region operations — all return new Rect instances
    # ------------------------------------------------------------------

    def intersect(self, other: "Rect") -> "Rect":
        """Return the overlapping region, or an empty Rect if there is none."""
        x0 = max(self.x0, other.x0)
        y0 = max(self.y0, other.y0)
        x1 = min(self.x1, other.x1)
        y1 = min(self.y1, other.y1)
        if x0 > x1 or y0 > y1:
            return Rect(0, 0, 0, 0)
        return Rect(x0, y0, x1, y1)

    def include_rect(self, other: "Rect") -> "Rect":
        """Return the bounding box that contains both rectangles."""
        return Rect(
            min(self.x0, other.x0),
            min(self.y0, other.y0),
            max(self.x1, other.x1),
            max(self.y1, other.y1),
        )

    def include_point(self, x: float, y: float) -> "Rect":
        """Return a new Rect expanded to include the point (x, y)."""
        return Rect(
            min(self.x0, x),
            min(self.y0, y),
            max(self.x1, x),
            max(self.y1, y),
        )

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Rect):
            return NotImplemented
        return (
            self.x0 == other.x0
            and self.y0 == other.y0
            and self.x1 == other.x1
            and self.y1 == other.y1
        )

    def __iter__(self):
        """Allow tuple(rect) → (x0, y0, x1, y1)."""
        return iter((self.x0, self.y0, self.x1, self.y1))

    def __repr__(self) -> str:
        return f"Rect(x0={self.x0}, y0={self.y0}, x1={self.x1}, y1={self.y1})"
