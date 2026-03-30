"""
SoPDF vs PyMuPDF — master benchmark runner.

Usage
-----
    python tests/benchmark/run_benchmarks.py

Output
------
  tests/benchmark/reports/report_<ISO-timestamp>.md

The script:
  1. Ensures the benchmark PDF fixture exists (generates if needed).
  2. Runs render benchmarks (bench_render.py).
  3. Runs text-extraction benchmarks (bench_text.py).
  4. Writes a comprehensive Markdown report to tests/benchmark/reports/.
"""

from __future__ import annotations

import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure project root is on sys.path so local sopdf is importable
_root = Path(__file__).resolve().parents[2]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import pymupdf
import pypdfium2
import pikepdf

import sopdf
from tests.benchmark.fixtures import BENCH_PDF, build_bench_pdf

REPORTS_DIR = Path(__file__).parent / "reports"


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _fmt(secs: float) -> str:
    return f"{secs * 1000:.1f} ms"


def _ratio(sopdf_t: float, mupdf_t: float) -> str:
    if mupdf_t == 0:
        return "N/A"
    r = sopdf_t / mupdf_t
    if r <= 1.0:
        return f"**{1/r:.2f}× faster**"
    return f"{r:.2f}× slower"


def _row(label: str, so: dict, mu: dict) -> str:
    return (
        f"| {label} "
        f"| {_fmt(so['mean'])} ± {_fmt(so['stdev'])} "
        f"| {_fmt(mu['mean'])} ± {_fmt(mu['stdev'])} "
        f"| {_ratio(so['mean'], mu['mean'])} |"
    )


def _speedup(seq_t: float, par_t: float) -> str:
    if par_t == 0:
        return "N/A"
    return f"{seq_t / par_t:.2f}×"


# ---------------------------------------------------------------------------
# Report generator
# ---------------------------------------------------------------------------

def generate_report(render_results: dict, text_results: dict) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = REPORTS_DIR / f"report_{ts}.md"
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    r = render_results
    t = text_results

    lines: list[str] = [
        "# SoPDF vs PyMuPDF — Benchmark Report",
        "",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} · "
        f"Platform: {platform.machine()} · "
        f"Python: {sys.version.split()[0]} · "
        f"Cores: {os.cpu_count()}",
        "",
        "## Environment",
        "",
        "| | Version |",
        "| --- | --- |",
        f"| sopdf | {sopdf.__version__} |",
        f"| PyMuPDF | {pymupdf.__version__} |",
        f"| pypdfium2 | {pypdfium2.version.PYPDFIUM_INFO} |",
        f"| pikepdf | {pikepdf.__version__} |",
        f"| Fixture | `{BENCH_PDF.name}` — 50 pages, {BENCH_PDF.stat().st_size // 1024} KB |",
        "",
        "---",
        "",
        "## Rendering",
        "",
        "| Scenario | sopdf (mean ± σ) | PyMuPDF (mean ± σ) | Ratio |",
        "| --- | --- | --- | --- |",
        _row("Open document", r["open_sopdf"], r["open_pymupdf"]),
        _row("Render 1 page @ 72 DPI",  r["single_page_dpi72_sopdf"],  r["single_page_dpi72_pymupdf"]),
        _row("Render 1 page @ 150 DPI", r["single_page_dpi150_sopdf"], r["single_page_dpi150_pymupdf"]),
        _row("Render 1 page @ 300 DPI", r["single_page_dpi300_sopdf"], r["single_page_dpi300_pymupdf"]),
        _row("50 pages sequential @ 150 DPI", r["seq_all_sopdf"], r["seq_all_pymupdf"]),
        _row("50 pages parallel/process legacy @ 150 DPI", r["par_legacy_sopdf"], r["par_process_pymupdf"]),
        _row("50 pages parallel/process batched @ 150 DPI", r["par_batched_sopdf"], r["par_process_pymupdf"]),
        f"| 50 pages parallel/thread @ 150 DPI | N/A (pypdfium2 not thread-safe)"
        f" | {_fmt(r['par_thread_pymupdf']['mean'])} ± {_fmt(r['par_thread_pymupdf']['stdev'])} | — |",
        "",
        "### Parallel speedup vs sequential",
        "",
        "| Strategy | sopdf | PyMuPDF |",
        "| --- | --- | --- |",
        f"| process/legacy  | {_speedup(r['seq_all_sopdf']['mean'], r['par_legacy_sopdf']['mean'])} | {_speedup(r['seq_all_pymupdf']['mean'], r['par_process_pymupdf']['mean'])} |",
        f"| process/batched | {_speedup(r['seq_all_sopdf']['mean'], r['par_batched_sopdf']['mean'])} | — |",
        f"| thread          | N/A | {_speedup(r['seq_all_pymupdf']['mean'], r['par_thread_pymupdf']['mean'])} |",
        "",
        "---",
        "",
        "## Text Extraction",
        "",
        "| Scenario | sopdf (mean ± σ) | PyMuPDF (mean ± σ) | Ratio |",
        "| --- | --- | --- | --- |",
        _row("Plain text — 50 pages",        t["text_all_sopdf"],   t["text_all_pymupdf"]),
        _row("Text blocks — 50 pages",       t["blocks_all_sopdf"], t["blocks_all_pymupdf"]),
        _row("Search 'benchmark' — 50 pages",t["search_all_sopdf"], t["search_all_pymupdf"]),
        _row("Region extract — 50 pages",    t["region_all_sopdf"], t["region_all_pymupdf"]),
        "",
        "### Correctness (page 0)",
        "",
        "| Metric | sopdf | PyMuPDF |",
        "| --- | --- | --- |",
        f"| Characters | {t['verify']['sopdf_chars']} | {t['verify']['pymupdf_chars']} |",
        f"| Blocks | {t['verify']['sopdf_blocks']} | {t['verify']['pymupdf_blocks']} |",
        f"| Word overlap | {t['verify']['content_overlap_pct']:.0f}% | — |",
        "",
        "---",
        "",
        "_Auto-generated by `tests/benchmark/run_benchmarks.py`_",
        "",
    ]

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    # Ensure fixture exists
    if not BENCH_PDF.exists():
        print("Generating 50-page benchmark fixture …")
        build_bench_pdf()
        print(f"  → {BENCH_PDF}  ({BENCH_PDF.stat().st_size / 1024:.1f} KB)")

    print(
        f"\nBenchmark PDF: {BENCH_PDF.name}  "
        f"({BENCH_PDF.stat().st_size / 1024:.1f} KB, 50 pages)"
    )

    print("\n── Render benchmarks ───────────────────────────────────────────")
    import tests.benchmark.bench_render as br
    render_results = br.run()

    print("\n── Text extraction benchmarks ──────────────────────────────────")
    import tests.benchmark.bench_text as bt
    text_results = bt.run()

    report = generate_report(render_results, text_results)
    print(f"\n✓ Report written → {report.relative_to(_root)}")
    print(f"  ({report.stat().st_size} bytes)")

    _print_summary(render_results, text_results)


