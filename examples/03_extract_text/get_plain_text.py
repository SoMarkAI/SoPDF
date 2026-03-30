"""Extract the full text of each page as a plain string."""

import sopdf

with sopdf.open("../../tests/fixtures/simple.pdf") as doc:
    for i, page in enumerate(doc.pages):
        text = page.get_text()
        print(f"--- Page {i} ---")
        print(text)
