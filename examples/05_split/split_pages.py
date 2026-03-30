"""Extract a subset of pages into a new document."""

import sopdf

with sopdf.open("../../tests/fixtures/multipage.pdf") as doc:
    print(f"Original pages: {doc.page_count}")

    # Extract pages 0, 2, 4 (0-based indices)
    new_doc = doc.split(pages=[0, 2, 4])
    print(f"Split document pages: {new_doc.page_count}")
    new_doc.close()

    # Or save directly to a file
    doc.split(pages=[0, 1], output="chapter1.pdf")
    print("Saved chapter1.pdf")
