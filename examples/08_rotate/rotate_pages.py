"""Rotate individual pages and save the result."""

import sopdf

with sopdf.open("../../tests/fixtures/simple.pdf") as doc:
    print(f"Before: page 0 rotation = {doc[0].rotation}°")

    doc[0].rotation = 90   # assignment shorthand
    # or: doc[0].set_rotation(90)

    print(f"After:  page 0 rotation = {doc[0].rotation}°")
    doc.save("rotated_output.pdf")

print("Saved rotated_output.pdf")
