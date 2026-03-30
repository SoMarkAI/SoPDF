"""Render all pages of a document sequentially."""

import sopdf

with sopdf.open("../../tests/fixtures/multipage.pdf") as doc:
    images = sopdf.render_pages(doc.pages, dpi=150)  # list[bytes]

for i, img in enumerate(images):
    print(f"Page {i}: {len(img):,} bytes")
