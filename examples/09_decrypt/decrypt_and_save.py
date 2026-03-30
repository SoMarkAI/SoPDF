"""Open an encrypted PDF and save a password-free copy."""

import sopdf

with sopdf.open("../../tests/fixtures/encrypted.pdf", password="secret") as doc:
    print(f"Encrypted: {doc.is_encrypted}")
    # Save without specifying encryption — pikepdf strips it by default
    doc.save("decrypted.pdf")

with sopdf.open("decrypted.pdf") as doc:
    print(f"Decrypted file encrypted: {doc.is_encrypted}")  # False
