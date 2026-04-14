# Runtime Dependency Choice: OpenCV vs Pillow

## Why SoPDF Uses OpenCV Instead of Pillow

SoPDF uses [`opencv-python`](https://pypi.org/project/opencv-python/) as its image encoding runtime dependency, rather than the more commonly seen Pillow (PIL). This document explains the rationale and provides the benchmark evidence behind that choice.

---

## Background

PDF page rendering in SoPDF works through the following pipeline:

1. A PDF page is rasterised by **pypdfium2** (Google PDFium) into a raw bitmap buffer.
2. The bitmap buffer is converted to a Python-accessible array.
3. The array is encoded into PNG or JPEG bytes for output.

Steps 1 and 3 are where the image library comes into play. The key question is: what is the fastest way to go from a pypdfium2 bitmap to encoded image bytes?

---

## The Pillow Approach (Old)

The previous implementation used Pillow via pypdfium2's `bitmap.to_pil()` helper:

```python
bitmap = pdfium_page.render(scale=scale)   # pypdfium2 renders to BGRx bitmap
pil_image = bitmap.to_pil()               # allocates a new PIL Image (RGBA copy)
pil_image = pil_image.convert("RGB")      # another copy: RGBA → RGB
buf = io.BytesIO()
pil_image.save(buf, format="PNG")         # encodes into BytesIO
return buf.getvalue()
```

Issues with this path:
- `to_pil()` allocates a brand-new PIL `Image` object — a full memory copy.
- `.convert("RGB")` allocates yet another copy for colour space adjustment.
- `save()` writes into a `BytesIO` buffer, adding a third allocation before the final bytes are extracted.

---

## The OpenCV Approach (Current)

The current implementation uses pypdfium2's official NumPy bridge (`bitmap.to_numpy()`) and OpenCV's `cv2.imencode()`:

```python
# Render directly in 3-channel BGR — no padding byte, no extra channels
bitmap = pdfium_page.render(
    scale=scale,
    force_bitmap_format=pdfium.raw.FPDFBitmap_BGR,
)
arr = bitmap.to_numpy()              # zero-copy NumPy view of the bitmap buffer
_, encoded = cv2.imencode('.png', arr)
return bytes(encoded)
```

For PNG with alpha:
```python
bitmap = pdfium_page.render(scale=scale, maybe_alpha=True)  # BGRA
arr = bitmap.to_numpy()                                      # zero-copy view
_, encoded = cv2.imencode('.png', arr)
return bytes(encoded)
```

Advantages:
- **`force_bitmap_format=FPDFBitmap_BGR`** renders the page directly in 3-channel BGR — the native format of OpenCV — eliminating any channel reordering or padding removal.
- **`bitmap.to_numpy()`** is zero-copy: the returned NumPy array shares memory with pypdfium2's internal bitmap buffer. No pixel data is duplicated.
- **`cv2.imencode()`** is a highly optimised C++ routine that encodes PNG/JPEG directly from the NumPy array without intermediate Python objects or extra allocations.

This is also the approach recommended by the pypdfium2 project itself for OpenCV integration.

---

## Benchmark Results

Measured on Apple M-series (arm64, 10-core), Python 3.12, against a 50-page PDF fixture.

### Single-page rendering

| Scenario | Pillow | OpenCV | Speedup |
|---|---|---|---|
| Render 1 page @ 72 DPI  | 6.6 ms  | 4.1 ms  | **1.61× faster** |
| Render 1 page @ 150 DPI | 20.0 ms | 11.7 ms | **1.71× faster** |
| Render 1 page @ 300 DPI | 64.6 ms | 34.2 ms | **1.89× faster** |

### Full-document rendering (50 pages @ 150 DPI)

| Scenario | Pillow | OpenCV | Speedup |
|---|---|---|---|
| Sequential rendering | 966.9 ms | 543 ms | **1.78× faster** |
| Parallel rendering   | 410.7 ms | 418 ms | ≈ parity |

The speedup widens with resolution because a larger pixel buffer amplifies the cost of memory allocations and copies in the Pillow path.

Parallel performance is essentially identical because the bottleneck there is process spawn overhead and IPC, not image encoding.

---

## Summary

| Criterion | Pillow | OpenCV |
|---|---|---|
| Array conversion | Allocates new Image (full copy) | Zero-copy NumPy view |
| Channel handling | Python-level `.convert()` call | Eliminated via `force_bitmap_format` |
| Encoding | `save()` + `BytesIO` + `getvalue()` | `cv2.imencode()` direct |
| pypdfium2 official support | ✅ (`to_pil()`) | ✅ (`to_numpy()`) |
| Rendering speedup vs Pillow | — | **1.6× – 1.9× faster** |

OpenCV eliminates redundant copies at every stage of the post-rendering pipeline. For a library whose primary value proposition is rendering performance, this makes it the right choice.
