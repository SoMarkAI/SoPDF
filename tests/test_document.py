"""Tests for sopdf.Document — construction, properties, lifecycle."""

import io
from pathlib import Path

import pytest
import sopdf
from sopdf import Document, FileDataError, PageError, PasswordError


class TestDocumentOpen:
    def test_open_from_path_str(self, simple_pdf):
        doc = sopdf.open(str(simple_pdf))
        assert isinstance(doc, Document)
        doc.close()

    def test_open_from_path_object(self, simple_pdf):
        doc = sopdf.open(simple_pdf)
        assert isinstance(doc, Document)
        doc.close()

    def test_open_from_stream(self, simple_pdf):
        data = simple_pdf.read_bytes()
        doc = sopdf.open(stream=data)
        assert isinstance(doc, Document)
        doc.close()

    def test_open_encrypted_correct_password(self, encrypted_pdf):
        doc = sopdf.open(str(encrypted_pdf), password="secret")
        assert doc.page_count >= 1
        doc.close()

    def test_open_encrypted_wrong_password(self, encrypted_pdf):
        with pytest.raises(PasswordError):
            sopdf.open(str(encrypted_pdf), password="wrong")

    def test_open_encrypted_no_password(self, encrypted_pdf):
        with pytest.raises((PasswordError, FileDataError)):
            sopdf.open(str(encrypted_pdf))

    def test_open_nonexistent_file(self, tmp_path):
        with pytest.raises((FileDataError, FileNotFoundError, Exception)):
            sopdf.open(str(tmp_path / "does_not_exist.pdf"))

    def test_open_invalid_data(self, tmp_path):
        bad = tmp_path / "bad.pdf"
        bad.write_bytes(b"this is not a pdf at all")
        with pytest.raises((FileDataError, Exception)):
            sopdf.open(str(bad))

    def test_open_no_args_raises(self):
        with pytest.raises(ValueError):
            Document._open()


class TestDocumentContextManager:
    def test_with_statement(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            assert doc.page_count >= 1

    def test_closed_after_with(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            pass
        assert doc._closed is True

    def test_use_after_close_raises(self, simple_pdf):
        doc = sopdf.open(str(simple_pdf))
        doc.close()
        with pytest.raises(Exception):
            _ = doc.page_count


class TestDocumentProperties:
    def test_page_count_single(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            assert doc.page_count == 1

    def test_page_count_multi(self, multipage_pdf):
        with sopdf.open(str(multipage_pdf)) as doc:
            assert doc.page_count == 5

    def test_metadata_returns_metadata_object(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            meta = doc.metadata
            assert isinstance(meta, sopdf.Metadata)
            # backward-compat: to_dict() has lowercase keys
            d = meta.to_dict()
            for key in ("title", "author", "subject", "creator", "producer"):
                assert key in d

    def test_is_encrypted_false(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            assert doc.is_encrypted is False

    def test_is_encrypted_true(self, encrypted_pdf):
        with sopdf.open(str(encrypted_pdf), password="secret") as doc:
            assert doc.is_encrypted is True

    def test_len(self, multipage_pdf):
        with sopdf.open(str(multipage_pdf)) as doc:
            assert len(doc) == 5

    def test_repr(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            assert "Document" in repr(doc)


class TestDocumentPageAccess:
    def test_getitem_first_page(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            page = doc[0]
            assert page.number == 0

    def test_getitem_negative_index(self, multipage_pdf):
        with sopdf.open(str(multipage_pdf)) as doc:
            page = doc[-1]
            assert page.number == doc.page_count - 1

    def test_getitem_out_of_range(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            with pytest.raises(PageError):
                _ = doc[99]

    def test_load_page(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            page = doc.load_page(0)
            assert page.number == 0

    def test_pages_list(self, multipage_pdf):
        with sopdf.open(str(multipage_pdf)) as doc:
            pages = list(doc.pages)
            assert len(pages) == 5

    def test_iteration(self, multipage_pdf):
        with sopdf.open(str(multipage_pdf)) as doc:
            indices = [p.number for p in doc]
            assert indices == list(range(5))
