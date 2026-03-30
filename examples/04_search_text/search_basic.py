"""Search for a keyword and print all match bounding boxes."""

import sopdf

with sopdf.open("../../tests/fixtures/simple.pdf") as doc:
    matches = doc[0].search("sopdf")  # returns list[Rect]

    print(f"Found {len(matches)} match(es):")
    for i, rect in enumerate(matches):
        print(f"  [{i}] {rect}")
