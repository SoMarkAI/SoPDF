"""
Tests for dual-engine state synchronisation.

When a write operation (e.g. rotation) marks the document dirty, the next
read operation (rendering or text extraction) must auto-sync and reflect the
new state.
"""

import pytest
import sopdf
from sopdf._utils import ensure_synced


class TestDirtyFlag:
    def test_fresh_doc_not_dirty(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            assert doc._dirty is False

    def test_rotation_marks_dirty(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            doc[0].rotation = 90
            assert doc._dirty is True

    def test_append_marks_dirty(self, simple_pdf, multipage_pdf):
        with sopdf.open(str(simple_pdf)) as doc_a:
            with sopdf.open(str(multipage_pdf)) as doc_b:
                doc_a.append(doc_b)
            assert doc_a._dirty is True

    def test_ensure_synced_clears_dirty(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            doc[0].rotation = 90
            assert doc._dirty is True
            ensure_synced(doc)
            assert doc._dirty is False


class TestHotReload:
    def test_render_after_rotation_does_not_raise(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            doc[0].rotation = 90
            # render() must call ensure_synced() internally
            data = doc[0].render(dpi=72)
            assert len(data) > 0

    def test_get_text_after_append_does_not_raise(self, simple_pdf, multipage_pdf):
        with sopdf.open(str(simple_pdf)) as doc_a:
            with sopdf.open(str(multipage_pdf)) as doc_b:
                doc_a.append(doc_b)
            # Text extraction on any page should work after sync
            text = doc_a[0].get_text()
            assert isinstance(text, str)

    def test_pdfium_doc_replaced_after_sync(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            original_pdfium = doc._pdfium_doc
            doc[0].rotation = 90
            ensure_synced(doc)
            # After hot-reload the pdfium instance is replaced
            assert doc._pdfium_doc is not original_pdfium
