"""Save every page as an individual PDF file."""

import sopdf

with sopdf.open("../../tests/fixtures/multipage.pdf") as doc:
    # Outputs page_0.pdf, page_1.pdf, … into the given directory
    doc.split_each(output_dir="pages/")
    print(f"Saved {doc.page_count} individual page files to pages/")
