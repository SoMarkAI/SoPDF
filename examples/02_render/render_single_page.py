"""Render the first page to PNG bytes at 150 DPI."""

import sopdf

with sopdf.open("../../tests/fixtures/simple.pdf") as doc:
    img_bytes = doc[0].render(dpi=150)  # returns PNG bytes by default

print(f"Rendered {len(img_bytes):,} bytes of PNG data")
