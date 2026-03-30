"""
Render benchmark: sopdf vs PyMuPDF

Measures:
  1. Document open time
  2. Single-page render at 72 / 150 / 300 DPI
  3. Full-document sequential render (all 50 pages) at 150 DPI
  4. Full-document parallel render (ProcessPoolExecutor) at 150 DPI
     - sopdf strategy A: one-page-per-worker (legacy)
     - sopdf strategy B: batched pages per worker (optimised)
     - PyMuPDF: one-page-per-worker (process)
     - PyMuPDF: thread pool (PyMuPDF is thread-safe; pypdfium2 is not)

Thread-safety note
------------------
pypdfium2 (sopdf's rendering engine) is NOT thread-safe — concurrent calls
to PdfDocument() from multiple threads cause SIGABRT.  sopdf therefore only
supports process-based parallelism.  PyMuPDF's bundled PDFium is patched for
thread safety and supports both strategies.

Methodology
-----------
- Each measurement: N_WARMUP warm-up runs (discarded) + N_RUNS timed runs.
- Reports mean ± std-dev, min and max.
- Both libraries render to PNG bytes so the comparison is end-to-end
  (open → decode → rasterise → encode).
"""

from __future__ import annotations

import gc
import os
import statistics
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from pathlib import Path
from typing import Callable

import pymupdf  # PyMuPDF

import sopdf
from sopdf._utils import _render_batch, _render_one
from sopdf._render import _build_args, _build_batch_args

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

N_WARMUP = 1
N_RUNS = 5
BENCH_PDF = Path(__file__).parent / "fixtures" / "bench_50pages.pdf"
SINGLE_PAGE_DPIS = [72, 150, 300]
N_WORKERS = os.cpu_count() or 4


# ---------------------------------------------------------------------------
# Timing utility
# ---------------------------------------------------------------------------

def timed(fn: Callable, n_warmup: int = N_WARMUP, n_runs: int = N_RUNS) -> dict:
    """Run *fn* n_warmup + n_runs times; return stats over the timed runs."""
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

def _mupdf_render_page(path: Path, page_index: int, dpi: int) -> bytes:
    with pymupdf.open(str(path)) as doc:
        page = doc[page_index]
        mat = pymupdf.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat, colorspace=pymupdf.csRGB, alpha=False)
        return pix.tobytes("png")


def _mupdf_render_all_sequential(path: Path, dpi: int) -> list[bytes]:
    results = []
    with pymupdf.open(str(path)) as doc:
        for page in doc:
            mat = pymupdf.Matrix(dpi / 72, dpi / 72)
            pix = page.get_pixmap(matrix=mat, colorspace=pymupdf.csRGB, alpha=False)
            results.append(pix.tobytes("png"))
    return results


def _mupdf_render_one_worker(args: tuple) -> bytes:
    """Top-level picklable worker for PyMuPDF parallel rendering."""
    path_str, page_index, dpi = args
    with pymupdf.open(path_str) as doc:
        page = doc[page_index]
        mat = pymupdf.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat, colorspace=pymupdf.csRGB, alpha=False)
        return pix.tobytes("png")


def _mupdf_render_parallel_process(path: Path, dpi: int) -> list[bytes]:
    with pymupdf.open(str(path)) as doc:
        n = len(doc)
    args = [(str(path), i, dpi) for i in range(n)]
    with ProcessPoolExecutor(max_workers=N_WORKERS) as ex:
        return list(ex.map(_mupdf_render_one_worker, args))


def _mupdf_render_parallel_thread(path: Path, dpi: int) -> list[bytes]:
    """Thread-based parallel render for PyMuPDF (thread-safe PDFium build)."""
    with pymupdf.open(str(path)) as doc:
        n = len(doc)

    def _one(page_index: int) -> bytes:
        with pymupdf.open(str(path)) as d:
            page = d[page_index]
            mat = pymupdf.Matrix(dpi / 72, dpi / 72)
            pix = page.get_pixmap(matrix=mat, colorspace=pymupdf.csRGB, alpha=False)
            return pix.tobytes("png")

    with ThreadPoolExecutor(max_workers=N_WORKERS) as ex:
        return list(ex.map(_one, range(n)))


# ---------------------------------------------------------------------------
# sopdf helpers
# ---------------------------------------------------------------------------

def _sopdf_render_page(path: Path, page_index: int, dpi: int) -> bytes:
    with sopdf.open(str(path)) as doc:
        return doc[page_index].render(dpi=dpi, format="png")


def _sopdf_render_all_sequential(path: Path, dpi: int) -> list[bytes]:
    with sopdf.open(str(path)) as doc:
        return [doc[i].render(dpi=dpi, format="png") for i in range(doc.page_count)]


