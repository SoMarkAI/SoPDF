"""
sopdf.Document — top-level PDF object.

Dual-engine backend:
  - pypdfium2 (PDFium): opened eagerly — fast (≈0.06 ms).
    Serves all read-only operations: render, text extraction, search,
    page count, metadata, page rotation reads.

  - pikepdf (libqpdf): opened **lazily** on the first write operation
    (rotation change, save, split, append, …).
    Avoids the ≈1.5 ms libqpdf parse cost for read-only sessions.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Iterator, Union

import pypdfium2 as pdfium

from ._exceptions import FileDataError, PageError, PasswordError


class Document:
    """Represents an open PDF document."""

    def __init__(
        self,
        _pdfium_doc: pdfium.PdfDocument,
        _source: Union[str, Path, None],
        *,
        _pike_doc=None,           # pre-built pikepdf handle (or None = lazy)
        _password: Union[bytes, None] = None,
        _stream: Union[bytes, None] = None,   # kept for lazy-pike init + workers
    ) -> None:
        self._pdfium_doc = _pdfium_doc
        self._source = _source
        self._pike_doc = _pike_doc        # None until first write
        self._password = _password
        self._stream = _stream
        self._dirty = False
        self._closed = False

    # ------------------------------------------------------------------
    # Factory (called by sopdf.open)
    # ------------------------------------------------------------------

    @classmethod
    def _open(
        cls,
        path: Union[str, Path, None] = None,
        *,
        stream: Union[bytes, None] = None,
        password: Union[str, None] = None,
    ) -> "Document":
        """Internal factory used by :func:`sopdf.open`.

        Only pypdfium2 is opened here; pikepdf is deferred until the
        first write operation to keep open latency minimal.
        """
        pwd_bytes = password.encode() if isinstance(password, str) else password

        if path is not None:
            path = Path(path)
            try:
                pdfium_doc = pdfium.PdfDocument(str(path), password=password)
            except pdfium.PdfiumError as exc:
                _msg = str(exc).lower()
                if "password" in _msg:
                    raise PasswordError(str(exc)) from exc
                raise FileDataError(str(exc)) from exc

            return cls(pdfium_doc, path, _password=pwd_bytes)

        elif stream is not None:
            try:
                pdfium_doc = pdfium.PdfDocument(stream, password=password)
            except pdfium.PdfiumError as exc:
                _msg = str(exc).lower()
                if "password" in _msg:
                    raise PasswordError(str(exc)) from exc
                raise FileDataError(str(exc)) from exc

            return cls(pdfium_doc, None, _password=pwd_bytes, _stream=stream)

        else:
            raise ValueError("Provide either a file path or stream= keyword argument.")

    # ------------------------------------------------------------------
    # Lazy pikepdf initialisation
    # ------------------------------------------------------------------

    def _ensure_pike(self) -> None:
        """Open the pikepdf engine on first write-operation request."""
        self._check_open()
        if self._pike_doc is not None:
            return

        import pikepdf

        try:
            if self._source is not None:
                self._pike_doc = pikepdf.open(
                    str(self._source), password=self._password or b""
                )
            elif self._stream is not None:
                self._pike_doc = pikepdf.open(
                    io.BytesIO(self._stream), password=self._password or b""
                )
            else:
                raise PDFError(
                    "Cannot initialise write engine: document has no file source. "
                    "Save the document to a file first."
                )
        except pikepdf.PasswordError as exc:
            raise PasswordError(str(exc)) from exc
        except pikepdf.PdfError as exc:
            raise FileDataError(str(exc)) from exc

    # ------------------------------------------------------------------
    # Properties — served from pypdfium2 (no pikepdf needed)
    # ------------------------------------------------------------------

    @property
    def page_count(self) -> int:
        self._check_open()
        from ._utils import ensure_synced

        ensure_synced(self)  # reflect any appended/removed pages in pdfium
        return len(self._pdfium_doc)

    @property
    def metadata(self) -> dict:
        """Document metadata dict (keys lowercase).

        Sourced from pypdfium2 for zero-cost reads.
        """
        self._check_open()
        return {k.lower(): v for k, v in self._pdfium_doc.get_metadata_dict().items()}

    @property
    def is_encrypted(self) -> bool:
        """Whether this document is (or was) password-protected."""
        self._check_open()
        self._ensure_pike()
        return self._pike_doc.is_encrypted

    # ------------------------------------------------------------------
    # Page access
    # ------------------------------------------------------------------

    def __getitem__(self, index: int) -> "Page":
        self._check_open()
        from ._page import Page

        count = self.page_count
        if index < 0:
            index = count + index
        if not (0 <= index < count):
            raise PageError(
                f"Page index {index} out of range (document has {count} pages)."
            )
        return Page(self, index)

    def load_page(self, index: int) -> "Page":
        """Same as ``doc[index]``."""
        return self[index]

    @property
    def pages(self) -> "_PageList":
        return _PageList(self)

    def __len__(self) -> int:
        return self.page_count

    def __iter__(self) -> Iterator["Page"]:
        return iter(self.pages)

    # ------------------------------------------------------------------
    # Save / export  (require pikepdf)
    # ------------------------------------------------------------------

    def save(
        self,
        path: Union[str, Path],
        *,
        compress: bool = True,
        garbage: bool = False,
        linearize: bool = False,
    ) -> None:
        """Save the document to *path*."""
        self._check_open()
        self._ensure_pike()

        import pikepdf
        from ._utils import safe_save

        save_kwargs: dict = {}
        if compress:
            save_kwargs["compress_streams"] = True
        if garbage:
            save_kwargs["object_stream_mode"] = pikepdf.ObjectStreamMode.generate
        if linearize:
            save_kwargs["linearize"] = True

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if self._source is not None and Path(path).resolve() == Path(self._source).resolve():
            safe_save(self._pike_doc, path, **save_kwargs)
        else:
            self._pike_doc.save(str(path), **save_kwargs)

    def to_bytes(self, *, compress: bool = True) -> bytes:
        """Serialise to bytes without writing to disk."""
        self._check_open()
        self._ensure_pike()
        buf = io.BytesIO()
        save_kwargs = {}
        if compress:
            save_kwargs["compress_streams"] = True
        self._pike_doc.save(buf, **save_kwargs)
        return buf.getvalue()

    # ------------------------------------------------------------------
    # Split  (require pikepdf)
    # ------------------------------------------------------------------

    def split(
        self,
        pages: list[int],
        output: Union[str, Path, None] = None,
    ) -> "Document":
        """Extract *pages* (0-based indices) into a new Document (or save directly)."""
        self._check_open()
        self._ensure_pike()

        import pikepdf

        count = self.page_count
        for idx in pages:
            if not (0 <= idx < count):
                raise PageError(f"Page index {idx} out of range.")

        new_pike = pikepdf.new()
        for idx in pages:
            new_pike.pages.append(self._pike_doc.pages[idx])

        buf = io.BytesIO()
        new_pike.save(buf)
        buf.seek(0)
        raw = buf.read()

        if output is not None:
            output = Path(output)
            output.parent.mkdir(parents=True, exist_ok=True)
            new_pike.save(str(output))
            new_pike.close()

        new_pdfium = pdfium.PdfDocument(raw)
        # The new document already has its pike_doc; no lazy loading needed.
        return Document(new_pdfium, None, _pike_doc=new_pike)

    def split_each(self, output_dir: Union[str, Path]) -> None:
        """Save every page as a separate PDF into *output_dir*."""
        self._check_open()
        self._ensure_pike()

        import pikepdf

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        for i in range(self.page_count):
            new_pike = pikepdf.new()
            new_pike.pages.append(self._pike_doc.pages[i])
            new_pike.save(str(output_dir / f"page_{i}.pdf"))
            new_pike.close()

    # ------------------------------------------------------------------
    # Append (merge helper)  (require pikepdf on both docs)
    # ------------------------------------------------------------------

    def append(self, other: "Document") -> None:
        """Append all pages of *other* to this document."""
        self._check_open()
        self._ensure_pike()
        other._ensure_pike()
        for page in other._pike_doc.pages:
            self._pike_doc.pages.append(page)
        self._dirty = True

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        if not self._closed:
            try:
                self._pdfium_doc.close()
            except Exception:
                pass
            if self._pike_doc is not None:
                try:
                    self._pike_doc.close()
                except Exception:
                    pass
            self._closed = True

    def __enter__(self) -> "Document":
        return self

    def __exit__(self, *_) -> None:
        self.close()

    def __repr__(self) -> str:
        source = str(self._source) if self._source else "<stream>"
        return f"Document(source={source!r}, pages={self.page_count})"

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _check_open(self) -> None:
        if self._closed:
            raise PDFError("Operation on a closed Document.")


# Avoid circular import — imported here so _check_open can raise it
from ._exceptions import PDFError  # noqa: E402


class _PageList:
    """Lazy sequence of Page objects. Supports iteration and indexing."""

    __slots__ = ("_doc",)

    def __init__(self, doc: Document) -> None:
        self._doc = doc

    def __len__(self) -> int:
        return self._doc.page_count

    def __getitem__(self, index: int) -> "Page":
        return self._doc[index]

    def __iter__(self) -> Iterator["Page"]:
        for i in range(len(self)):
            yield self._doc[i]

    def __repr__(self) -> str:
        return f"<PageList len={len(self)}>"
