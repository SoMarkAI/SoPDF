"""Render a page directly to an image file."""

import sopdf

with sopdf.open("../../tests/fixtures/simple.pdf") as doc:
    doc[0].render_to_file("page0.png", dpi=300)         # high-resolution PNG
    doc[0].render_to_file("page0_thumb.jpeg", dpi=72, format="jpeg")  # thumbnail

print("Saved page0.png and page0_thumb.jpeg")
