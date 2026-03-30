"""
sopdf.Page — proxy to a single PDF page via the dual-engine backend.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from ._document import Document

from ._exceptions import PageError
from ._rect import Rect
from ._text import TextBlock


_VALID_ROTATIONS = {0, 90, 180, 270}


class Page:
    """Represents a single page within a :class:`~sopdf.Document`."""

    __slots__ = ("_doc", "_index")

    def __init__(self, doc: "Document", index: int) -> None:
        self._doc = doc
        self._index = index

    # ------------------------------------------------------------------
    # Basic properties
    # ------------------------------------------------------------------

    @property
    def number(self) -> int:
        """0-based page index."""
        return self._index

    @property
    def rect(self) -> Rect:
        """Page dimensions as a :class:`~sopdf.Rect` (in points)."""
        from ._utils import ensure_synced

        ensure_synced(self._doc)
        pdfium_page = self._doc._pdfium_doc[self._index]
        w = pdfium_page.get_width()
        h = pdfium_page.get_height()
        return Rect(0, 0, w, h)

    @property
    def rotation(self) -> int:
        """Current page rotation in degrees (0 / 90 / 180 / 270).

        Read via pypdfium2 so no pikepdf initialisation is required for
        read-only workflows.  If the document is dirty (pending write),
        :func:`~sopdf._utils.ensure_synced` re-loads pdfium first.
        """
        from ._utils import ensure_synced

        ensure_synced(self._doc)
        pdfium_page = self._doc._pdfium_doc[self._index]
        return pdfium_page.get_rotation()

    @rotation.setter
    def rotation(self, degrees: int) -> None:
        self.set_rotation(degrees)

    def set_rotation(self, degrees: int) -> None:
        """Set page rotation (must be 0, 90, 180, or 270)."""
        if degrees not in _VALID_ROTATIONS:
            raise PageError(f"Rotation must be one of {sorted(_VALID_ROTATIONS)}, got {degrees}.")
        import pikepdf

        self._doc._ensure_pike()
        pike_page = self._doc._pike_doc.pages[self._index]
        pike_page["/Rotate"] = degrees
        self._doc._dirty = True

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render(
        self,
        *,
        dpi: int = 72,
        format: str = "png",
        alpha: bool = False,
    ) -> bytes:
        """Render this page to image bytes.

        Parameters
        ----------
        dpi:
            Resolution in dots per inch. Default is 72.
        format:
            ``"png"`` (default) or ``"jpeg"``.
        alpha:
            Include alpha channel (PNG only).

        Returns
        -------
        bytes
            Encoded image data.
        """
        from ._utils import ensure_synced

        ensure_synced(self._doc)

        scale = dpi / 72.0
        pdfium_page = self._doc._pdfium_doc[self._index]
        bitmap = pdfium_page.render(scale=scale)  # pypdfium2 >= 4.0
        pil_image = bitmap.to_pil()

        buf = io.BytesIO()
        fmt = format.upper()
        if fmt == "JPEG":
            pil_image = pil_image.convert("RGB")
            pil_image.save(buf, format="JPEG")
        else:
            if not alpha:
                pil_image = pil_image.convert("RGB")
            pil_image.save(buf, format="PNG")
        return buf.getvalue()

    def render_to_file(
        self,
        path: Union[str, Path],
        *,
        dpi: int = 72,
        format: str = "png",
        alpha: bool = False,
    ) -> None:
        """Render this page and write the image to *path*."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = self.render(dpi=dpi, format=format, alpha=alpha)
        path.write_bytes(data)

    # ------------------------------------------------------------------
    # Text extraction
    # ------------------------------------------------------------------

    def get_text(self, *, rect: Union[Rect, None] = None) -> str:
        """Return the plain text of this page (or a sub-region)."""
        from ._utils import ensure_synced

        ensure_synced(self._doc)
        pdfium_page = self._doc._pdfium_doc[self._index]
        text_page = pdfium_page.get_textpage()

        if rect is None:
            return text_page.get_text_range()

        return text_page.get_text_bounded(
            left=rect.x0,
            bottom=rect.y0,
            right=rect.x1,
            top=rect.y1,
        )

    def get_text_blocks(
        self,
        *,
        rect: Union[Rect, None] = None,
        format: str = "list",
    ) -> list:
        """Extract text blocks with bounding boxes.

        Parameters
        ----------
        rect:
            Optionally restrict extraction to this region.
        format:
            ``"list"`` (default) returns :class:`~sopdf.TextBlock` objects;
            ``"dict"`` returns plain dictionaries.
        """
        from ._utils import ensure_synced

        ensure_synced(self._doc)
        pdfium_page = self._doc._pdfium_doc[self._index]
        text_page = pdfium_page.get_textpage()

        n_chars = text_page.count_chars()
        n_rects = text_page.count_rects(0, n_chars)

        blocks = []
        for i in range(n_rects):
            l, b, r, t = text_page.get_rect(i)  # (left, bottom, right, top) in pts
            block_rect = Rect(l, b, r, t)

            if rect is not None and not rect.intersects(block_rect):
                continue

            text = text_page.get_text_bounded(left=l, bottom=b, right=r, top=t)
            if not text.strip():
                continue

            tb = TextBlock(text=text, rect=block_rect)
            if format == "dict":
                blocks.append(tb.to_dict())
            else:
                blocks.append(tb)

        return blocks

    # ------------------------------------------------------------------
    # Text search
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        *,
        match_case: bool = False,
    ) -> list[Rect]:
        """Search for *query* on this page and return a list of match :class:`~sopdf.Rect` objects."""
        from ._utils import ensure_synced

        ensure_synced(self._doc)
        pdfium_page = self._doc._pdfium_doc[self._index]
        text_page = pdfium_page.get_textpage()
        searcher = text_page.search(query, match_case=match_case, match_whole_word=False)

        rects = []
        while True:
            # In pypdfium2, get_next() returns (char_index, char_count) or None.
            match = searcher.get_next()
            if match is None:
                break
            char_index, char_count = match
            # Collect per-character bounding boxes and union them into one Rect
            ls, bs, rs, ts = [], [], [], []
            for i in range(char_index, char_index + char_count):
                cb = text_page.get_charbox(i)  # (l, b, r, t)
                ls.append(cb[0]); bs.append(cb[1])
                rs.append(cb[2]); ts.append(cb[3])
            if ls:
                rects.append(Rect(min(ls), min(bs), max(rs), max(ts)))
        return rects

    def search_text_blocks(
        self,
        query: str,
        *,
        match_case: bool = False,
    ) -> list[dict]:
        """Search for *query* and return each match with its surrounding text block context.

        Returns
        -------
        list[dict]
            Each entry: ``{'text': str, 'rect': Rect, 'match_rect': Rect}``
        """
        match_rects = self.search(query, match_case=match_case)
        if not match_rects:
            return []

        blocks = self.get_text_blocks()
        results = []
        for match_rect in match_rects:
            # Find the text block that contains (or overlaps) this match
            context_block = None
            for block in blocks:
                if block.rect.intersects(match_rect):
                    context_block = block
                    break
            results.append(
                {
                    "text": context_block.text if context_block else "",
                    "rect": context_block.rect if context_block else match_rect,
                    "match_rect": match_rect,
                }
            )
        return results

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"Page(number={self._index}, rect={self.rect!r})"
