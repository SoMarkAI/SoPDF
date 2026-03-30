"""Extract text only from a specific rectangular region of the page."""

import sopdf

with sopdf.open("../../tests/fixtures/simple.pdf") as doc:
    # Define a region in PDF points (top-left area of an A4-ish page)
    region = sopdf.Rect(0, 650, 612, 792)

    text = doc[0].get_text(rect=region)
    print("Text in region:", repr(text))

    blocks = doc[0].get_text_blocks(rect=region)
    print(f"Blocks in region: {len(blocks)}")
