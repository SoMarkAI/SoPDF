"""Tests for sopdf.Outline / OutlineItem — empty, single-level, multi-level tree."""

import pytest
import sopdf
from sopdf import Outline, OutlineItem


class TestOutlineType:
    def test_outline_is_outline_object(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            assert isinstance(doc.outline, Outline)

    def test_same_object_on_repeated_access(self, outline_pdf):
        with sopdf.open(str(outline_pdf)) as doc:
            assert doc.outline is doc.outline

    def test_repr_contains_outline(self, outline_pdf):
        with sopdf.open(str(outline_pdf)) as doc:
            r = repr(doc.outline)
            assert "Outline" in r


class TestEmptyOutline:
    def test_simple_pdf_has_no_outline(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            assert len(doc.outline) == 0

    def test_empty_outline_is_falsy(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            assert not doc.outline

    def test_empty_items_is_empty_list(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            assert doc.outline.items == []

    def test_empty_to_list(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            assert doc.outline.to_list() == []

    def test_empty_iteration(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            items = list(doc.outline)
            assert items == []


class TestOutlineStructure:
    def test_outline_is_truthy(self, outline_pdf):
        with sopdf.open(str(outline_pdf)) as doc:
            assert bool(doc.outline)

    def test_top_level_count(self, outline_pdf):
        # outline.pdf has 2 top-level chapters
        with sopdf.open(str(outline_pdf)) as doc:
            assert len(doc.outline.items) == 2

    def test_total_node_count(self, outline_pdf):
        # Chapter 1 + Chapter 2 + Section 2.1 + Section 2.2 = 4 total
        with sopdf.open(str(outline_pdf)) as doc:
            assert len(doc.outline) == 4

    def test_top_level_titles(self, outline_pdf):
        with sopdf.open(str(outline_pdf)) as doc:
            titles = [item.title for item in doc.outline.items]
            assert titles == ["Chapter 1", "Chapter 2"]

    def test_chapter1_has_no_children(self, outline_pdf):
        with sopdf.open(str(outline_pdf)) as doc:
            ch1 = doc.outline.items[0]
            assert len(ch1.children) == 0

    def test_chapter2_has_two_children(self, outline_pdf):
        with sopdf.open(str(outline_pdf)) as doc:
            ch2 = doc.outline.items[1]
            assert len(ch2.children) == 2

    def test_section_titles(self, outline_pdf):
        with sopdf.open(str(outline_pdf)) as doc:
            ch2 = doc.outline.items[1]
            child_titles = [c.title for c in ch2.children]
            assert child_titles == ["Section 2.1", "Section 2.2"]

    def test_page_indices(self, outline_pdf):
        with sopdf.open(str(outline_pdf)) as doc:
            items = doc.outline.items
            assert items[0].page == 0   # Chapter 1 → page 0
            assert items[1].page == 1   # Chapter 2 → page 1
            ch2 = items[1]
            assert ch2.children[0].page == 2  # Section 2.1 → page 2
            assert ch2.children[1].page == 3  # Section 2.2 → page 3

    def test_level_values(self, outline_pdf):
        with sopdf.open(str(outline_pdf)) as doc:
            items = doc.outline.items
            assert items[0].level == 0
            assert items[1].level == 0
            assert items[1].children[0].level == 1
            assert items[1].children[1].level == 1


class TestOutlineItem:
    def test_outline_item_is_frozen(self, outline_pdf):
        with sopdf.open(str(outline_pdf)) as doc:
            item = doc.outline.items[0]
            with pytest.raises((AttributeError, TypeError)):
                item.title = "modified"  # type: ignore[misc]

    def test_outline_item_to_dict(self, outline_pdf):
        with sopdf.open(str(outline_pdf)) as doc:
            item = doc.outline.items[1]
            d = item.to_dict()
            assert d["title"] == "Chapter 2"
            assert d["page"] == 1
            assert d["level"] == 0
            assert len(d["children"]) == 2

    def test_outline_item_repr(self, outline_pdf):
        with sopdf.open(str(outline_pdf)) as doc:
            r = repr(doc.outline.items[1])
            assert "OutlineItem" in r
            assert "Chapter 2" in r

    def test_item_is_outlineitem_instance(self, outline_pdf):
        with sopdf.open(str(outline_pdf)) as doc:
            for item in doc.outline:
                assert isinstance(item, OutlineItem)


class TestOutlineToList:
    def test_to_list_length(self, outline_pdf):
        with sopdf.open(str(outline_pdf)) as doc:
            flat = doc.outline.to_list()
            assert len(flat) == len(doc.outline)

    def test_to_list_order(self, outline_pdf):
        # DFS order: Chapter 1, Chapter 2, Section 2.1, Section 2.2
        with sopdf.open(str(outline_pdf)) as doc:
            flat = doc.outline.to_list()
            assert flat[0]["title"] == "Chapter 1"
            assert flat[1]["title"] == "Chapter 2"
            assert flat[2]["title"] == "Section 2.1"
            assert flat[3]["title"] == "Section 2.2"

    def test_to_list_levels(self, outline_pdf):
        with sopdf.open(str(outline_pdf)) as doc:
            flat = doc.outline.to_list()
            assert flat[0]["level"] == 0
            assert flat[1]["level"] == 0
            assert flat[2]["level"] == 1
            assert flat[3]["level"] == 1

    def test_to_list_dict_keys(self, outline_pdf):
        with sopdf.open(str(outline_pdf)) as doc:
            flat = doc.outline.to_list()
            for entry in flat:
                assert set(entry.keys()) == {"level", "title", "page"}

    def test_to_list_pages(self, outline_pdf):
        with sopdf.open(str(outline_pdf)) as doc:
            flat = doc.outline.to_list()
            pages = [e["page"] for e in flat]
            assert pages == [0, 1, 2, 3]


class TestOutlineIteration:
    def test_iteration_gives_top_level_items(self, outline_pdf):
        with sopdf.open(str(outline_pdf)) as doc:
            items = list(doc.outline)
            assert len(items) == 2
            assert all(isinstance(i, OutlineItem) for i in items)

    def test_children_are_tuple(self, outline_pdf):
        with sopdf.open(str(outline_pdf)) as doc:
            ch2 = doc.outline.items[1]
            assert isinstance(ch2.children, tuple)
