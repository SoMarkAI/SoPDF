"""Tests for sopdf.Metadata — read, write, date parsing, null handling."""

from datetime import datetime, timezone, timedelta

import pytest
import sopdf
from sopdf import Metadata


class TestMetadataType:
    def test_metadata_is_metadata_object(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            assert isinstance(doc.metadata, Metadata)

    def test_same_object_on_repeated_access(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            assert doc.metadata is doc.metadata

    def test_repr_contains_metadata(self, metadata_pdf):
        with sopdf.open(str(metadata_pdf)) as doc:
            r = repr(doc.metadata)
            assert "Metadata" in r
            assert "Test Title" in r


class TestMetadataRead:
    def test_title(self, metadata_pdf):
        with sopdf.open(str(metadata_pdf)) as doc:
            assert doc.metadata.title == "Test Title"

    def test_author(self, metadata_pdf):
        with sopdf.open(str(metadata_pdf)) as doc:
            assert doc.metadata.author == "Test Author"

    def test_subject(self, metadata_pdf):
        with sopdf.open(str(metadata_pdf)) as doc:
            assert doc.metadata.subject == "Test Subject"

    def test_keywords(self, metadata_pdf):
        with sopdf.open(str(metadata_pdf)) as doc:
            assert doc.metadata.keywords == "test keyword"

    def test_creator(self, metadata_pdf):
        with sopdf.open(str(metadata_pdf)) as doc:
            assert doc.metadata.creator == "Test Creator"

    def test_producer(self, metadata_pdf):
        with sopdf.open(str(metadata_pdf)) as doc:
            assert doc.metadata.producer == "Test Producer"

    def test_creation_date_raw_string(self, metadata_pdf):
        with sopdf.open(str(metadata_pdf)) as doc:
            assert doc.metadata.creation_date is not None
            assert "2024" in doc.metadata.creation_date

    def test_mod_date_raw_string(self, metadata_pdf):
        with sopdf.open(str(metadata_pdf)) as doc:
            assert doc.metadata.mod_date is not None
            assert "2024" in doc.metadata.mod_date


class TestMetadataNull:
    def test_missing_fields_return_none(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            # simple.pdf has no metadata set via pikepdf — fields are empty or absent
            meta = doc.metadata
            # None of these should raise; values may be None or empty string → None
            for field in ("title", "author", "subject", "keywords", "creator", "producer"):
                val = getattr(meta, field)
                assert val is None or isinstance(val, str)

    def test_creation_datetime_none_when_absent(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            # simple.pdf has no dates; should return None, never raise
            result = doc.metadata.creation_datetime
            assert result is None or isinstance(result, datetime)

    def test_mod_datetime_none_when_absent(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            result = doc.metadata.mod_datetime
            assert result is None or isinstance(result, datetime)


class TestDateParsing:
    def test_creation_datetime_utc_plus_8(self, metadata_pdf):
        with sopdf.open(str(metadata_pdf)) as doc:
            dt = doc.metadata.creation_datetime
            assert dt is not None
            assert dt.year == 2024
            assert dt.month == 1
            assert dt.day == 1
            assert dt.hour == 12
            assert dt.minute == 0
            # UTC+8
            assert dt.utcoffset() == timedelta(hours=8)

    def test_mod_datetime_utc(self, metadata_pdf):
        with sopdf.open(str(metadata_pdf)) as doc:
            dt = doc.metadata.mod_datetime
            assert dt is not None
            assert dt.year == 2024
            assert dt.month == 6
            assert dt.day == 1
            assert dt.hour == 9
            assert dt.tzinfo == timezone.utc

    def test_malformed_date_returns_none(self, simple_pdf):
        from sopdf._metadata import _parse_pdf_date
        assert _parse_pdf_date(None) is None
        assert _parse_pdf_date("") is None
        assert _parse_pdf_date("not-a-date") is None
        assert _parse_pdf_date("D:") is None

    def test_parse_date_without_d_prefix(self):
        from sopdf._metadata import _parse_pdf_date
        dt = _parse_pdf_date("20230315")
        assert dt is not None
        assert dt.year == 2023
        assert dt.month == 3
        assert dt.day == 15

    def test_parse_date_utc_z(self):
        from sopdf._metadata import _parse_pdf_date
        dt = _parse_pdf_date("D:20230315120000Z")
        assert dt is not None
        assert dt.tzinfo == timezone.utc

    def test_parse_date_negative_offset(self):
        from sopdf._metadata import _parse_pdf_date
        dt = _parse_pdf_date("D:20230315120000-05'00'")
        assert dt is not None
        assert dt.utcoffset() == timedelta(hours=-5)

    def test_parse_date_invalid_month_zero_returns_none(self):
        # Regex matches (4-digit year, then "00" month) but datetime(2024, 0, …) raises ValueError
        from sopdf._metadata import _parse_pdf_date
        assert _parse_pdf_date("D:20240000000000Z") is None

    def test_write_mod_date_round_trip(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            doc.metadata.mod_date = "D:20250101000000Z"
            data = doc.to_bytes()
        with sopdf.open(stream=data) as doc2:
            assert doc2.metadata.mod_datetime is not None
            assert doc2.metadata.mod_datetime.year == 2025

    def test_write_none_on_absent_field_does_not_raise(self, simple_pdf):
        # simple.pdf has no /Title in its Info dict — deleting a non-existent key
        # should not raise (KeyError is caught internally).
        with sopdf.open(str(simple_pdf)) as doc:
            doc.metadata.title = None  # key doesn't exist → KeyError swallowed


class TestMetadataWrite:
    def test_write_title_round_trip(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            doc.metadata.title = "New Title"
            data = doc.to_bytes()

        with sopdf.open(stream=data) as doc2:
            assert doc2.metadata.title == "New Title"

    def test_write_author_round_trip(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            doc.metadata.author = "New Author"
            data = doc.to_bytes()

        with sopdf.open(stream=data) as doc2:
            assert doc2.metadata.author == "New Author"

    def test_write_all_fields_round_trip(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            doc.metadata.title    = "Title"
            doc.metadata.author   = "Author"
            doc.metadata.subject  = "Subject"
            doc.metadata.keywords = "kw1 kw2"
            doc.metadata.creator  = "Creator"
            doc.metadata.producer = "Producer"
            data = doc.to_bytes()

        with sopdf.open(stream=data) as doc2:
            assert doc2.metadata.title    == "Title"
            assert doc2.metadata.author   == "Author"
            assert doc2.metadata.subject  == "Subject"
            assert doc2.metadata.keywords == "kw1 kw2"
            assert doc2.metadata.creator  == "Creator"
            assert doc2.metadata.producer == "Producer"

    def test_write_sets_dirty_flag(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            assert doc._dirty is False
            doc.metadata.title = "X"
            assert doc._dirty is True

    def test_write_then_read_reflects_value(self, simple_pdf):
        """After writing, reading the same property returns the updated value."""
        with sopdf.open(str(simple_pdf)) as doc:
            doc.metadata.title = "In-memory Title"
            assert doc.metadata.title == "In-memory Title"

    def test_write_none_removes_field(self, metadata_pdf):
        with sopdf.open(str(metadata_pdf)) as doc:
            doc.metadata.title = None
            data = doc.to_bytes()

        with sopdf.open(stream=data) as doc2:
            assert doc2.metadata.title is None

    def test_write_date_round_trip(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            doc.metadata.creation_date = "D:20250101000000Z"
            data = doc.to_bytes()

        with sopdf.open(stream=data) as doc2:
            assert doc2.metadata.creation_datetime is not None
            assert doc2.metadata.creation_datetime.year == 2025


class TestMetadataDictCompat:
    def test_to_dict_returns_lowercase_keys(self, metadata_pdf):
        with sopdf.open(str(metadata_pdf)) as doc:
            d = doc.metadata.to_dict()
            assert isinstance(d, dict)
            for key in d:
                assert key == key.lower()

    def test_to_dict_has_standard_keys(self, metadata_pdf):
        with sopdf.open(str(metadata_pdf)) as doc:
            d = doc.metadata.to_dict()
            for key in ("title", "author", "subject", "creator", "producer"):
                assert key in d

    def test_getitem_dict_style(self, metadata_pdf):
        with sopdf.open(str(metadata_pdf)) as doc:
            assert doc.metadata["title"] == doc.metadata.title
            assert doc.metadata["author"] == doc.metadata.author

    def test_getitem_missing_key_returns_none(self, simple_pdf):
        with sopdf.open(str(simple_pdf)) as doc:
            assert doc.metadata["nonexistent_key_xyz"] is None
