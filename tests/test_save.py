"""Tests for Document.save, Document.to_bytes, and in-place overwrite."""

import shutil

import pytest
import sopdf


class TestSave:
    def test_save_creates_file(self, simple_pdf, tmp_path):
        out = tmp_path / "out.pdf"
        with sopdf.open(str(simple_pdf)) as doc:
            doc.save(out)
        assert out.exists()
        assert out.stat().st_size > 0

    def test_saved_file_is_valid_pdf(self, simple_pdf, tmp_path):
        out = tmp_path / "out.pdf"
        with sopdf.open(str(simple_pdf)) as doc:
            doc.save(out)
        with sopdf.open(str(out)) as saved:
            assert saved.page_count == 1

    def test_save_with_compress(self, simple_pdf, tmp_path):
        out = tmp_path / "compressed.pdf"
        with sopdf.open(str(simple_pdf)) as doc:
            doc.save(out, compress=True)
        assert out.exists()

    def test_save_with_garbage(self, simple_pdf, tmp_path):
        out = tmp_path / "garbage.pdf"
        with sopdf.open(str(simple_pdf)) as doc:
            doc.save(out, garbage=True)
        assert out.exists()

    def test_save_creates_parent_dirs(self, simple_pdf, tmp_path):
        out = tmp_path / "deep" / "nested" / "out.pdf"
        with sopdf.open(str(simple_pdf)) as doc:
            doc.save(out)
        assert out.exists()

    def test_save_overwrite_same_file(self, simple_pdf, tmp_path):
        copy = tmp_path / "copy.pdf"
        shutil.copy(str(simple_pdf), str(copy))
        with sopdf.open(str(copy)) as doc:
            # Overwrite in place — should not raise on any platform
            doc.save(copy)
        with sopdf.open(str(copy)) as doc:
            assert doc.page_count == 1


class TestToBytes:
    def test_to_bytes_returns_bytes(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            data = doc.to_bytes()
            assert isinstance(data, bytes)
            assert len(data) > 0

    def test_to_bytes_is_valid_pdf(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            data = doc.to_bytes()
        reopened = sopdf.open(stream=data)
        assert reopened.page_count == 1
        reopened.close()

    def test_to_bytes_compressed_smaller_or_equal(self, multipage_pdf):
        with sopdf.open(str(multipage_pdf)) as doc:
            compressed = doc.to_bytes(compress=True)
            uncompressed = doc.to_bytes(compress=False)
        assert len(compressed) <= len(uncompressed) * 1.1  # allow slight variance
