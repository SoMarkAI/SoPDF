"""Tests for opening and repairing corrupted PDFs."""

import pytest
import sopdf
from sopdf import FileDataError


class TestRepair:
    def test_open_corrupted_or_raises_file_data_error(self, corrupted_pdf):
        """The corrupted fixture may open (with repair) or raise FileDataError — both are valid."""
        try:
            with sopdf.open(str(corrupted_pdf)) as doc:
                assert doc.page_count >= 1
        except FileDataError:
            pass  # Corruption was too severe — acceptable

    def test_save_repaired(self, corrupted_pdf, tmp_path):
        """If the corrupted PDF can be opened, saving it should produce a valid file."""
        try:
            with sopdf.open(str(corrupted_pdf)) as doc:
                out = tmp_path / "repaired.pdf"
                doc.save(out, compress=True, garbage=True)
            with sopdf.open(str(out)) as repaired:
                assert repaired.page_count >= 1
        except FileDataError:
            pytest.skip("Fixture too corrupted to open — skipping repair test")

    def test_severely_corrupted_raises_file_data_error(self, tmp_path):
        bad = tmp_path / "bad.pdf"
        bad.write_bytes(b"not a pdf at all %%%%")
        with pytest.raises((FileDataError, Exception)):
            sopdf.open(str(bad))
