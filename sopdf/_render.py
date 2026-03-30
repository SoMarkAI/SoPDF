"""
sopdf batch rendering — sequential and parallel.
"""

from __future__ import annotations

import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from ._page import Page

from ._utils import _render_batch, _render_one


def render_pages(
    pages: list["Page"],
    *,
    dpi: int = 72,
    format: str = "png",
    alpha: bool = False,
    parallel: bool = False,
) -> list[bytes]:
    """Render a list of pages, returning a list of encoded image bytes.

    Parameters
    ----------
    pages:
        List of :class:`~sopdf.Page` objects.
    dpi:
        Resolution. Default 72.
    format:
        ``"png"`` or ``"jpeg"``.
    alpha:
        Include alpha channel (PNG only).
    parallel:
        Use :mod:`multiprocessing` for faster CPU-bound rendering.
        Pages are batched across workers to minimise process-spawn and
        inter-process data-transfer overhead.
    """
    if not parallel:
        return [p.render(dpi=dpi, format=format, alpha=alpha) for p in pages]

    n_workers = min(len(pages), os.cpu_count() or 4)
    args_list = _build_batch_args(pages, dpi, format, alpha, n_workers)
    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        batch_results = list(executor.map(_render_batch, args_list))

    # Re-assemble in original page order
    # Each batch_results[i] is a list of bytes for that chunk's pages.
    result_map: dict[int, bytes] = {}
    for (_, page_indices, *_rest), page_bytes in zip(args_list, batch_results):
        for idx, data in zip(page_indices, page_bytes):
            result_map[idx] = data
    return [result_map[p._index] for p in pages]


def render_pages_to_files(
    pages: list["Page"],
    output_dir: Union[str, Path],
    *,
    dpi: int = 72,
    format: str = "png",
    alpha: bool = False,
    parallel: bool = False,
) -> None:
    """Render pages and write them to *output_dir* as ``page_0.png``, ``page_1.png``, …"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    ext = "jpg" if format.lower() == "jpeg" else "png"

    images = render_pages(pages, dpi=dpi, format=format, alpha=alpha, parallel=parallel)
    for i, data in enumerate(images):
        (output_dir / f"page_{i}.{ext}").write_bytes(data)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_args(
    pages: list["Page"],
    dpi: int,
    format: str,
    alpha: bool,
) -> list[tuple]:
    """Build pickle-safe argument tuples for *_render_one* workers.

    Serialises stream-backed documents once per Document object rather than
    once per page, avoiding redundant pikepdf serialisation.
    """
    # Deduplicate: compute source once per distinct document object.
    # Prefer the file path (string) or original stream bytes over a fresh
    # pikepdf serialisation — avoids triggering lazy pikepdf load for
    # read-only parallel render workflows.
    _source_cache: dict[int, object] = {}

    def _source(doc) -> object:
        doc_id = id(doc)
        if doc_id not in _source_cache:
            if doc._source is not None:
                _source_cache[doc_id] = doc._source          # file path
            elif doc._stream is not None and not doc._dirty:
                _source_cache[doc_id] = doc._stream          # original bytes
            else:
                _source_cache[doc_id] = doc.to_bytes()       # pikepdf serialise
        return _source_cache[doc_id]

    return [(_source(p._doc), p._index, dpi, format, alpha) for p in pages]


def _build_batch_args(
    pages: list["Page"],
    dpi: int,
    format: str,
    alpha: bool,
    n_workers: int,
) -> list[tuple]:
    """Build batched argument tuples for *_render_batch* workers.

    Groups pages by document, then distributes each document's pages across
    *n_workers* chunks so that each worker opens the document once and renders
    multiple pages — greatly reducing per-process overhead.
    """
    # Group page indices by document
    from collections import defaultdict

    _source_cache: dict[int, object] = {}
    doc_pages: dict[int, list] = defaultdict(list)  # doc_id → [page_obj, …]

    for page in pages:
        doc = page._doc
        doc_id = id(doc)
        if doc_id not in _source_cache:
            if doc._source is not None:
                _source_cache[doc_id] = doc._source
            elif doc._stream is not None and not doc._dirty:
                _source_cache[doc_id] = doc._stream
            else:
                _source_cache[doc_id] = doc.to_bytes()
        doc_pages[doc_id].append(page)

    # Build chunks: interleave pages across workers to balance load
    # (round-robin assignment of pages within each document)
    chunks: list[tuple[object, list[int]]] = []
    for doc_id, doc_page_list in doc_pages.items():
        source = _source_cache[doc_id]
        n = min(n_workers, len(doc_page_list))
        # Assign page i to worker bucket i % n
        buckets: list[list[int]] = [[] for _ in range(n)]
        for i, page in enumerate(doc_page_list):
            buckets[i % n].append(page._index)
        for bucket in buckets:
            if bucket:
                chunks.append((source, bucket, dpi, format, alpha))

    return chunks
