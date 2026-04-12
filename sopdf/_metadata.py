"""
sopdf.Metadata — read/write proxy for PDF Document Info dictionary.

Read operations are served by pypdfium2 (zero pikepdf cost).
Write operations lazily trigger pikepdf and mark the document dirty;
the next read automatically syncs via ensure_synced().
"""

from __future__ import annotations

import re
from datetime import datetime, timezone, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._document import Document


_DATE_RE = re.compile(
    r"^D?:?(\d{4})(\d{2})?(\d{2})?(\d{2})?(\d{2})?(\d{2})?"
    r"([Z+\-])?(\d{2})?'?(\d{2})?'?$"
)


def _parse_pdf_date(s: str | None) -> datetime | None:
    """Parse a PDF date string (``D:YYYYMMDDHHmmSSOHH'mm'``) into a :class:`datetime`.

    Returns ``None`` on missing or unparseable input — never raises.
    """
    if not s:
        return None
    m = _DATE_RE.match(s.strip())
    if not m:
        return None
    Y, Mo, D, H, Mi, S, sign, tzh, tzm = m.groups()
    try:
        tz = timezone.utc
        if sign and sign not in ("Z", "z"):
            delta = timedelta(hours=int(tzh or 0), minutes=int(tzm or 0))
            tz = timezone(delta if sign == "+" else -delta)
        return datetime(
            int(Y), int(Mo or 1), int(D or 1),
            int(H or 0), int(Mi or 0), int(S or 0),
            tzinfo=tz,
        )
    except (ValueError, TypeError):
        return None


class Metadata:
    """Read/write proxy for the PDF Document Info dictionary.

    Obtained via ``doc.metadata`` — never constructed directly.

    Read path (no pikepdf cost):
        ``meta.title`` → ``ensure_synced()`` → ``pypdfium2.get_metadata_dict()``

    Write path (lazy pikepdf initialisation):
        ``meta.title = "X"`` → ``_ensure_pike()`` → ``pike_doc.docinfo["/Title"]``
        → ``_dirty = True`` (sync happens on next read)
    """

    __slots__ = ("_doc",)

    def __init__(self, doc: "Document") -> None:
        self._doc = doc

    # ------------------------------------------------------------------ #
    # Internal helpers                                                     #
    # ------------------------------------------------------------------ #

    def _raw(self) -> dict:
        from ._utils import ensure_synced
        ensure_synced(self._doc)
        return self._doc._pdfium_doc.get_metadata_dict()

    def _get(self, pdf_key: str) -> str | None:
        return self._raw().get(pdf_key) or None

    def _set(self, pdf_key: str, value: str | None) -> None:
        import pikepdf
        self._doc._ensure_pike()
        dk = f"/{pdf_key}"
        if value is None:
            try:
                del self._doc._pike_doc.docinfo[dk]
            except KeyError:
                pass
        else:
            self._doc._pike_doc.docinfo[dk] = pikepdf.String(value)
        self._doc._dirty = True

    # ------------------------------------------------------------------ #
    # Standard text fields                                                 #
    # ------------------------------------------------------------------ #

    @property
    def title(self) -> str | None:
        """Document title (``/Title``)."""
        return self._get("Title")

    @title.setter
    def title(self, value: str | None) -> None:
        self._set("Title", value)

    @property
    def author(self) -> str | None:
        """Author name (``/Author``)."""
        return self._get("Author")

    @author.setter
    def author(self, value: str | None) -> None:
        self._set("Author", value)

    @property
    def subject(self) -> str | None:
        """Document subject (``/Subject``)."""
        return self._get("Subject")

    @subject.setter
    def subject(self, value: str | None) -> None:
        self._set("Subject", value)

    @property
    def keywords(self) -> str | None:
        """Search keywords (``/Keywords``)."""
        return self._get("Keywords")

    @keywords.setter
    def keywords(self, value: str | None) -> None:
        self._set("Keywords", value)

    @property
    def creator(self) -> str | None:
        """Authoring tool that created the source document (``/Creator``)."""
        return self._get("Creator")

    @creator.setter
    def creator(self, value: str | None) -> None:
        self._set("Creator", value)

    @property
    def producer(self) -> str | None:
        """Tool that produced the PDF (``/Producer``)."""
        return self._get("Producer")

    @producer.setter
    def producer(self, value: str | None) -> None:
        self._set("Producer", value)

    # ------------------------------------------------------------------ #
    # Date fields — raw strings + parsed datetimes                        #
    # ------------------------------------------------------------------ #

    @property
    def creation_date(self) -> str | None:
        """Raw PDF creation date string (``/CreationDate``), e.g. ``D:20240101120000+08'00'``."""
        return self._get("CreationDate")

    @creation_date.setter
    def creation_date(self, value: str | None) -> None:
        self._set("CreationDate", value)

    @property
    def mod_date(self) -> str | None:
        """Raw PDF modification date string (``/ModDate``)."""
        return self._get("ModDate")

    @mod_date.setter
    def mod_date(self, value: str | None) -> None:
        self._set("ModDate", value)

    @property
    def creation_datetime(self) -> datetime | None:
        """Creation date as a Python :class:`datetime`, or ``None`` if missing or unparseable."""
        return _parse_pdf_date(self.creation_date)

    @property
    def mod_datetime(self) -> datetime | None:
        """Modification date as a Python :class:`datetime`, or ``None`` if missing or unparseable."""
        return _parse_pdf_date(self.mod_date)

    # ------------------------------------------------------------------ #
    # Dict-like interface (backward compatibility)                         #
    # ------------------------------------------------------------------ #

    def to_dict(self) -> dict[str, str | None]:
        """Return all fields as a dict with lowercase keys.

        Matches the format of the old ``doc.metadata`` dict.
        """
        raw = self._raw()
        return {k.lower(): (v or None) for k, v in raw.items()}

    def __getitem__(self, key: str) -> str | None:
        """Support ``meta["title"]`` — backward compat with old dict-style access."""
        return self.to_dict().get(key)

    # ------------------------------------------------------------------ #
    # Dunder                                                               #
    # ------------------------------------------------------------------ #

    def __repr__(self) -> str:
        raw = self._raw()
        title = raw.get("Title") or ""
        author = raw.get("Author") or ""
        return f"Metadata(title={title!r}, author={author!r})"
