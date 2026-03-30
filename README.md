<div align="center">

# SoPDF

**The PDF processing library that belongs to everyone.**

[![PyPI version](https://img.shields.io/pypi/v/sopdf.svg)](https://pypi.org/project/sopdf/)
[![Python versions](https://img.shields.io/pypi/pyversions/sopdf.svg)](https://pypi.org/project/sopdf/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

```
pip install sopdf
```

</div>

---

## Why SoPDF?

For developers, a feature-rich open-source PDF processing library often comes with a license that is not friendly to the open-source ecosystem. If you release a product under a permissive license or contribute to a library that others can freely embed, the license can become a real obstacle. Yet high performance and comprehensive functionality are indispensable requirements for PDF processing.

**SoPDF was built to close that gap.**

Built on [`pypdfium2`](https://github.com/pypdfium2-team/pypdfium2) (Google's PDFium, for rendering & text) and [`pikepdf`](https://github.com/pikepdf/pikepdf) (libqpdf, for structure & writing), SoPDF delivers the same core capabilities under the **Apache 2.0 License** — no strings attached, no license audits, no friction. Embed it, ship it, fork it. It's yours.

Beyond its license, SoPDF is also **genuinely faster** than the incumbent alternative. Rendering is up to **1.56× faster**, plain-text extraction **2.7× faster**, and full-text search **3× faster** than PyMuPDF — all with 99% word-level accuracy parity. See [Benchmarks](#benchmarks) to verify the numbers yourself.

---

## Features

| Capability | SoPDF API |
|---|---|
| Open from path / bytes / stream | `sopdf.open()` |
| Render pages to PNG / JPEG | `page.render(dpi=300)` |
| Batch & parallel rendering | `sopdf.render_pages(pages, parallel=True)` |
| Extract plain text | `page.get_text()` |
| Extract text with bounding boxes | `page.get_text_blocks()` |
| Full-text search with hit rects | `page.search("keyword")` |
| Split pages into new document | `doc.split(pages=[0, 1, 2])` |
| Merge multiple PDFs | `sopdf.merge(["a.pdf", "b.pdf"], output="merged.pdf")` |
| Save with compression | `doc.save("out.pdf", compress=True, garbage=True)` |
| Serialise to bytes (no disk write) | `doc.to_bytes()` |
| Rotate pages | `page.rotation = 90` |
| Open & save encrypted PDFs | `sopdf.open("enc.pdf", password="secret")` |
| Auto-repair corrupted PDFs | `sopdf.open("corrupted.pdf")` |

---

## Quick Start

```python
import sopdf

# Open — near-instant thanks to lazy loading & mmap
with sopdf.open("document.pdf") as doc:
    print(f"{doc.page_count} pages  •  {doc.metadata['title']}")

    # Render page 0 at 150 DPI
    img_bytes = doc[0].render(dpi=150)           # PNG bytes
    doc[0].render_to_file("page0.png", dpi=300)  # write to disk

    # Extract text
    text = doc[0].get_text()
    blocks = doc[0].get_text_blocks()            # list[TextBlock]

    # Search
    hits = doc[0].search("invoice", match_case=False)
    for rect in hits:
        print(f"  match at {rect}")
```

### Split & Merge

```python
# Extract the first 3 pages
new_doc = doc.split(pages=[0, 1, 2], output="chapter1.pdf")

# Split every page into its own file
doc.split_each(output_dir="pages/")

# Merge a list of files
sopdf.merge(["intro.pdf", "body.pdf", "appendix.pdf"], output="book.pdf")

# Or append programmatically
doc_a.append(doc_b)
doc_a.save("combined.pdf")
```

### Render a whole document in parallel

```python
with sopdf.open("report.pdf") as doc:
    images = sopdf.render_pages(
        doc.pages,
        dpi=150,
        format="png",
        parallel=True,   # multiprocessing — bypasses GIL
    )
```

### Decrypt & save without password

```python
with sopdf.open("protected.pdf", password="hunter2") as doc:
    doc.save("unlocked.pdf")  # encryption stripped on save
```

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

## Installation

```bash
pip install sopdf
```

Requires Python 3.10+. The two native dependencies (`pypdfium2`, `pikepdf`)
ship pre-built wheels for macOS, Linux, and Windows — no compiler needed.

---

## API Reference

### `sopdf.open(path=None, password=None, *, stream=None) → Document`

| Argument | Type | Description |
|---|---|---|
| `path` | `str \| Path` | File path to the PDF |
| `password` | `str` | Password for encrypted PDFs |
| `stream` | `bytes` | Open from raw bytes instead of a file |

### `Document`

| Member | Type | Description |
|---|---|---|
| `page_count` | `int` | Total number of pages |
| `metadata` | `dict` | title, author, subject, creator, producer, dates |
| `is_encrypted` | `bool` | Whether the document is password-protected |
| `doc[i]` / `doc.load_page(i)` | `Page` | Access a page by 0-based index |
| `doc.pages` | sequence | Iterable of all pages |
| `doc.split(pages, output=None)` | `Document` | Extract a page subset |
| `doc.split_each(output_dir)` | — | Save each page as a separate file |
| `doc.append(other)` | — | Append another document's pages |
| `doc.save(path, *, compress, garbage, linearize)` | — | Save to disk |
| `doc.to_bytes(*, compress)` | `bytes` | Serialise to bytes |
| `doc.close()` | — | Release file handles |

### `Page`

| Member | Type | Description |
|---|---|---|
| `number` | `int` | 0-based page index |
| `rect` | `Rect` | Page dimensions in points |
| `rotation` | `int` | Page rotation (0 / 90 / 180 / 270) |
| `render(dpi, format, alpha)` | `bytes` | Render to PNG / JPEG |
| `render_to_file(path, dpi, format, alpha)` | — | Render and save |
| `get_text(rect=None)` | `str` | Extract plain text |
| `get_text_blocks(rect=None, format="list")` | `list` | Structured text blocks |
| `search(query, match_case=False)` | `list[Rect]` | Find text, return hit rects |
| `search_text_blocks(query, match_case=False)` | `list[dict]` | Find text with context |

### Exceptions

```python
sopdf.PDFError        # base — subclasses RuntimeError
sopdf.PasswordError   # wrong or missing password
sopdf.FileDataError   # corrupted or unreadable PDF
sopdf.PageError       # invalid page index or rotation
```

---

## License

Apache 2.0 — see [LICENSE](LICENSE).

SoPDF is free to use in personal projects, commercial products, and open-source libraries. No licensing fees, no attribution requirements beyond the standard Apache 2.0 notice.
