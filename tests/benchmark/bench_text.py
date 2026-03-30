"""
Text extraction benchmark: sopdf vs PyMuPDF

Measures:
  1. Plain text extraction — full page (get_text / get_text_range)
  2. Text-block extraction — with bounding boxes
  3. Keyword search across all 50 pages
  4. Selective region extraction (sub-rect of page)

Methodology
-----------
Same warm-up / timed-run protocol as bench_render:
  N_WARMUP warm-up runs followed by N_RUNS timed runs.
Stats: mean ± std-dev, min, max.
"""

from __future__ import annotations

import gc
import statistics
import time
from pathlib import Path
from typing import Callable

import pymupdf

import sopdf

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

N_WARMUP = 1
N_RUNS = 5
BENCH_PDF = Path(__file__).parent / "fixtures" / "bench_50pages.pdf"

# Keyword that appears on every page, so search touches all pages
SEARCH_QUERY = "benchmark"
# Sub-rectangle: upper half of the page (in PDF pts, origin bottom-left)
SUB_RECT_SOPDF = sopdf.Rect(0, 400, 612, 792)


# ---------------------------------------------------------------------------
# Timing utility (same as bench_render)
# ---------------------------------------------------------------------------

def timed(fn: Callable, n_warmup: int = N_WARMUP, n_runs: int = N_RUNS) -> dict:
    for _ in range(n_warmup):
        fn()
        gc.collect()
    times = []
    for _ in range(n_runs):
        gc.collect()
        t0 = time.perf_counter()
        fn()
        times.append(time.perf_counter() - t0)
    return {
        "mean": statistics.mean(times),
        "stdev": statistics.stdev(times) if len(times) > 1 else 0.0,
        "min": min(times),
        "max": max(times),
        "runs": n_runs,
    }


# ---------------------------------------------------------------------------
# PyMuPDF helpers
# ---------------------------------------------------------------------------

def _mupdf_extract_text_all(path: Path) -> list[str]:
    """Extract plain text from every page."""
    results = []
    with pymupdf.open(str(path)) as doc:
        for page in doc:
            results.append(page.get_text("text"))
    return results


def _mupdf_extract_blocks_all(path: Path) -> list[list]:
    """Extract text blocks (with bounding boxes) from every page."""
    results = []
    with pymupdf.open(str(path)) as doc:
        for page in doc:
            results.append(page.get_text("blocks"))
    return results


def _mupdf_search_all(path: Path, query: str) -> list[list]:
    """Search for *query* on every page; return list of match-rect lists."""
    results = []
    with pymupdf.open(str(path)) as doc:
        for page in doc:
            results.append(page.search_for(query))
    return results


def _mupdf_extract_text_region(path: Path) -> list[str]:
    """Extract text from a sub-rect of every page."""
    results = []
    clip = pymupdf.Rect(0, 0, 612, 392)  # upper half in PyMuPDF coord (top-down)
    with pymupdf.open(str(path)) as doc:
        for page in doc:
            results.append(page.get_text("text", clip=clip))
    return results


# ---------------------------------------------------------------------------
# sopdf helpers
# ---------------------------------------------------------------------------

def _sopdf_extract_text_all(path: Path) -> list[str]:
    with sopdf.open(str(path)) as doc:
        return [doc[i].get_text() for i in range(doc.page_count)]


def _sopdf_extract_blocks_all(path: Path) -> list[list]:
    with sopdf.open(str(path)) as doc:
        return [doc[i].get_text_blocks() for i in range(doc.page_count)]


def _sopdf_search_all(path: Path, query: str) -> list[list]:
    with sopdf.open(str(path)) as doc:
        return [doc[i].search(query) for i in range(doc.page_count)]


def _sopdf_extract_text_region(path: Path) -> list[str]:
    with sopdf.open(str(path)) as doc:
        return [doc[i].get_text(rect=SUB_RECT_SOPDF) for i in range(doc.page_count)]


# ---------------------------------------------------------------------------
# Correctness spot-check
# ---------------------------------------------------------------------------

