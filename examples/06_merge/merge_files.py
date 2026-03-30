"""Merge multiple PDF files into one using the module-level merge function."""

import sopdf

sopdf.merge(
    ["../../tests/fixtures/simple.pdf", "../../tests/fixtures/multipage.pdf"],
    output="merged.pdf",
)
print("Created merged.pdf")

with sopdf.open("merged.pdf") as doc:
    print(f"Total pages: {doc.page_count}")  # 1 + 5 = 6