def _sopdf_render_parallel_legacy(path: Path, dpi: int) -> list[bytes]:
    """One page per worker — the original strategy (one task per page)."""
    with sopdf.open(str(path)) as doc:
        pages = list(doc.pages)
        args = _build_args(pages, dpi, "png", False)
    with ProcessPoolExecutor(max_workers=N_WORKERS) as ex:
        return list(ex.map(_render_one, args))


def _sopdf_render_parallel_batched(path: Path, dpi: int) -> list[bytes]:
    """Batched strategy: each worker gets N/cpu_count pages, opens PDF once."""
    with sopdf.open(str(path)) as doc:
        pages = list(doc.pages)
        return sopdf.render_pages(pages, dpi=dpi, parallel=True)


# ---------------------------------------------------------------------------
# Main benchmark runner
# ---------------------------------------------------------------------------

def run() -> dict:
    """Execute all render benchmarks and return results dict."""
    if not BENCH_PDF.exists():
        from tests.benchmark.fixtures import build_bench_pdf
        print("  Generating benchmark fixture …")
        build_bench_pdf()

    pdf = BENCH_PDF
    results: dict[str, dict] = {}

    print(f"  Workers: {N_WORKERS}")

    # ── 1. Document open time ─────────────────────────────────────────────
    print("  [open] sopdf …", end=" ", flush=True)
    results["open_sopdf"] = timed(lambda: sopdf.open(str(pdf)).close())
    print(f"{results['open_sopdf']['mean']*1000:.1f} ms")

    print("  [open] pymupdf …", end=" ", flush=True)
    results["open_pymupdf"] = timed(lambda: pymupdf.open(str(pdf)).close())
    print(f"{results['open_pymupdf']['mean']*1000:.1f} ms")

    # ── 2. Single-page render at multiple DPIs ────────────────────────────
    for dpi in SINGLE_PAGE_DPIS:
        print(f"  [single page @ {dpi} DPI] sopdf …", end=" ", flush=True)
        results[f"single_page_dpi{dpi}_sopdf"] = timed(
            lambda d=dpi: _sopdf_render_page(pdf, 0, d)
        )
        print(f"{results[f'single_page_dpi{dpi}_sopdf']['mean']*1000:.1f} ms")

        print(f"  [single page @ {dpi} DPI] pymupdf …", end=" ", flush=True)
        results[f"single_page_dpi{dpi}_pymupdf"] = timed(
            lambda d=dpi: _mupdf_render_page(pdf, 0, d)
        )
        print(f"{results[f'single_page_dpi{dpi}_pymupdf']['mean']*1000:.1f} ms")

    # ── 3. Full-document sequential render @ 150 DPI ──────────────────────
    print("  [50-page sequential @ 150 DPI] sopdf …", end=" ", flush=True)
    results["seq_all_sopdf"] = timed(
        lambda: _sopdf_render_all_sequential(pdf, 150), n_runs=3
    )
    print(f"{results['seq_all_sopdf']['mean']:.3f} s")

    print("  [50-page sequential @ 150 DPI] pymupdf …", end=" ", flush=True)
    results["seq_all_pymupdf"] = timed(
        lambda: _mupdf_render_all_sequential(pdf, 150), n_runs=3
    )
    print(f"{results['seq_all_pymupdf']['mean']:.3f} s")

    # ── 4. Parallel render: legacy vs batched ─────────────────────────────
    print("  [50-page parallel/legacy @ 150 DPI] sopdf …", end=" ", flush=True)
    results["par_legacy_sopdf"] = timed(
        lambda: _sopdf_render_parallel_legacy(pdf, 150), n_runs=3
    )
    print(f"{results['par_legacy_sopdf']['mean']:.3f} s")

    print("  [50-page parallel/batched @ 150 DPI] sopdf …", end=" ", flush=True)
    results["par_batched_sopdf"] = timed(
        lambda: _sopdf_render_parallel_batched(pdf, 150), n_runs=3
    )
    print(f"{results['par_batched_sopdf']['mean']:.3f} s")

    print("  [50-page parallel/process @ 150 DPI] pymupdf …", end=" ", flush=True)
    results["par_process_pymupdf"] = timed(
        lambda: _mupdf_render_parallel_process(pdf, 150), n_runs=3
    )
    print(f"{results['par_process_pymupdf']['mean']:.3f} s")

    print("  [50-page parallel/thread @ 150 DPI] pymupdf …", end=" ", flush=True)
    results["par_thread_pymupdf"] = timed(
        lambda: _mupdf_render_parallel_thread(pdf, 150), n_runs=3
    )
    print(f"{results['par_thread_pymupdf']['mean']:.3f} s")

    return results


if __name__ == "__main__":
    print("=== Render Benchmark ===")
    run()
