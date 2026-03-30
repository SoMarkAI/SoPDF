"""Tests for opening encrypted PDFs and saving as decrypted."""

import pytest
import sopdf
from sopdf import PasswordError


class TestDecrypt:
    def test_open_with_correct_password(self, encrypted_pdf):
        with sopdf.open(str(encrypted_pdf), password="secret") as doc:
            assert doc.page_count >= 1

    def test_open_wrong_password_raises(self, encrypted_pdf):
        with pytest.raises(PasswordError):
            sopdf.open(str(encrypted_pdf), password="wrong_password")

    def test_is_encrypted(self, encrypted_pdf):
        with sopdf.open(str(encrypted_pdf), password="secret") as doc:
            assert doc.is_encrypted is True

    def test_save_removes_encryption(self, encrypted_pdf, tmp_path):
        out = tmp_path / "decrypted.pdf"
        with sopdf.open(str(encrypted_pdf), password="secret") as doc:
            doc.save(str(out))
        # Should open without password now
        with sopdf.open(str(out)) as doc:
            assert doc.page_count >= 1

    def test_decrypted_file_not_encrypted(self, encrypted_pdf, tmp_path):
        out = tmp_path / "decrypted.pdf"
        with sopdf.open(str(encrypted_pdf), password="secret") as doc:
            doc.save(str(out))
        with sopdf.open(str(out)) as doc:
            assert doc.is_encrypted is False
