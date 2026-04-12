"""Write (update) document metadata and save the result."""

import sopdf

with sopdf.open("../../tests/fixtures/simple.pdf") as doc:
    print("Before:")
    print(f"  title  = {doc.metadata.title!r}")
    print(f"  author = {doc.metadata.author!r}")

    # Set fields via attribute assignment — identical pattern to page.rotation = 90
    doc.metadata.title   = "Annual Report 2025"
    doc.metadata.author  = "Kevin Qiu"
    doc.metadata.subject = "Financial summary for FY2025"
    doc.metadata.keywords = "finance report annual 2025"

    print("\nAfter (in memory):")
    print(f"  title  = {doc.metadata.title!r}")
    print(f"  author = {doc.metadata.author!r}")

    # Persist to a new file
    doc.save("metadata_output.pdf")
    print("\nSaved metadata_output.pdf")

# Verify round-trip
with sopdf.open("metadata_output.pdf") as doc2:
    print("\nVerification (re-opened):")
    print(f"  title   = {doc2.metadata.title!r}")
    print(f"  author  = {doc2.metadata.author!r}")
    print(f"  subject = {doc2.metadata.subject!r}")
