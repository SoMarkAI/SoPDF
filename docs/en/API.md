# SoPDF API Reference

## Table of Contents

- [Top-Level Functions](#top-level-functions)
  - [open()](#sopdfopenpath-password-stream)
  - [merge()](#sopdfmergeinputs-output)
  - [render\_pages()](#sopdfrender_pagespages-dpi-format-alpha-parallel)
  - [render\_pages\_to\_files()](#sopdfrender_pages_to_filespages-output_dir-dpi-format-alpha-parallel)
- [Document](#document)
  - [Properties](#document-properties)
  - [Page Access](#page-access)
  - [Split](#split)
  - [Merge](#merge)
  - [Save](#save)
  - [Lifecycle](#lifecycle)
- [Page](#page)
  - [Properties](#page-properties)
  - [Rendering](#rendering)
  - [Text Extraction](#text-extraction)
  - [Text Search](#text-search)
- [Data Types](#data-types)
  - [Rect](#rect)
  - [TextBlock](#textblock)
- [Exceptions](#exceptions)

---

## Top-Level Functions

### `sopdf.open(path, password, *, stream)`

Opens a PDF document and returns a `Document` instance.

```python
sopdf.open(
    path: str | pathlib.Path | None = None,
    password: str | None = None,
    *,
    stream: bytes | None = None,
) -> Document
```

**Parameters**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `path` | `str \| Path \| None` | `None` | File-system path to the PDF. Mutually exclusive with `stream`. |
| `password` | `str \| None` | `None` | Password for encrypted PDFs. Pass `None` if no password is required. |
| `stream` | `bytes \| None` | `None` | Open from raw bytes in memory instead of a file. Mutually exclusive with `path`. |

**Returns**

`Document` — The opened document object.

**Exceptions**

| Exception | Condition |
|---|---|
| `PasswordError` | The document requires a password that was not provided or is incorrect. |
| `FileDataError` | The file is corrupted or cannot be parsed as a valid PDF. |

**Examples**

```python
# Open from a file path
doc = sopdf.open("report.pdf")

# Open an encrypted document
doc = sopdf.open("secure.pdf", password="hunter2")

# Open from raw bytes in memory
with open("report.pdf", "rb") as f:
    doc = sopdf.open(stream=f.read())

# Recommended: use a context manager for automatic resource cleanup
with sopdf.open("report.pdf") as doc:
    print(doc.page_count)
```

---

### `sopdf.merge(inputs, output)`

Merges multiple PDF files into a single output file, in the order provided.

```python
sopdf.merge(
    inputs: list[str | pathlib.Path],
    output: str | pathlib.Path,
) -> None
```

**Parameters**

| Parameter | Type | Description |
|---|---|---|
| `inputs` | `list[str \| Path]` | Ordered list of PDF file paths to concatenate. |
| `output` | `str \| Path` | Destination file path for the merged PDF. |

**Exceptions**

| Exception | Condition |
|---|---|
| `ValueError` | `inputs` list is empty. |
| `PasswordError` | One of the input files requires a password. |
| `FileDataError` | One of the input files cannot be read. |

**Examples**

```python
sopdf.merge(
    ["intro.pdf", "body.pdf", "appendix.pdf"],
    output="book.pdf",
)
```

---

### `sopdf.render_pages(pages, *, dpi, format, alpha, parallel)`

Renders a list of pages to encoded image bytes.

```python
sopdf.render_pages(
    pages: list[Page],
    *,
    dpi: int = 72,
    format: str = "png",
    alpha: bool = False,
    parallel: bool = False,
) -> list[bytes]
```

**Parameters**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `pages` | `list[Page]` | — | List of page objects to render, typically from `doc.pages`. |
| `dpi` | `int` | `72` | Rendering resolution in dots per inch. Common values: 72 (screen preview), 150 (high quality), 300 (print quality). |
| `format` | `str` | `"png"` | Output image format: `"png"` or `"jpeg"`. |
| `alpha` | `bool` | `False` | Whether to include an alpha (transparency) channel. Only effective for PNG. |
| `parallel` | `bool` | `False` | Whether to use multiprocessing for rendering. Bypasses the GIL for significant speedup on multi-core machines. |

**Returns**

`list[bytes]` — A list of encoded image bytes, one entry per page, in the same order as `pages`.

**Examples**

```python
with sopdf.open("report.pdf") as doc:
    # Sequential rendering
    images = sopdf.render_pages(doc.pages, dpi=150)

    # Parallel rendering with multiprocessing (recommended for large documents)
    images = sopdf.render_pages(doc.pages, dpi=300, parallel=True)
```

---

### `sopdf.render_pages_to_files(pages, output_dir, *, dpi, format, alpha, parallel)`

Renders pages and writes the results to a directory as `page_0.png`, `page_1.png`, etc.

```python
sopdf.render_pages_to_files(
    pages: list[Page],
    output_dir: str | pathlib.Path,
    *,
    dpi: int = 72,
    format: str = "png",
    alpha: bool = False,
    parallel: bool = False,
) -> None
```

**Parameters**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `pages` | `list[Page]` | — | List of page objects to render. |
| `output_dir` | `str \| Path` | — | Output directory path. Created automatically if it does not exist. |
| `dpi` | `int` | `72` | Rendering resolution in dots per inch. |
| `format` | `str` | `"png"` | Output image format: `"png"` or `"jpeg"`. |
| `alpha` | `bool` | `False` | Whether to include an alpha channel (PNG only). |
| `parallel` | `bool` | `False` | Whether to use multiprocessing for rendering. |

**Examples**

```python
with sopdf.open("report.pdf") as doc:
    sopdf.render_pages_to_files(doc.pages, "output/", dpi=150, parallel=True)
# Produces: output/page_0.png, output/page_1.png, ...
```

---

## Document

`Document` represents an open PDF document. It should never be constructed directly — always obtain one via `sopdf.open()`.

---

### Document Properties

#### `page_count`

```python
doc.page_count -> int
```

The total number of pages in the document (read-only).

---

#### `metadata`

```python
doc.metadata -> dict
```

Document metadata dictionary (read-only). Keys are lowercase strings. Possible fields:

| Key | Type | Description |
|---|---|---|
| `"title"` | `str` | Document title. |
| `"author"` | `str` | Author name. |
| `"subject"` | `str` | Document subject. |
| `"creator"` | `str` | Application that created the document. |
| `"producer"` | `str` | Tool that produced the PDF. |
| `"creation_date"` | `str` | Creation date. |
| `"mod_date"` | `str` | Last modification date. |

Some fields may be absent depending on the document.

---

#### `is_encrypted`

```python
doc.is_encrypted -> bool
```

Whether the document is password-protected (read-only). Returns `True` even when the correct password has been provided and the document opened successfully.

---

#### `pages`

```python
doc.pages -> _PageList
```

Lazy sequence of all pages (read-only). Supports iteration and slicing. Commonly used with `render_pages()`.

---

### Page Access

#### `doc[index]` / `doc.load_page(index)`

```python
doc[index: int] -> Page
doc.load_page(index: int) -> Page
```

Retrieves a page by 0-based index. Negative indices are supported (`doc[-1]` returns the last page).

**Exceptions**

| Exception | Condition |
|---|---|
| `PageError` | Index is out of range. |

**Examples**

```python
first_page = doc[0]
last_page  = doc[-1]
third_page = doc.load_page(2)
```

---

#### `len(doc)`

```python
len(doc) -> int
```

Equivalent to `doc.page_count`.

---

#### Iteration

```python
for page in doc:
    print(page.number)
```

---

### Split

#### `doc.split(pages, output)`

```python
doc.split(
    pages: list[int],
    output: str | pathlib.Path | None = None,
) -> Document
```

Extracts specified pages from the current document and returns a new `Document` object.

**Parameters**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `pages` | `list[int]` | — | List of 0-based page indices to extract. The output order matches the list order. |
| `output` | `str \| Path \| None` | `None` | If provided, the new document is also written to this path. Otherwise, it is returned in memory only. |

**Returns**

`Document` — A new document containing the specified pages.

**Examples**

```python
# Extract the first 3 pages and save to disk
chapter = doc.split(pages=[0, 1, 2], output="chapter1.pdf")

# Extract to memory only, no disk write
excerpt = doc.split(pages=[4, 5, 6])
```

---

#### `doc.split_each(output_dir)`

```python
doc.split_each(output_dir: str | pathlib.Path) -> None
```

Saves each page as a separate PDF file. Files are named `page_0.pdf`, `page_1.pdf`, etc.

**Parameters**

| Parameter | Type | Description |
|---|---|---|
| `output_dir` | `str \| Path` | Output directory path. Created automatically if it does not exist. |

**Examples**

```python
doc.split_each("pages/")
# Produces: pages/page_0.pdf, pages/page_1.pdf, ...
```

---

### Merge

#### `doc.append(other)`

```python
doc.append(other: Document) -> None
```

Appends all pages of another document to the end of this document. After calling this method, the document is marked as modified and must be saved via `save()` or `to_bytes()` to persist the change.

**Parameters**

| Parameter | Type | Description |
|---|---|---|
| `other` | `Document` | The document whose pages will be appended. |

**Examples**

```python
with sopdf.open("part1.pdf") as doc_a, sopdf.open("part2.pdf") as doc_b:
    doc_a.append(doc_b)
    doc_a.save("combined.pdf")
```

---

### Save

#### `doc.save(path, *, compress, garbage, linearize)`

```python
doc.save(
    path: str | pathlib.Path,
    *,
    compress: bool = True,
    garbage: bool = False,
    linearize: bool = False,
) -> None
```

Writes the document to disk.

**Parameters**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `path` | `str \| Path` | — | Destination file path. |
| `compress` | `bool` | `True` | Whether to compress content streams. Can significantly reduce file size. |
| `garbage` | `bool` | `False` | Whether to generate object streams for additional structural compression. |
| `linearize` | `bool` | `False` | Whether to linearize the PDF for optimized sequential network access (Fast Web View). |

**Examples**

```python
# Basic save (compression enabled by default)
doc.save("output.pdf")

# Maximum compression
doc.save("output.pdf", compress=True, garbage=True)

# Strip encryption (open with the correct password, then save)
doc.save("unlocked.pdf")
```

---

#### `doc.to_bytes(*, compress)`

```python
doc.to_bytes(compress: bool = True) -> bytes
```

Serializes the document to bytes without writing to disk. Useful for in-memory processing or serving a PDF over a network.

**Parameters**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `compress` | `bool` | `True` | Whether to compress content streams. |

**Returns**

`bytes` — The complete PDF file contents as bytes.

**Examples**

```python
pdf_bytes = doc.to_bytes()

# Return directly as a Flask HTTP response
from flask import Response
return Response(doc.to_bytes(), mimetype="application/pdf")
```

---

### Lifecycle

#### `doc.close()`

```python
doc.close() -> None
```

Closes the document and releases all file handles and memory resources. Using a `with` statement is recommended over calling this directly.

---

#### Context Manager

```python
with sopdf.open("file.pdf") as doc:
    ...
# close() is called automatically on exit
```

---

## Page

`Page` represents a single page within a document. Obtained via `doc[i]` or `doc.load_page(i)` — never constructed directly.

---

### Page Properties

#### `number`

```python
page.number -> int
```

The 0-based index of this page (read-only).

---

#### `rect`

```python
page.rect -> Rect
```

The page dimensions as a `Rect` in PDF points (1 pt = 1/72 inch) (read-only). Use `rect.width` and `rect.height` to get the page size.

---

#### `rotation`

```python
page.rotation -> int          # read current rotation
page.rotation = degrees: int  # set rotation
```

The page rotation in degrees. Must be one of `0`, `90`, `180`, `270` (read/write).

**Exceptions**

| Exception | Condition |
|---|---|
| `PageError` | Set to a value other than 0, 90, 180, or 270. |

---

### Rendering

#### `page.render(*, dpi, format, alpha)`

```python
page.render(
    *,
    dpi: int = 72,
    format: str = "png",
    alpha: bool = False,
) -> bytes
```

Renders the page to encoded image bytes.

**Parameters**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `dpi` | `int` | `72` | Rendering resolution in dots per inch. Use 72 for screen preview, 300 for print quality. |
| `format` | `str` | `"png"` | Output image format: `"png"` or `"jpeg"`. |
| `alpha` | `bool` | `False` | Whether to include an alpha (transparency) channel. Only effective for PNG; JPEG does not support transparency. |

**Returns**

`bytes` — Encoded image bytes (PNG or JPEG).

**Examples**

```python
png_bytes  = page.render(dpi=150)
jpeg_bytes = page.render(dpi=150, format="jpeg")
png_alpha  = page.render(dpi=72, alpha=True)
```

---

#### `page.render_to_file(path, *, dpi, format, alpha)`

```python
page.render_to_file(
    path: str | pathlib.Path,
    *,
    dpi: int = 72,
    format: str = "png",
    alpha: bool = False,
) -> None
```

Renders the page and writes the image to a file. Parameters are identical to `render()`.

**Parameters**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `path` | `str \| Path` | — | Output file path (including extension). |
| `dpi` | `int` | `72` | Rendering resolution in dots per inch. |
| `format` | `str` | `"png"` | Output image format: `"png"` or `"jpeg"`. |
| `alpha` | `bool` | `False` | Whether to include an alpha channel (PNG only). |

**Examples**

```python
page.render_to_file("page0.png", dpi=300)
page.render_to_file("page0.jpg", dpi=150, format="jpeg")
```

---

### Text Extraction

#### `page.get_text(*, rect)`

```python
page.get_text(
    *,
    rect: Rect | None = None,
) -> str
```

Extracts plain text from the page.

**Parameters**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `rect` | `Rect \| None` | `None` | Restrict extraction to this rectangular region. Extracts the full page when `None`. |

**Returns**

`str` — The extracted plain text.

**Examples**

```python
full_text = page.get_text()

# Extract from a specific region only
region = Rect(0, 0, 300, 100)
header_text = page.get_text(rect=region)
```

---

#### `page.get_text_blocks(*, rect, format)`

```python
page.get_text_blocks(
    *,
    rect: Rect | None = None,
    format: str = "list",
) -> list
```

Extracts structured text blocks with bounding boxes.

**Parameters**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `rect` | `Rect \| None` | `None` | Restrict extraction to this rectangular region. Extracts the full page when `None`. |
| `format` | `str` | `"list"` | Return format. `"list"` returns a list of `TextBlock` objects; `"dict"` returns a list of plain dictionaries with `"text"` and `"rect"` keys. |

**Returns**

- When `format="list"`: `list[TextBlock]`
- When `format="dict"`: `list[dict]`, each of the form `{"text": "...", "rect": {"x0": ..., "y0": ..., "x1": ..., "y1": ...}}`

**Examples**

```python
blocks = page.get_text_blocks()
for block in blocks:
    print(block.text, block.rect)

# Return as dictionaries (convenient for JSON serialization)
dicts = page.get_text_blocks(format="dict")
```

---

### Text Search

#### `page.search(query, *, match_case)`

```python
page.search(
    query: str,
    *,
    match_case: bool = False,
) -> list[Rect]
```

Searches the page for a text string and returns the bounding rectangles of all matches.

**Parameters**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `query` | `str` | — | The text string to search for. |
| `match_case` | `bool` | `False` | Whether the search is case-sensitive. Case-insensitive by default. |

**Returns**

`list[Rect]` — Bounding rectangles for each match. Returns an empty list if no matches are found.

**Examples**

```python
hits = page.search("invoice")
for rect in hits:
    print(f"Match at {rect}")

# Case-sensitive search
hits = page.search("PDF", match_case=True)
```

---

#### `page.search_text_blocks(query, *, match_case)`

```python
page.search_text_blocks(
    query: str,
    *,
    match_case: bool = False,
) -> list[dict]
```

Searches for text and returns each match along with the surrounding text block for context.

**Parameters**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `query` | `str` | — | The text string to search for. |
| `match_case` | `bool` | `False` | Whether the search is case-sensitive. |

**Returns**

`list[dict]` — Each element is a dictionary with the following keys:

| Key | Type | Description |
|---|---|---|
| `"text"` | `str` | Full text content of the block containing the match. |
| `"rect"` | `Rect` | Bounding rectangle of the containing text block. |
| `"match_rect"` | `Rect` | Precise bounding rectangle of the matched keyword itself. |

**Examples**

```python
results = page.search_text_blocks("total amount")
for r in results:
    print(r["text"])        # full paragraph containing the keyword
    print(r["match_rect"])  # exact position of the keyword
```

---

## Data Types

### Rect

Represents a rectangular region. Coordinates are in PDF points (pt, where 1 pt = 1/72 inch). The coordinate system has its origin at the top-left corner of the page, with x increasing rightward and y increasing downward.

```python
Rect(x0: float, y0: float, x1: float, y1: float)
```

**Constructor Parameters**

| Parameter | Type | Description |
|---|---|---|
| `x0` | `float` | Left edge (x-coordinate of the top-left corner). |
| `y0` | `float` | Top edge (y-coordinate of the top-left corner). |
| `x1` | `float` | Right edge (x-coordinate of the bottom-right corner). |
| `y1` | `float` | Bottom edge (y-coordinate of the bottom-right corner). |

**Properties**

| Property | Type | Description |
|---|---|---|
| `x0` | `float` | Left edge. |
| `y0` | `float` | Top edge. |
| `x1` | `float` | Right edge. |
| `y1` | `float` | Bottom edge. |
| `width` | `float` | Rectangle width, equal to `x1 - x0`. |
| `height` | `float` | Rectangle height, equal to `y1 - y0`. |
| `is_valid` | `bool` | `True` when `x0 ≤ x1` and `y0 ≤ y1`. |
| `is_empty` | `bool` | `True` when the rectangle has zero area. |

**Methods**

| Method | Returns | Description |
|---|---|---|
| `get_area()` | `float` | Rectangle area. Returns `0` for invalid rectangles. |
| `contains(other)` | `bool` | If `other` is a `Rect`, returns `True` if it is fully contained. If `other` is an `(x, y)` tuple, returns `True` if the point is inside. |
| `intersects(other)` | `bool` | Returns `True` if the two rectangles overlap (touching edges count). |
| `intersect(other)` | `Rect` | Returns the intersection region. Returns an empty `Rect` if there is no overlap. |
| `include_rect(other)` | `Rect` | Returns the smallest bounding rectangle that contains both rectangles. |
| `include_point(x, y)` | `Rect` | Returns a new rectangle expanded to include the given point. |

All geometric operations return new `Rect` instances — the original is immutable.

**Examples**

```python
r = Rect(10, 20, 200, 300)
print(r.width)    # 190.0
print(r.height)   # 280.0

# Containment check
print(r.contains(Rect(50, 50, 100, 100)))  # True
print(r.contains((50, 50)))                # True (point)

# Intersection
a = Rect(0, 0, 100, 100)
b = Rect(50, 50, 150, 150)
print(a.intersect(b))  # Rect(50, 50, 100, 100)

# Unpack
x0, y0, x1, y1 = r
```

---

### TextBlock

Represents a single block of text on a page, together with its bounding box.

```python
TextBlock(text: str, rect: Rect)
```

**Attributes**

| Attribute | Type | Description |
|---|---|---|
| `text` | `str` | The text content of the block. |
| `rect` | `Rect` | Bounding rectangle of the block on the page. |

**Methods**

| Method | Returns | Description |
|---|---|---|
| `to_dict()` | `dict` | Converts to a dictionary with `"text"` and `"rect"` keys, where `"rect"` is a dict with `"x0"`, `"y0"`, `"x1"`, `"y1"` keys. |

**Examples**

```python
blocks = page.get_text_blocks()
for block in blocks:
    print(block.text)
    print(block.rect.width, block.rect.height)
    print(block.to_dict())
```

---

## Exceptions

All exceptions inherit from `PDFError`, which inherits from the built-in `RuntimeError`.

```
RuntimeError
└── PDFError
    ├── PasswordError
    ├── FileDataError
    └── PageError
```

| Exception | When Raised |
|---|---|
| `PDFError` | Base class for all sopdf exceptions. Catch this to handle any sopdf error. |
| `PasswordError` | Opening an encrypted PDF with a missing or incorrect password. |
| `FileDataError` | PDF file is corrupted, has an invalid format, or cannot be parsed. |
| `PageError` | Page index is out of range, or rotation is set to an invalid value (not 0/90/180/270). |

**Examples**

```python
import sopdf

try:
    doc = sopdf.open("file.pdf", password="wrong")
except sopdf.PasswordError:
    print("Incorrect password")
except sopdf.FileDataError:
    print("File is corrupted")
except sopdf.PDFError as e:
    print(f"PDF error: {e}")
```
