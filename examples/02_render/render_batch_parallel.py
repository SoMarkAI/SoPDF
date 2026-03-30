"""Render all pages using multiprocessing for maximum throughput."""

import sopdf

with sopdf.open("../../tests/fixtures/multipage.pdf") as doc:
    # parallel=True spawns worker processes — ideal for large documents
    images = sopdf.render_pages(doc.pages, dpi=150, parallel=True)

print(f"Rendered {len(images)} pages in parallel")
