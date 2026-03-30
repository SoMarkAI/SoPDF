"""Tests for sopdf.Page — properties and boundary behaviour."""

import pytest
import sopdf
from sopdf import PageError, Rect


class TestPageProperties:
    def test_number(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            assert doc[0].number == 0

    def test_rect_is_rect(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            r = doc[0].rect
            assert isinstance(r, Rect)

    def test_rect_dimensions_positive(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            r = doc[0].rect
            assert r.width > 0
            assert r.height > 0

    def test_rotation_default_zero(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            assert doc[0].rotation == 0

    def test_rotation_values(self, rotated_pdf):
        with sopdf.open(str(rotated_pdf)) as doc:
            rotations = [doc[i].rotation for i in range(doc.page_count)]
            assert 90 in rotations or 180 in rotations or 270 in rotations

    def test_repr(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            assert "Page" in repr(doc[0])


class TestPageMutation:
    def test_set_rotation_90(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            doc[0].rotation = 90
            assert doc[0].rotation == 90

    def test_set_rotation_via_setter(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            doc[0].set_rotation(180)
            assert doc[0].rotation == 180

    def test_set_rotation_invalid(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            with pytest.raises((PageError, Exception)):
                doc[0].set_rotation(45)

    def test_set_rotation_marks_dirty(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            doc[0].rotation = 90
            assert doc._dirty is True