def verify_text_output(path: Path) -> dict:
    """
    Sanity-check: compare text output between the two libraries for page 0.
    Returns a dict with basic stats.
    """
    with sopdf.open(str(path)) as doc:
        sopdf_text = doc[0].get_text()
        sopdf_blocks = doc[0].get_text_blocks()

    with pymupdf.open(str(path)) as doc:
        pymupdf_text = doc[0].get_text("text")
        pymupdf_blocks = doc[0].get_text("blocks")

    return {
        "sopdf_chars": len(sopdf_text),
        "pymupdf_chars": len(pymupdf_text),
        "sopdf_blocks": len(sopdf_blocks),
        "pymupdf_blocks": len(pymupdf_blocks),
        # Check that all sopdf text appears in pymupdf text (modulo whitespace)
        "content_overlap_pct": _overlap_pct(sopdf_text, pymupdf_text),
    }


def _overlap_pct(a: str, b: str) -> float:
    """Percentage of unique words in *a* that also appear in *b*."""
    words_a = set(a.lower().split())
    words_b = set(b.lower().split())
    if not words_a:
        return 0.0
    return len(words_a & words_b) / len(words_a) * 100


# ---------------------------------------------------------------------------
# Main benchmark runner
# ---------------------------------------------------------------------------

def run() -> dict:
    """Execute all text benchmarks and return results dict."""
    if not BENCH_PDF.exists():
        from tests.benchmark.fixtures import build_bench_pdf
        print("  Generating benchmark fixture …")
        build_bench_pdf()

    pdf = BENCH_PDF
    results: dict[str, dict] = {}

    # Correctness check first
    cv = verify_text_output(pdf)
    print(
        f"  [verify] sopdf chars={cv['sopdf_chars']}, "
        f"pymupdf chars={cv['pymupdf_chars']}, "
        f"overlap={cv['content_overlap_pct']:.0f}%, "
        f"sopdf blocks={cv['sopdf_blocks']}, "
        f"pymupdf blocks={cv['pymupdf_blocks']}"
    )
    results["verify"] = cv

    # ── 1. Plain text extraction (all pages) ──────────────────────────────
    print("  [text/all pages] sopdf …", end=" ", flush=True)
    results["text_all_sopdf"] = timed(lambda: _sopdf_extract_text_all(pdf))
    print(f"{results['text_all_sopdf']['mean']*1000:.1f} ms")

    print("  [text/all pages] pymupdf …", end=" ", flush=True)
    results["text_all_pymupdf"] = timed(lambda: _mupdf_extract_text_all(pdf))
    print(f"{results['text_all_pymupdf']['mean']*1000:.1f} ms")

    # ── 2. Text blocks extraction (all pages) ─────────────────────────────
    print("  [blocks/all pages] sopdf …", end=" ", flush=True)
    results["blocks_all_sopdf"] = timed(lambda: _sopdf_extract_blocks_all(pdf))
    print(f"{results['blocks_all_sopdf']['mean']*1000:.1f} ms")

    print("  [blocks/all pages] pymupdf …", end=" ", flush=True)
    results["blocks_all_pymupdf"] = timed(lambda: _mupdf_extract_blocks_all(pdf))
    print(f"{results['blocks_all_pymupdf']['mean']*1000:.1f} ms")

    # ── 3. Keyword search (all pages) ─────────────────────────────────────
    print(f"  [search '{SEARCH_QUERY}'/all pages] sopdf …", end=" ", flush=True)
    results["search_all_sopdf"] = timed(
        lambda: _sopdf_search_all(pdf, SEARCH_QUERY)
    )
    print(f"{results['search_all_sopdf']['mean']*1000:.1f} ms")

    print(f"  [search '{SEARCH_QUERY}'/all pages] pymupdf …", end=" ", flush=True)
    results["search_all_pymupdf"] = timed(
        lambda: _mupdf_search_all(pdf, SEARCH_QUERY)
    )
    print(f"{results['search_all_pymupdf']['mean']*1000:.1f} ms")

    # ── 4. Sub-region text extraction (all pages) ─────────────────────────
    print("  [region text/all pages] sopdf …", end=" ", flush=True)
    results["region_all_sopdf"] = timed(lambda: _sopdf_extract_text_region(pdf))
    print(f"{results['region_all_sopdf']['mean']*1000:.1f} ms")

    print("  [region text/all pages] pymupdf …", end=" ", flush=True)
    results["region_all_pymupdf"] = timed(lambda: _mupdf_extract_text_region(pdf))
    print(f"{results['region_all_pymupdf']['mean']*1000:.1f} ms")

    return results


if __name__ == "__main__":
    print("=== Text Extraction Benchmark ===")
    run()
