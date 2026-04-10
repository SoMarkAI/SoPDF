<div align="center">

# SoPDF

**The PDF processing library that belongs to everyone.**

[![PyPI version](https://img.shields.io/pypi/v/sopdf.svg)](https://pypi.org/project/sopdf/)
[![Python versions](https://img.shields.io/pypi/pyversions/sopdf.svg)](https://pypi.org/project/sopdf/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

```
pip install sopdf
```

English | [中文](README_CN.md)

</div>

---

## Why SoPDF?

**1. 🚀 High Performance**

With parallel processing and other optimizations, SoPDF significantly outperforms alternatives: rendering up to **1.56x faster**, plain text extraction **2.7x faster**, and full-text search **3x faster** — while maintaining **99% word-level accuracy consistency** with PyMuPDF. See the [Performance Benchmark](#performance-benchmark) section, or run it yourself.

**2. ✨ Feature-Rich**

Built on [`pypdfium2`](https://github.com/pypdfium2-team/pypdfium2) (Google PDFium, for rendering and text) and [`pikepdf`](https://github.com/pikepdf/pikepdf) (libqpdf, for structure and writing). SoPDF covers the entire workflow from rendering and text extraction to structural editing.

**3. 🎯 Clean API**

Intuition as documentation. You would have designed it the same way.

**4. 🔓 Permissive License**

In PDF processing, feature-rich + open source often comes with a license unfriendly to the open-source ecosystem. But SoPDF delivers equivalent core capabilities under the **Apache 2.0 License** — no strings attached, no license audit, zero friction. Embed it, ship it, fork it. It's yours.

> If you find SoPDF helpful, please consider giving it a ⭐ Star — it really means a lot to us. Every star fuels our motivation to keep improving.

---

## Benchmarks

> Measured on Apple M-series (arm64, 10-core), Python 3.10, against a 50-page PDF fixture.
> Run the suite yourself: `python tests/benchmark/run_benchmarks.py`

### Rendering vs PyMuPDF

| Scenario | SoPDF | PyMuPDF | Speedup |
| --- | --- | --- | --- |
| Open document | 0.1 ms | 0.2 ms | **1.39× faster** |
| Render 1 page @ 72 DPI | 6.6 ms | 9.1 ms | **1.38× faster** |
| Render 1 page @ 150 DPI | 20.0 ms | 30.3 ms | **1.51× faster** |
| Render 1 page @ 300 DPI | 64.6 ms | 101.1 ms | **1.56× faster** |
| 50 pages sequential @ 150 DPI | 966.9 ms | 1470.3 ms | **1.52× faster** |
| 50 pages parallel @ 150 DPI | 410.7 ms | 447.2 ms | **1.09× faster** |

SoPDF wins at every DPI — and the margin widens at higher resolutions. In parallel mode, SoPDF achieves a genuine **2.35× speedup** over its own sequential baseline. PyMuPDF's thread-parallel path, on the other hand, actually *regresses* to 1548.9 ms (slower than sequential) because MuPDF serialises concurrent renders behind a global lock.

### Text Extraction vs PyMuPDF

| Scenario | SoPDF | PyMuPDF | Speedup |
| --- | --- | --- | --- |
| Plain text — 50 pages | 26.0 ms | 70.0 ms | **2.70× faster** |
| Text blocks — 50 pages | 63.6 ms | 70.4 ms | **1.11× faster** |
| Search 'benchmark' — 50 pages | 30.2 ms | 91.0 ms | **3.01× faster** |
| Region extract — 50 pages | 27.6 ms | 39.6 ms | **1.43× faster** |

Text search is the standout: **3× faster** than PyMuPDF. Plain-text extraction follows at **2.7×**. Correctness is verified — sopdf and PyMuPDF produce 99% word-level overlap on the same document, so the speed advantage carries no accuracy trade-off.

---

## Architecture

SoPDF runs two best-in-class C/C++ engines in tandem:

```
┌──────────────────────────────────────────┐
│               SoPDF Python API           │
├───────────────────┬──────────────────────┤
│   pypdfium2       │   pikepdf            │
│   (Google PDFium) │   (libqpdf)          │
│                   │                      │
│   • Rendering     │   • Structure reads  │
│   • Text extract  │   • All writes       │
│   • Search        │   • Save / compress  │
└───────────────────┴──────────────────────┘
```

A **dirty-flag + hot-reload** mechanism keeps the two engines in sync:
when you write via pikepdf (e.g. rotate a page), the next read operation
(e.g. render) automatically reserialises the document into pypdfium2 —
zero manual sync required.

Files are opened with **lazy loading / mmap** — a 500 MB PDF opens in
milliseconds and only the pages you actually access are loaded.

---

## Quick Start

```bash
pip install sopdf
```

Requires Python 3.10+. The two native dependencies (`pypdfium2`, `pikepdf`) ship pre-built wheels for macOS, Linux, and Windows — no compiler needed.

```python
import sopdf

# --- Open ---
# from a file path (near-instant thanks to lazy loading & mmap)
with sopdf.open("document.pdf") as doc:

    # --- Render ---
    img_bytes = doc[0].render(dpi=150)            # PNG bytes
    doc[0].render_to_file("page0.png", dpi=300)   # write to disk

    # parallel rendering across all pages
    images = sopdf.render_pages(doc.pages, dpi=150, parallel=True)

    # --- Extract text ---
    text = doc[0].get_text()
    blocks = doc[0].get_text_blocks()             # list[TextBlock] with bounding boxes

    # --- Search ---
    hits = doc[0].search("invoice", match_case=False)   # list[Rect]

    # --- Split & merge ---
    new_doc = doc.split(pages=[0, 1, 2], output="chapter1.pdf")
    doc.split_each(output_dir="pages/")
    sopdf.merge(["intro.pdf", "body.pdf"], output="book.pdf")

    # --- Save ---
    doc.append(new_doc)
    doc.save("out.pdf", compress=True, garbage=True)
    raw = doc.to_bytes()                          # no disk write

    # --- Rotate ---
    doc[0].rotation = 90

# --- Encrypted PDFs ---
with sopdf.open("protected.pdf", password="hunter2") as doc:
    doc.save("unlocked.pdf")                      # encryption stripped on save

# --- Open from bytes / stream ---
with open("document.pdf", "rb") as f:
    with sopdf.open(stream=f.read()) as doc:
        print(doc.page_count)

# --- Auto-repair corrupted PDFs ---
with sopdf.open("corrupted.pdf") as doc:
    doc.save("repaired.pdf")
```

---

## Features

| Capability | Examples |
|---|---|
| Open from path / bytes / stream | [01_open](examples/01_open) |
| Render pages to PNG / JPEG | [02_render](examples/02_render) |
| Batch & parallel rendering | [02_render](examples/02_render) |
| Extract plain text | [03_extract_text](examples/03_extract_text) |
| Extract text with bounding boxes | [03_extract_text](examples/03_extract_text) |
| Full-text search with hit rects | [04_search_text](examples/04_search_text) |
| Split pages into new document | [05_split](examples/05_split) |
| Merge multiple PDFs | [06_merge](examples/06_merge) |
| Save with compression | [07_save_compress](examples/07_save_compress) |
| Serialise to bytes (no disk write) | [07_save_compress](examples/07_save_compress) |
| Rotate pages | [08_rotate](examples/08_rotate) |
| Open & save encrypted PDFs | [09_decrypt](examples/09_decrypt) |
| Auto-repair corrupted PDFs | [10_repair](examples/10_repair) |

---

## License

Apache 2.0 — see [LICENSE](LICENSE).

SoPDF is free to use in personal projects, commercial products, and open-source libraries. No licensing fees, no attribution requirements beyond the standard Apache 2.0 notice.

## WeChat Group
<img src="./docs/assets/wechat.png" width="100">
