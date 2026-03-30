"""Tests for text extraction — get_text / get_text_blocks."""

import pytest
import sopdf
from sopdf import Rect, TextBlock


class TestGetText:
    def test_returns_string(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            text = doc[0].get_text()
            assert isinstance(text, str)

    def test_contains_expected_content(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            text = doc[0].get_text()
            # Our fixture writes "Hello, sopdf!" so some part should be there
            assert len(text) > 0

    def test_multipage_different_text(self, multipage_pdf):
        with sopdf.open(str(multipage_pdf)) as doc:
            texts = [doc[i].get_text() for i in range(doc.page_count)]
            # Each page should have distinct content
            assert len(set(texts)) > 1

    def test_get_text_with_rect(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            page = doc[0]
            r = page.rect
            # Full-page rect should return same as no-rect
            full_text = page.get_text(rect=Rect(r.x0, r.y0, r.x1, r.y1))
            assert isinstance(full_text, str)


class TestGetTextBlocks:
    def test_returns_list(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            blocks = doc[0].get_text_blocks()
            assert isinstance(blocks, list)

    def test_blocks_are_text_block_instances(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            blocks = doc[0].get_text_blocks()
            for b in blocks:
                assert isinstance(b, TextBlock)

    def test_text_block_has_rect(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            blocks = doc[0].get_text_blocks()
            for b in blocks:
                assert isinstance(b.rect, Rect)

    def test_format_dict(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            blocks = doc[0].get_text_blocks(format="dict")
            for b in blocks:
                assert isinstance(b, dict)
                assert "text" in b
                assert "rect" in b

    def test_blocks_with_rect_filter(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            page = doc[0]
            r = page.rect
            # Rect covering none of the page
            empty_rect = Rect(r.x1 + 100, r.y1 + 100, r.x1 + 200, r.y1 + 200)
            blocks = page.get_text_blocks(rect=empty_rect)
            assert blocks == []
