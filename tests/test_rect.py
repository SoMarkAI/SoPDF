"""Comprehensive unit tests for sopdf.Rect."""

import pytest
from sopdf import Rect


class TestRectConstruction:
    def test_basic_construction(self):
        r = Rect(0, 0, 100, 200)
        assert r.x0 == 0
        assert r.y0 == 0
        assert r.x1 == 100
        assert r.y1 == 200

    def test_float_coercion(self):
        r = Rect(1, 2, 3, 4)
        assert isinstance(r.x0, float)

    def test_repr(self):
        r = Rect(1, 2, 3, 4)
        assert "Rect" in repr(r)

    def test_iter_unpacking(self):
        r = Rect(1, 2, 3, 4)
        x0, y0, x1, y1 = r
        assert (x0, y0, x1, y1) == (1.0, 2.0, 3.0, 4.0)

    def test_equality(self):
        assert Rect(0, 0, 10, 10) == Rect(0, 0, 10, 10)
        assert Rect(0, 0, 10, 10) != Rect(0, 0, 10, 11)

    def test_equality_with_non_rect(self):
        assert Rect(0, 0, 10, 10).__eq__("not a rect") is NotImplemented


class TestRectDimensions:
    def test_width(self):
        assert Rect(10, 0, 60, 100).width == 50

    def test_height(self):
        assert Rect(0, 20, 100, 70).height == 50

    def test_get_area(self):
        assert Rect(0, 0, 10, 5).get_area() == 50

    def test_area_of_invalid_rect(self):
        assert Rect(10, 0, 0, 10).get_area() == 0


class TestRectValidity:
    def test_valid(self):
        assert Rect(0, 0, 10, 10).is_valid is True

    def test_invalid_x(self):
        assert Rect(10, 0, 5, 10).is_valid is False

    def test_invalid_y(self):
        assert Rect(0, 10, 10, 5).is_valid is False

    def test_empty_zero_width(self):
        assert Rect(5, 0, 5, 10).is_empty is True

    def test_empty_zero_height(self):
        assert Rect(0, 5, 10, 5).is_empty is True

    def test_not_empty(self):
        assert Rect(0, 0, 1, 1).is_empty is False


class TestRectContainment:
    def test_contains_inner_rect(self):
        outer = Rect(0, 0, 100, 100)
        inner = Rect(10, 10, 90, 90)
        assert outer.contains(inner) is True

    def test_does_not_contain_larger(self):
        small = Rect(10, 10, 50, 50)
        large = Rect(0, 0, 100, 100)
        assert small.contains(large) is False

    def test_contains_point_inside(self):
        r = Rect(0, 0, 100, 100)
        assert r.contains((50, 50)) is True

    def test_contains_point_outside(self):
        r = Rect(0, 0, 100, 100)
        assert r.contains((150, 50)) is False

    def test_contains_point_on_edge(self):
        r = Rect(0, 0, 100, 100)
        assert r.contains((0, 0)) is True
        assert r.contains((100, 100)) is True


class TestRectIntersection:
    def test_intersects_overlapping(self):
        a = Rect(0, 0, 50, 50)
        b = Rect(25, 25, 75, 75)
        assert a.intersects(b) is True

    def test_intersects_touching_edge(self):
        a = Rect(0, 0, 50, 50)
        b = Rect(50, 0, 100, 50)
        assert a.intersects(b) is True

    def test_not_intersects_separate(self):
        a = Rect(0, 0, 10, 10)
        b = Rect(20, 20, 30, 30)
        assert a.intersects(b) is False

    def test_intersect_overlap_region(self):
        a = Rect(0, 0, 50, 50)
        b = Rect(25, 25, 75, 75)
        result = a.intersect(b)
        assert result == Rect(25, 25, 50, 50)

    def test_intersect_no_overlap(self):
        a = Rect(0, 0, 10, 10)
        b = Rect(20, 20, 30, 30)
        result = a.intersect(b)
        assert result.is_empty or not result.is_valid

    def test_include_rect_bounding_box(self):
        a = Rect(0, 0, 50, 50)
        b = Rect(25, 25, 75, 75)
        result = a.include_rect(b)
        assert result == Rect(0, 0, 75, 75)

    def test_include_point_expands(self):
        r = Rect(10, 10, 50, 50)
        result = r.include_point(0, 0)
        assert result.x0 == 0
        assert result.y0 == 0

    def test_include_point_inside_unchanged(self):
        r = Rect(0, 0, 100, 100)
        result = r.include_point(50, 50)
        assert result == r
