"""Tests for Document.split and Document.split_each."""

import pytest
import sopdf
from sopdf import Document, PageError


class TestSplit:
    def test_split_returns_document(self, multipage_pdf):
        with sopdf.open(str(multipage_pdf)) as doc:
            new_doc = doc.split(pages=[0, 1])
            assert isinstance(new_doc, Document)
            assert new_doc.page_count == 2
            new_doc.close()

    def test_split_correct_page_count(self, multipage_pdf):
        with sopdf.open(str(multipage_pdf)) as doc:
            new_doc = doc.split(pages=[0, 2, 4])
            assert new_doc.page_count == 3
            new_doc.close()

    def test_split_to_file(self, multipage_pdf, tmp_path):
        out = tmp_path / "split.pdf"
        with sopdf.open(str(multipage_pdf)) as doc:
            doc.split(pages=[0, 1], output=out)
        assert out.exists()
        with sopdf.open(str(out)) as split_doc:
            assert split_doc.page_count == 2

    def test_split_invalid_page_index(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            with pytest.raises(PageError):
                doc.split(pages=[99])

    def test_split_does_not_modify_original(self, multipage_pdf):
        with sopdf.open(str(multipage_pdf)) as doc:
            original_count = doc.page_count
            _ = doc.split(pages=[0])
            assert doc.page_count == original_count


class TestSplitEach:
    def test_split_each_creates_files(self, multipage_pdf, tmp_path):
        with sopdf.open(str(multipage_pdf)) as doc:
            doc.split_each(output_dir=tmp_path / "pages")
        files = sorted((tmp_path / "pages").glob("page_*.pdf"))
        assert len(files) == 5

    def test_split_each_files_are_single_page(self, multipage_pdf, tmp_path):
        with sopdf.open(str(multipage_pdf)) as doc:
            doc.split_each(output_dir=tmp_path / "pages")
        for f in (tmp_path / "pages").glob("page_*.pdf"):
            with sopdf.open(str(f)) as single:
                assert single.page_count == 1

    def test_split_each_creates_dir(self, simple_pdf, tmp_path):
        output = tmp_path / "new" / "nested" / "dir"
        with sopdf.open(str(simple_pdf)) as doc:
            doc.split_each(output_dir=output)
        assert output.exists()
