"""Attempt to open and repair a corrupted PDF.

pypdfium2 (PDFium) applies fault-tolerant parsing; pikepdf rebuilds the
structure cleanly on save. Together they can rescue many lightly damaged files.
"""

import sopdf

try:
    with sopdf.open("../../tests/fixtures/corrupted.pdf") as doc:
        print(f"Opened corrupted.pdf — {doc.page_count} page(s) recovered")
        # Re-saving with garbage=True rebuilds the object graph cleanly
        doc.save("repaired.pdf", compress=True, garbage=True)
    print("Saved repaired.pdf")
except sopdf.FileDataError as e:
    print(f"File is too damaged to recover: {e}")
