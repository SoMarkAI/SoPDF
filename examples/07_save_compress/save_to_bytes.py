"""Serialise a document to bytes without writing to disk."""

import sopdf

with sopdf.open("../../tests/fixtures/simple.pdf") as doc:
    data = doc.to_bytes(compress=True)  # returns bytes

print(f"In-memory PDF size: {len(data):,} bytes")

# The bytes are a valid PDF — you can re-open them
with sopdf.open(stream=data) as doc2:
    print(f"Re-opened from bytes — pages: {doc2.page_count}")
