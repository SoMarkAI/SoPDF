"""
sopdf internal utilities:
  - Dirty-flag hot-reload (sync pikepdf → pypdfium2)
  - Safe overwrite (handles Windows file-lock on mmap'd files)
"""

from __future__ import annotations

import io
import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._document import Document


# ---------------------------------------------------------------------------
# Dual-engine state synchronisation
# ---------------------------------------------------------------------------

def ensure_synced(doc: "Document") -> None:
    """If the document is dirty, re-serialise pikepdf state into pypdfium2."""
    if doc._dirty:
        _sync_to_pdfium(doc)
        doc._dirty = False


def _sync_to_pdfium(doc: "Document") -> None:
    """Serialise *doc._pike_doc* to bytes and hot-reload *doc._pdfium_doc*."""
    import pypdfium2 as pdfium

    buf = io.BytesIO()
    doc._pike_doc.save(buf)
    buf.seek(0)
    raw = buf.read()

    # Close old pdfium handle before replacing it
    try:
        doc._pdfium_doc.close()
    except Exception:
        pass

    doc._pdfium_doc = pdfium.PdfDocument(raw)


# ---------------------------------------------------------------------------
# Safe file-overwrite (Windows mmap compatibility)
# ---------------------------------------------------------------------------

def safe_save(pike_doc, path: str | Path, **save_kwargs) -> None:
    """Write *pike_doc* to *path*, safely handling in-place overwrites.

    On Windows, an open mmap lock prevents writing directly to the source
    file.  We write to a sibling .tmp file first, close handles there, then
    do an atomic rename.
    """
    path = Path(path)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    try:
        pike_doc.save(str(tmp_path), **save_kwargs)
        # Atomic replace (works cross-platform in Python 3.3+)
        os.replace(tmp_path, path)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise


# ---------------------------------------------------------------------------
# Render worker helpers (multiprocessing pickle-safe)
# ---------------------------------------------------------------------------

def _render_one(args: tuple) -> bytes:
    """Top-level function so it can be pickled by ProcessPoolExecutor.

    args = (source, page_index, dpi, fmt, alpha)
    source is either a file path (str) or raw bytes.
    """
    import pypdfium2 as pdfium

    source, page_index, dpi, fmt, alpha = args
    pdf = pdfium.PdfDocument(source)

    try:
        page = pdf[page_index]
        scale = dpi / 72.0
        bitmap = page.render(scale=scale)
        pil_image = bitmap.to_pil()
        buf = io.BytesIO()
        fmt_upper = fmt.upper()
        if fmt_upper == "JPEG":
            pil_image = pil_image.convert("RGB")
            pil_image.save(buf, format="JPEG")
        else:
            if not alpha:
                pil_image = pil_image.convert("RGB")
            pil_image.save(buf, format="PNG")
        return buf.getvalue()
    finally:
        pdf.close()


def _render_batch(args: tuple) -> list[bytes]:
    """Render a batch of pages from a single document in one worker call.

    args = (source, page_indices, dpi, fmt, alpha)

    Opening the PDF once per worker and rendering multiple pages amortises
    the file-open and import overhead across all pages in the batch.
    """
    import pypdfium2 as pdfium

    source, page_indices, dpi, fmt, alpha = args
    pdf = pdfium.PdfDocument(source)

    results: list[bytes] = []
    try:
        scale = dpi / 72.0
        fmt_upper = fmt.upper()
        for idx in page_indices:
            page = pdf[idx]
            bitmap = page.render(scale=scale)
            pil_image = bitmap.to_pil()
            buf = io.BytesIO()
            if fmt_upper == "JPEG":
                pil_image = pil_image.convert("RGB")
                pil_image.save(buf, format="JPEG")
            else:
                if not alpha:
                    pil_image = pil_image.convert("RGB")
                pil_image.save(buf, format="PNG")
            results.append(buf.getvalue())
    finally:
        pdf.close()
    return results