def _print_summary(r: dict, t: dict) -> None:
    """Print a concise verdict table to stdout."""

    def _v(so: float, mu: float) -> str:
        ratio = so / mu if mu else 0
        if ratio <= 1:
            return f"sopdf {1/ratio:.2f}× faster"
        return f"sopdf {ratio:.2f}× slower"

    rows = [
        # (scenario, sopdf_dict, pymupdf_dict)
        ("Open document",            r["open_sopdf"],                    r["open_pymupdf"]),
        ("Render 1 page @ 72 DPI",   r["single_page_dpi72_sopdf"],       r["single_page_dpi72_pymupdf"]),
        ("Render 1 page @ 150 DPI",  r["single_page_dpi150_sopdf"],      r["single_page_dpi150_pymupdf"]),
        ("Render 1 page @ 300 DPI",  r["single_page_dpi300_sopdf"],      r["single_page_dpi300_pymupdf"]),
        ("Render 50 pages seq.",      r["seq_all_sopdf"],                  r["seq_all_pymupdf"]),
        ("Render 50 pages parallel", r["par_batched_sopdf"],              r["par_process_pymupdf"]),
        ("Text extract (50 pages)",  t["text_all_sopdf"],                 t["text_all_pymupdf"]),
        ("Text blocks (50 pages)",   t["blocks_all_sopdf"],               t["blocks_all_pymupdf"]),
        ("Search (50 pages)",        t["search_all_sopdf"],               t["search_all_pymupdf"]),
        ("Region extract (50 pages)",t["region_all_sopdf"],               t["region_all_pymupdf"]),
    ]

    col_w = [max(len(s), 28) for s in ["Scenario", "sopdf", "PyMuPDF", "Verdict"]]
    col_w = [28, 14, 14, 24]
    sep = "┼".join("─" * (w + 2) for w in col_w)
    header = "│".join(f" {h:<{w}} " for h, w in zip(
        ["Scenario", "sopdf", "PyMuPDF", "Verdict"], col_w
    ))

    print("\n" + "─" * (sum(col_w) + len(col_w) * 3 + len(col_w) - 1))
    print(header)
    print(sep)
    for scenario, so, mu in rows:
        so_s = _fmt(so["mean"])
        mu_s = _fmt(mu["mean"])
        verdict = _v(so["mean"], mu["mean"])
        print("│".join(f" {v:<{w}} " for v, w in zip(
            [scenario, so_s, mu_s, verdict], col_w
        )))
    print("─" * (sum(col_w) + len(col_w) * 3 + len(col_w) - 1))


if __name__ == "__main__":
    main()
