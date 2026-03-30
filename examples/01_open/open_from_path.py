"""Open a PDF by file path — the most common entry point."""

import sopdf

doc = sopdf.open("../../tests/fixtures/simple.pdf")

print(f"Pages: {doc.page_count}")
print(f"Metadata: {doc.metadata}")
print(f"Encrypted: {doc.is_encrypted}")

doc.close()

# Preferred: use a context manager so the file handle is always released
with sopdf.open("../../tests/fixtures/simple.pdf") as doc:
    print(f"Pages (via context manager): {doc.page_count}")
