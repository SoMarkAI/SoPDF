"""Search and retrieve the surrounding text block for each match."""

import sopdf

with sopdf.open("../../tests/fixtures/simple.pdf") as doc:
    results = doc[0].search_text_blocks("sopdf")
    # Each result: {'text': str, 'rect': Rect, 'match_rect': Rect}

    for item in results:
        print(f"Match rect  : {item['match_rect']}")
        print(f"Block rect  : {item['rect']}")
        print(f"Context text: {item['text']!r}")
        print()
