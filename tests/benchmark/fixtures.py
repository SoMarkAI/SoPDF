"""
Benchmark fixture generation.

Generates a rich 50-page PDF suitable for meaningful render and text
extraction benchmarks.  Content intentionally uses multiple fonts, font
sizes, colored vector graphics, and varied text densities per page so
that rendering is CPU-representative rather than trivially fast.

Re-run standalone to re-build the fixture:
    python tests/benchmark/fixtures.py
"""

from __future__ import annotations

import io
import math
from pathlib import Path

import pikepdf

FIXTURE_DIR = Path(__file__).parent / "fixtures"
BENCH_PDF = FIXTURE_DIR / "bench_50pages.pdf"

# Page geometry
PAGE_W = 612  # points  (8.5 in)
PAGE_H = 792  # points  (11 in)
N_PAGES = 50

# --------------------------------------------------------------------------
# Low-level PDF content-stream helpers
# --------------------------------------------------------------------------

def _rect_cmd(x: float, y: float, w: float, h: float,
              r: float, g: float, b: float) -> bytes:
    """Filled rectangle with solid RGB colour."""
    return (
        f"q {r:.3f} {g:.3f} {b:.3f} rg "
        f"{x:.1f} {y:.1f} {w:.1f} {h:.1f} re f Q\n"
    ).encode()


def _text_cmd(x: float, y: float, font: str, size: int, text: str) -> bytes:
    """Single text-show command (PDF BT … ET)."""
    safe = (
        text
        .replace("\\", "\\\\")
        .replace("(", r"\(")
        .replace(")", r"\)")
    )
    return f"BT /{font} {size} Tf {x:.1f} {y:.1f} Td ({safe}) Tj ET\n".encode()


def _build_page_content(page_num: int) -> bytes:
    """
    Build a content stream for one page.

    Layout:
      - Header bar (dark-blue rectangle spanning the top)
      - Title in large white Helvetica-Bold text
      - 8 alternating-colour section blocks, each with body text
      - A footer bar
    """
    buf = io.BytesIO()

    # ── Header rectangle ──────────────────────────────────────────────────
    buf.write(_rect_cmd(0, PAGE_H - 60, PAGE_W, 60, 0.12, 0.23, 0.45))

    # ── Title ─────────────────────────────────────────────────────────────
    title = f"SoPDF Benchmark Document  —  Page {page_num + 1} of {N_PAGES}"
    buf.write(_text_cmd(24, PAGE_H - 40, "F2", 18, title))

    # ── Body sections ─────────────────────────────────────────────────────
    colours = [
        (0.95, 0.97, 1.00),
        (1.00, 0.97, 0.92),
        (0.94, 1.00, 0.94),
        (1.00, 0.93, 0.93),
    ]
    y = PAGE_H - 80
    for section in range(8):
        section_h = 80
        r, g, b = colours[section % len(colours)]

        # Section background
        buf.write(_rect_cmd(20, y - section_h, PAGE_W - 40, section_h, r, g, b))

        # Section heading
        heading = (
            f"Section {section + 1}: Performance Characteristics "
            f"(Page {page_num + 1}, Section {section + 1})"
        )
        buf.write(_text_cmd(30, y - 18, "F2", 11, heading))

        # Body text — three lines of dummy prose
        sentences = [
            (
                f"This section benchmarks rendering at 72, 150, and 300 DPI "
                f"for page {page_num + 1}, section {section + 1}."
            ),
            (
                f"Text extraction validates character counts and bounding-box "
                f"accuracy at word level (word_index={page_num * 8 + section})."
            ),
            (
                f"Search latency is measured over the full {N_PAGES}-page document "
                f"corpus with match_case=False (run_id={page_num * 8 + section:05d})."
            ),
        ]
        for line_i, sentence in enumerate(sentences):
            buf.write(_text_cmd(30, y - 34 - line_i * 14, "F1", 9, sentence))

        # A small accent rectangle on the left edge
        hue = (page_num * 0.05 + section * 0.12) % 1.0
        hr, hg, hb = _hsv_to_rgb(hue, 0.7, 0.85)
        buf.write(_rect_cmd(20, y - section_h + 4, 6, section_h - 8, hr, hg, hb))

        y -= section_h + 4

    # ── Footer bar ────────────────────────────────────────────────────────
    buf.write(_rect_cmd(0, 0, PAGE_W, 30, 0.12, 0.23, 0.45))
    footer = (
        f"sopdf v0.1.0  |  benchmark fixture  |  "
        f"page {page_num + 1}/{N_PAGES}  |  "
        f"MIT License"
    )
    buf.write(_text_cmd(24, 10, "F1", 8, footer))

    return buf.getvalue()


def _hsv_to_rgb(h: float, s: float, v: float) -> tuple[float, float, float]:
    """Minimal HSV → RGB conversion (all values in [0, 1])."""
    if s == 0:
        return v, v, v
    i = int(h * 6)
    f = h * 6 - i
    p, q, t_ = v * (1 - s), v * (1 - s * f), v * (1 - s * (1 - f))
    sector = i % 6
    if sector == 0:
        return v, t_, p
    if sector == 1:
        return q, v, p
    if sector == 2:
        return p, v, t_
    if sector == 3:
        return p, q, v
    if sector == 4:
        return t_, p, v
    return v, p, q


# --------------------------------------------------------------------------
# Resources (shared font dictionary for all pages)
# --------------------------------------------------------------------------

def _make_font_resources(pdf: pikepdf.Pdf) -> pikepdf.Dictionary:
    return pikepdf.Dictionary(
        Font=pikepdf.Dictionary(
            F1=pikepdf.Dictionary(
                Type=pikepdf.Name("/Font"),
                Subtype=pikepdf.Name("/Type1"),
                BaseFont=pikepdf.Name("/Helvetica"),
            ),
            F2=pikepdf.Dictionary(
                Type=pikepdf.Name("/Font"),
                Subtype=pikepdf.Name("/Type1"),
                BaseFont=pikepdf.Name("/Helvetica-Bold"),
            ),
        )
    )


# --------------------------------------------------------------------------
# Fixture builder
# --------------------------------------------------------------------------

def build_bench_pdf(path: Path = BENCH_PDF) -> Path:
    """Build (or rebuild) the 50-page benchmark PDF at *path*."""
    path.parent.mkdir(parents=True, exist_ok=True)

    pdf = pikepdf.new()
    resources = _make_font_resources(pdf)

    for i in range(N_PAGES):
        content = _build_page_content(i)
        page_dict = pikepdf.Dictionary(
            Type=pikepdf.Name("/Page"),
            MediaBox=pikepdf.Array([0, 0, PAGE_W, PAGE_H]),
            Resources=resources,
            Contents=pdf.make_stream(content),
        )
        pdf.pages.append(pikepdf.Page(page_dict))

    pdf.save(str(path))
    pdf.close()
    return path


if __name__ == "__main__":
    p = build_bench_pdf()
    print(f"Built benchmark fixture: {p}  ({p.stat().st_size / 1024:.1f} KB)")
