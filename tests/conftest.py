"""
Pytest configuration — auto-generate test fixtures if they don't exist.

All fixture PDFs are built with pikepdf so no external files are needed.
"""

from __future__ import annotations

import io
import struct
from pathlib import Path

import pikepdf
import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Helpers — building minimal PDF content streams
# ---------------------------------------------------------------------------

def _make_page(pdf: pikepdf.Pdf, text: str = "", rotation: int = 0) -> None:
    """Append a new page (with optional text content) to *pdf*."""
    content = b""
    resources = pikepdf.Dictionary()

    if text:
        safe = text.replace("\\", "\\\\").replace("(", r"\(").replace(")", r"\)")
        content = f"BT /F1 14 Tf 72 700 Td ({safe}) Tj ET".encode()
        resources = pikepdf.Dictionary(
            Font=pikepdf.Dictionary(
                F1=pikepdf.Dictionary(
                    Type=pikepdf.Name("/Font"),
                    Subtype=pikepdf.Name("/Type1"),
                    BaseFont=pikepdf.Name("/Helvetica"),
                )
            )
        )

    page_dict = pikepdf.Dictionary(
        Type=pikepdf.Name("/Page"),
        MediaBox=pikepdf.Array([0, 0, 612, 792]),
        Resources=resources,
        Contents=pdf.make_stream(content),
    )
    if rotation:
        page_dict["/Rotate"] = rotation

    # pikepdf.Page wraps the dictionary so PageList.append() accepts it
    pdf.pages.append(pikepdf.Page(page_dict))


# ---------------------------------------------------------------------------
# Fixture generators
# ---------------------------------------------------------------------------

def _build_simple(path: Path) -> None:
    pdf = pikepdf.new()
    _make_page(pdf, "Hello, sopdf! This is a simple test document.")
    pdf.save(str(path))


def _build_multipage(path: Path) -> None:
    pdf = pikepdf.new()
    for i in range(5):
        _make_page(pdf, f"Page {i + 1} of 5. sopdf multipage test.")
    pdf.save(str(path))


def _build_encrypted(path: Path) -> None:
    pdf = pikepdf.new()
    _make_page(pdf, "This page is inside an encrypted PDF.")
    encryption = pikepdf.Encryption(user="secret", owner="owner_pass")
    pdf.save(str(path), encryption=encryption)


def _build_rotated(path: Path) -> None:
    pdf = pikepdf.new()
    for deg in [0, 90, 180, 270]:
        _make_page(pdf, f"This page is rotated {deg} degrees.", rotation=deg)
    pdf.save(str(path))


def _build_mixed(path: Path) -> None:
    """Multi-page document with varied text content (simulating mixed content)."""
    pdf = pikepdf.new()
    texts = [
        "Chapter 1: Introduction to sopdf",
        "Chapter 2: Rendering pages at high DPI",
        "Chapter 3: Extracting and searching text",
    ]
    for t in texts:
        _make_page(pdf, t)
    pdf.save(str(path))


def _build_corrupted(path: Path) -> None:
    """Write a valid PDF then corrupt the trailer slightly — pikepdf/pdfium can usually repair it."""
    pdf = pikepdf.new()
    _make_page(pdf, "Corrupted PDF test.")
    buf = io.BytesIO()
    pdf.save(buf)
    raw = bytearray(buf.getvalue())
    # Corrupt a few bytes in the middle (not the header or xref)
    mid = len(raw) // 2
    for i in range(min(8, len(raw) - mid)):
        raw[mid + i] ^= 0xFF
    path.write_bytes(bytes(raw))


# ---------------------------------------------------------------------------
# Session fixture — build once per test session
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def build_fixtures() -> None:
    """Create all test PDF fixtures if they don't already exist."""
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

    builders = {
        "simple.pdf": _build_simple,
        "multipage.pdf": _build_multipage,
        "encrypted.pdf": _build_encrypted,
        "rotated.pdf": _build_rotated,
        "mixed.pdf": _build_mixed,
        "corrupted.pdf": _build_corrupted,
    }

    for filename, builder in builders.items():
        target = FIXTURES_DIR / filename
        if not target.exists():
            builder(target)


# ---------------------------------------------------------------------------
# Convenience path fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def simple_pdf(build_fixtures) -> Path:
    return FIXTURES_DIR / "simple.pdf"


@pytest.fixture(scope="session")
def multipage_pdf(build_fixtures) -> Path:
    return FIXTURES_DIR / "multipage.pdf"


@pytest.fixture(scope="session")
def encrypted_pdf(build_fixtures) -> Path:
    return FIXTURES_DIR / "encrypted.pdf"


@pytest.fixture(scope="session")
def rotated_pdf(build_fixtures) -> Path:
    return FIXTURES_DIR / "rotated.pdf"


@pytest.fixture(scope="session")
def mixed_pdf(build_fixtures) -> Path:
    return FIXTURES_DIR / "mixed.pdf"


@pytest.fixture(scope="session")
def corrupted_pdf(build_fixtures) -> Path:
    return FIXTURES_DIR / "corrupted.pdf"
