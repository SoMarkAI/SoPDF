"""Open a PDF from raw bytes — useful when you already have the file in memory."""

import sopdf

# Read the file into memory first
with open("../../tests/fixtures/simple.pdf", "rb") as f:
    pdf_bytes = f.read()

# Then open from the bytes stream
with sopdf.open(stream=pdf_bytes) as doc:
    print(f"Pages: {doc.page_count}")
    print(f"Source: <in-memory stream>")
