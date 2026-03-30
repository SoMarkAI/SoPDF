"""Save with compression and garbage collection to minimise file size."""

import sopdf

with sopdf.open("../../tests/fixtures/multipage.pdf") as doc:
    doc.save(
        "output_compressed.pdf",
        compress=True,    # deflate-compress streams
        garbage=True,     # remove unreferenced objects
        linearize=False,  # fast web view (disabled here)
    )

print("Saved output_compressed.pdf")
