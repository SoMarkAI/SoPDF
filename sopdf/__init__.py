"""
sopdf — Apache 2.0-licensed PDF processing library.

Drop-in capable replacement for PyMuPDF workflows, built on
pypdfium2 (rendering) + pikepdf (structure/writing).

Quick start::

    import sopdf

    with sopdf.open("document.pdf") as doc:
        print(doc.page_count)
        page = doc[0]
        img = page.render(dpi=150)
        text = page.get_text()
"""

__version__ = "0.1.0"

from ._document import Document
from ._exceptions import FileDataError, PDFError, PageError, PasswordError
from ._merge import merge
from ._metadata import Metadata
from ._outline import Outline, OutlineItem
from ._page import Page
from ._rect import Rect
from ._render import render_pages, render_pages_to_files
from ._text import TextBlock


def open(
    path=None,
    password=None,
    *,
    stream=None,
):
    """Open a PDF and return a :class:`Document`.

    Parameters
    ----------
    path:
        File-system path to the PDF (``str`` or :class:`pathlib.Path`).
    password:
        Password string for encrypted PDFs.
    stream:
        Raw PDF bytes. Use instead of *path* to open from memory.

    Returns
    -------
    Document

    Examples
    --------
    >>> doc = sopdf.open("file.pdf")
    >>> doc = sopdf.open("file.pdf", password="secret")
    >>> doc = sopdf.open(stream=pdf_bytes)
    """
    return Document._open(path, stream=stream, password=password)


__all__ = [
    "__version__",
    # factory
    "open",
    "merge",
    "render_pages",
    "render_pages_to_files",
    # classes
    "Document",
    "Metadata",
    "Outline",
    "OutlineItem",
    "Page",
    "Rect",
    "TextBlock",
    # exceptions
    "PDFError",
    "PasswordError",
    "FileDataError",
    "PageError",
]
