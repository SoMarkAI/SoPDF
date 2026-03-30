"""Tests for the sopdf exception hierarchy."""

import pytest
import sopdf
from sopdf import PDFError, PasswordError, FileDataError, PageError


class TestExceptionHierarchy:
    def test_pdf_error_is_runtime_error(self):
        assert issubclass(PDFError, RuntimeError)

    def test_password_error_is_pdf_error(self):
        assert issubclass(PasswordError, PDFError)

    def test_file_data_error_is_pdf_error(self):
        assert issubclass(FileDataError, PDFError)

    def test_page_error_is_pdf_error(self):
        assert issubclass(PageError, PDFError)

    def test_can_catch_password_error_as_pdf_error(self):
        with pytest.raises(PDFError):
            raise PasswordError("bad password")

    def test_can_catch_file_data_error_as_runtime_error(self):
        with pytest.raises(RuntimeError):
            raise FileDataError("bad file")

    def test_exception_message_preserved(self):
        msg = "test message"
        exc = PageError(msg)
        assert str(exc) == msg
