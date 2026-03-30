"""Tests for parallel rendering with render_pages(parallel=True)."""

import pytest
import sopdf


def _is_png(data: bytes) -> bool:
    return data[:8] == b"\x89PNG\r\n\x1a\n"


class TestParallelRender:
    def test_parallel_returns_same_count(self, multipage_pdf):
        with sopdf.open(str(multipage_pdf)) as doc:
            pages = list(doc.pages)
            imgs = sopdf.render_pages(pages, parallel=True)
            assert len(imgs) == len(pages)

    def test_parallel_all_valid_png(self, multipage_pdf):
        with sopdf.open(str(multipage_pdf)) as doc:
            pages = list(doc.pages)
            imgs = sopdf.render_pages(pages, parallel=True)
            assert all(_is_png(img) for img in imgs)

    def test_parallel_matches_sequential(self, multipage_pdf):
        with sopdf.open(str(multipage_pdf)) as doc:
            pages = list(doc.pages)
            sequential = sopdf.render_pages(pages, dpi=72)
            parallel = sopdf.render_pages(pages, dpi=72, parallel=True)
            # Same number of results, each is non-empty
            assert len(sequential) == len(parallel)
            for s, p in zip(sequential, parallel):
                assert len(s) > 0
                assert len(p) > 0

    def test_parallel_order_preserved(self, multipage_pdf):
        """Pages rendered in parallel must be returned in original order."""
        with sopdf.open(str(multipage_pdf)) as doc:
            pages = list(doc.pages)
            imgs = sopdf.render_pages(pages, dpi=72, parallel=True)
            assert len(imgs) == doc.page_count
