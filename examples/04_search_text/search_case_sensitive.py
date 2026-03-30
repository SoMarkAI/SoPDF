"""Case-sensitive vs case-insensitive search."""

import sopdf

with sopdf.open("../../tests/fixtures/simple.pdf") as doc:
    page = doc[0]

    # Case-insensitive (default)
    insensitive = page.search("hello")
    print(f"Case-insensitive matches: {len(insensitive)}")

    # Exact case match
    sensitive = page.search("Hello", match_case=True)
    print(f"Case-sensitive matches for 'Hello': {len(sensitive)}")
