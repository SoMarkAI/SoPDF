"""
sopdf.Outline — read-only bookmark (table of contents) tree.

Built on first access via ``doc.outline``; uses pypdfium2 so no
pikepdf initialisation is needed for read-only workflows.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._document import Document


@dataclass(frozen=True)
class OutlineItem:
    """A single bookmark node in the document outline (immutable).

    Attributes:
        title:    Bookmark label as it appears in the reader TOC panel.
        page:     0-based target page index; ``-1`` when no destination page.
        level:    Nesting depth; 0 = top-level item.
        children: Nested child items as a frozen tuple.
    """

    title: str
    page: int
    level: int
    children: tuple["OutlineItem", ...] = ()

    def to_dict(self) -> dict:
        """Serialize to a plain dict (recursive)."""
        return {
            "title": self.title,
            "page": self.page,
            "level": self.level,
            "children": [c.to_dict() for c in self.children],
        }

    def __repr__(self) -> str:
        return (
            f"OutlineItem(title={self.title!r}, page={self.page}, "
            f"level={self.level}, children={len(self.children)})"
        )


def _build_tree(pdfium_doc) -> list[OutlineItem]:
    """Convert pypdfium2's flat depth-first TOC list into a nested OutlineItem tree."""
    flat = list(pdfium_doc.get_toc())
    if not flat:
        return []

    # Build as mutable dicts first, then freeze into dataclasses.
    root: list[dict] = []
    stack: list[dict] = []  # tracks current ancestry path by level

    for fi in flat:
        dest = fi.get_dest()
        page = dest.get_index() if dest is not None else -1
        node = {
            "title": fi.get_title() or "",
            "page": page,
            "level": fi.level,
            "children": [],
        }
        # Pop ancestors that are at the same or deeper level.
        while stack and stack[-1]["level"] >= fi.level:
            stack.pop()
        (stack[-1]["children"] if stack else root).append(node)
        stack.append(node)

    def _freeze(d: dict) -> OutlineItem:
        return OutlineItem(
            title=d["title"],
            page=d["page"],
            level=d["level"],
            children=tuple(_freeze(c) for c in d["children"]),
        )

    return [_freeze(d) for d in root]


class Outline:
    """Read-only bookmark tree for a PDF document.

    Obtained via ``doc.outline`` — never constructed directly.
    The tree is built once at instantiation time from pypdfium2's TOC data.
    """

    def __init__(self, doc: "Document") -> None:
        from ._utils import ensure_synced
        ensure_synced(doc)
        self._items: list[OutlineItem] = _build_tree(doc._pdfium_doc)

    @property
    def items(self) -> list[OutlineItem]:
        """Top-level outline items (each may have nested ``children``)."""
        return self._items

    def to_list(self) -> list[dict]:
        """Flat DFS traversal compatible with PyMuPDF ``get_toc()`` output.

        Returns
        -------
        list[dict]
            Each entry: ``{"level": int, "title": str, "page": int}``
        """
        result: list[dict] = []

        def _walk(items: list[OutlineItem]) -> None:
            for item in items:
                result.append({"level": item.level, "title": item.title, "page": item.page})
                _walk(list(item.children))

        _walk(self._items)
        return result

    def _count_all(self, items: list[OutlineItem]) -> int:
        return sum(1 + self._count_all(list(item.children)) for item in items)

    def __len__(self) -> int:
        """Total number of outline nodes across all nesting levels."""
        return self._count_all(self._items)

    def __iter__(self):
        """Iterate over top-level items."""
        return iter(self._items)

    def __bool__(self) -> bool:
        """``True`` when the document has at least one outline item."""
        return bool(self._items)

    def __repr__(self) -> str:
        return f"Outline(top_level={len(self._items)}, total={len(self)})"
