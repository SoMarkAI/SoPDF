"""Extract text with bounding-box metadata."""

import sopdf

with sopdf.open("../../tests/fixtures/simple.pdf") as doc:
    blocks = doc[0].get_text_blocks()  # list[TextBlock]
    for block in blocks:
        print(f"Text : {block.text!r}")
        print(f"Rect : {block.rect}")
        print()

    # As plain dicts — useful for serialisation
    blocks_dict = doc[0].get_text_blocks(format="dict")
    print("Dict format:", blocks_dict)
