"""Tests for sopdf.merge and Document.append."""

import pytest
import sopdf


class TestModuleMerge:
    def test_merge_two_files(self, simple_pdf, multipage_pdf, tmp_path):
        out = tmp_path / "merged.pdf"
        sopdf.merge([str(simple_pdf), str(multipage_pdf)], output=out)
        assert out.exists()
        with sopdf.open(str(out)) as doc:
            assert doc.page_count == 6  # 1 + 5

    def test_merge_three_files(self, simple_pdf, tmp_path):
        out = tmp_path / "triple.pdf"
        sopdf.merge([str(simple_pdf)] * 3, output=out)
        with sopdf.open(str(out)) as doc:
            assert doc.page_count == 3

    def test_merge_creates_parent_dirs(self, simple_pdf, tmp_path):
        out = tmp_path / "deep" / "nested" / "merged.pdf"
        sopdf.merge([str(simple_pdf)], output=out)
        assert out.exists()

    def test_merge_empty_inputs_raises(self, tmp_path):
        with pytest.raises(ValueError):
            sopdf.merge([], output=tmp_path / "out.pdf")


class TestAppend:
    def test_append_adds_pages(self, simple_pdf, multipage_pdf):
        with sopdf.open(str(simple_pdf)) as doc_a:
            with sopdf.open(str(multipage_pdf)) as doc_b:
                doc_a.append(doc_b)
                assert doc_a.page_count == 6

    def test_append_marks_dirty(self, simple_pdf, multipage_pdf):
        with sopdf.open(str(simple_pdf)) as doc_a:
            with sopdf.open(str(multipage_pdf)) as doc_b:
                doc_a.append(doc_b)
                assert doc_a._dirty is True

    def test_append_and_save(self, simple_pdf, multipage_pdf, tmp_path):
        out = tmp_path / "appended.pdf"
        with sopdf.open(str(simple_pdf)) as doc_a:
            with sopdf.open(str(multipage_pdf)) as doc_b:
                doc_a.append(doc_b)
                doc_a.save(out)
        with sopdf.open(str(out)) as doc:
            assert doc.page_count == 6
