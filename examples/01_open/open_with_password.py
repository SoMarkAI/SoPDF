"""Open a password-protected PDF."""

import sopdf

with sopdf.open("../../tests/fixtures/encrypted.pdf", password="secret") as doc:
    print(f"Pages: {doc.page_count}")
    print(f"Encrypted: {doc.is_encrypted}")
