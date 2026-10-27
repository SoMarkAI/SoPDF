"""Tests for page rendering."""

import io

import cv2
import numpy as np
import pytest
import sopdf


def _is_png(data: bytes) -> bool:
    return data[:8] == b"\x89PNG\r\n\x1a\n"


def _is_jpeg(data: bytes) -> bool:
    return data[:2] == b"\xff\xd8"


class TestRenderSinglePage:
    def test_render_returns_bytes(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            data = doc[0].render()
            assert isinstance(data, bytes)
            assert len(data) > 0

    def test_render_default_is_png(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            data = doc[0].render()
            assert _is_png(data)

    def test_render_jpeg(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            data = doc[0].render(format="jpeg")
            assert _is_jpeg(data)

    def test_render_higher_dpi_larger_file(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            low = doc[0].render(dpi=72)
            high = doc[0].render(dpi=300)
            assert len(high) > len(low)

    def test_render_to_file(self, simple_pdf, tmp_path):
        with sopdf.open(str(simple_pdf)) as doc:
            out = tmp_path / "page.png"
            doc[0].render_to_file(out)
            assert out.exists()
            assert _is_png(out.read_bytes())

    def test_render_to_file_creates_dirs(self, simple_pdf, tmp_path):
        with sopdf.open(str(simple_pdf)) as doc:
            out = tmp_path / "nested" / "dir" / "page.png"
            doc[0].render_to_file(out)
            assert out.exists()


class TestRenderArray:
    def test_render_array_is_bgr_uint8_at_dpi(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            page = doc[0]
            arr = page.render_array(dpi=144)
            assert arr.dtype == np.uint8
            assert arr.ndim == 3 and arr.shape[2] == 3
            assert arr.shape[:2] == (round(page.rect.height * 2), round(page.rect.width * 2))

    @pytest.mark.parametrize("alpha", [False, True])
    def test_render_array_matches_decoded_png(self, simple_pdf, alpha):
        with sopdf.open(str(simple_pdf)) as doc:
            arr = doc[0].render_array(dpi=96, alpha=alpha)
            png = doc[0].render(dpi=96, alpha=alpha)
        decoded = cv2.imdecode(np.frombuffer(png, np.uint8), cv2.IMREAD_UNCHANGED)
        assert np.array_equal(arr, decoded)

    def test_render_array_owns_its_memory(self, simple_pdf):
        # A view of PDFium's buffer would dangle once the bitmap is freed.
        with sopdf.open(str(simple_pdf)) as doc:
            arr = doc[0].render_array()
        assert arr.flags.owndata


class TestRenderBatch:
    def test_render_pages_returns_list(self, multipage_pdf):
        with sopdf.open(str(multipage_pdf)) as doc:
            imgs = sopdf.render_pages(list(doc.pages), dpi=72)
            assert len(imgs) == doc.page_count

    def test_render_pages_all_png(self, multipage_pdf):
        with sopdf.open(str(multipage_pdf)) as doc:
            imgs = sopdf.render_pages(list(doc.pages))
            assert all(_is_png(img) for img in imgs)

    def test_render_pages_to_files(self, multipage_pdf, tmp_path):
        with sopdf.open(str(multipage_pdf)) as doc:
            sopdf.render_pages_to_files(list(doc.pages), tmp_path)
            files = list(tmp_path.glob("page_*.png"))
            assert len(files) == doc.page_count
