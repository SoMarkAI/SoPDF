"""Save a document to disk (default settings)."""

import sopdf

with sopdf.open("../../tests/fixtures/simple.pdf") as doc:
    doc.save("output.pdf")

print("Saved output.pdf")
