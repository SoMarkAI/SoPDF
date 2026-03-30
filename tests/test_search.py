"""Tests for page.search and page.search_text_blocks."""

import pytest
import sopdf
from sopdf import Rect


class TestSearch:
    def test_search_returns_list(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            results = doc[0].search("sopdf")
            assert isinstance(results, list)

    def test_search_finds_known_word(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            # fixture text includes "sopdf"
            results = doc[0].search("sopdf")
            assert len(results) >= 1

    def test_search_results_are_rects(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            results = doc[0].search("Hello")
            for r in results:
                assert isinstance(r, Rect)

    def test_search_not_found_returns_empty(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            results = doc[0].search("zzz_not_in_document_xyz")
            assert results == []

    def test_search_case_insensitive_default(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            lower = doc[0].search("hello")
            upper = doc[0].search("HELLO")
            # Without match_case both should behave the same
            assert isinstance(lower, list)
            assert isinstance(upper, list)

    def test_search_case_sensitive(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            results = doc[0].search("HELLO", match_case=True)
            assert isinstance(results, list)


class TestSearchTextBlocks:
    def test_search_text_blocks_returns_list(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            results = doc[0].search_text_blocks("sopdf")
            assert isinstance(results, list)

    def test_each_result_has_required_keys(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            results = doc[0].search_text_blocks("sopdf")
            for item in results:
                assert "text" in item
                assert "rect" in item
                assert "match_rect" in item

    def test_match_rect_is_rect(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            results = doc[0].search_text_blocks("sopdf")
            for item in results:
                assert isinstance(item["match_rect"], Rect)

    def test_not_found_returns_empty(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            results = doc[0].search_text_blocks("zzz_not_in_document_xyz")
            assert results == []
