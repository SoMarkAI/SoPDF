"""
Targeted tests to cover remaining branches and edge cases.
These complement the main test modules.
"""

from __future__ import annotations

import io

import pytest
import sopdf
from sopdf import FileDataError, PasswordError, TextBlock, Rect
from sopdf._utils import ensure_synced, safe_save


# ---------------------------------------------------------------------------
# TextBlock.to_dict
# ---------------------------------------------------------------------------

class TestTextBlockDict:
    def test_to_dict_returns_dict(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            blocks = doc[0].get_text_blocks()
            if blocks:
                d = blocks[0].to_dict()
                assert isinstance(d, dict)
                assert "text" in d
                assert "rect" in d
                assert set(d["rect"]) >= {"x0", "y0", "x1", "y1"}

    def test_to_dict_direct(self):
        r = Rect(1, 2, 3, 4)
        tb = TextBlock("hello", r)
        d = tb.to_dict()
        assert d["text"] == "hello"
        assert d["rect"]["x0"] == 1.0

    def test_repr(self):
        tb = TextBlock("hello world", Rect(0, 0, 100, 20))
        assert "TextBlock" in repr(tb)

    def test_repr_long_text(self):
        tb = TextBlock("a" * 80, Rect(0, 0, 100, 20))
        assert "…" in repr(tb)


# ---------------------------------------------------------------------------
# Stream open error paths
# ---------------------------------------------------------------------------

class TestStreamOpenErrors:
    def test_open_stream_with_wrong_password(self, encrypted_pdf):
        data = encrypted_pdf.read_bytes()
        with pytest.raises((PasswordError, FileDataError)):
            sopdf.open(stream=data, password="wrong")

    def test_open_stream_invalid_bytes(self):
        with pytest.raises((FileDataError, Exception)):
            sopdf.open(stream=b"not a pdf at all %%%%")

    def test_open_stream_encrypted_no_password(self, encrypted_pdf):
        data = encrypted_pdf.read_bytes()
        with pytest.raises((PasswordError, FileDataError)):
            sopdf.open(stream=data)


# ---------------------------------------------------------------------------
# Merge error paths
# ---------------------------------------------------------------------------

class TestMergeErrors:
    def test_merge_nonexistent_file(self, tmp_path):
        with pytest.raises(Exception):
            sopdf.merge([str(tmp_path / "ghost.pdf")], output=tmp_path / "out.pdf")

    def test_merge_invalid_file(self, tmp_path):
        bad = tmp_path / "bad.pdf"
        bad.write_bytes(b"not a pdf")
        with pytest.raises(Exception):
            sopdf.merge([str(bad)], output=tmp_path / "out.pdf")


# ---------------------------------------------------------------------------
# ensure_synced when not dirty
# ---------------------------------------------------------------------------

class TestEnsureSyncedNoop:
    def test_ensure_synced_on_clean_doc(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            assert doc._dirty is False
            original = doc._pdfium_doc
            ensure_synced(doc)  # should be a no-op
            assert doc._pdfium_doc is original  # not replaced


# ---------------------------------------------------------------------------
# safe_save
# ---------------------------------------------------------------------------

class TestSafeSave:
    def test_safe_save_writes_file(self, simple_pdf, tmp_path):
        import pikepdf

        out = tmp_path / "safe_out.pdf"
        with pikepdf.open(str(simple_pdf)) as pike_doc:
            safe_save(pike_doc, out)
        assert out.exists()

    def test_save_overwrite_via_document(self, simple_pdf, tmp_path):
        import shutil

        copy = tmp_path / "copy.pdf"
        shutil.copy(str(simple_pdf), str(copy))
        with sopdf.open(str(copy)) as doc:
            doc[0].rotation = 90
            doc.save(copy)  # in-place overwrite — exercises safe_save path
        with sopdf.open(str(copy)) as doc:
            assert doc[0].rotation == 90


# ---------------------------------------------------------------------------
# Document close idempotency
# ---------------------------------------------------------------------------

class TestDocumentClose:
    def test_close_twice_no_error(self, simple_pdf):
        doc = sopdf.open(str(simple_pdf))
        doc.close()
        doc.close()  # second close must not raise
