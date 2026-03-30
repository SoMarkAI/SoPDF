"""Tests for page rotation."""

import pytest
import sopdf
from sopdf import PageError


class TestRotation:
    def test_set_rotation_90(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            doc[0].rotation = 90
            assert doc[0].rotation == 90

    def test_set_rotation_180(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            doc[0].rotation = 180
            assert doc[0].rotation == 180

    def test_set_rotation_270(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            doc[0].rotation = 270
            assert doc[0].rotation == 270

    def test_reset_rotation_to_0(self, rotated_pdf):
        with sopdf.open(str(rotated_pdf)) as doc:
            for i in range(doc.page_count):
                doc[i].rotation = 0
                assert doc[i].rotation == 0

    def test_invalid_rotation_raises(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            with pytest.raises((PageError, Exception)):
                doc[0].rotation = 45

    def test_rotation_persists_after_save(self, simple_pdf, tmp_path):
        out = tmp_path / "rotated.pdf"
        with sopdf.open(str(simple_pdf)) as doc:
            doc[0].rotation = 90
            doc.save(out)
        with sopdf.open(str(out)) as doc:
            assert doc[0].rotation == 90

    def test_set_rotation_method(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            doc[0].set_rotation(270)
            assert doc[0].rotation == 270

    def test_rotation_marks_dirty(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            assert doc._dirty is False
            doc[0].rotation = 90
            assert doc._dirty is True
