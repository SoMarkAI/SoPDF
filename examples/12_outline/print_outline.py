"""Print the document outline (table of contents) as a nested tree."""

import sopdf

with sopdf.open("../../tests/fixtures/outline.pdf") as doc:
    outline = doc.outline

    print(f"Outline: {outline}")          # Outline(top_level=2, total=4)
    print(f"Total items: {len(outline)}")
    print(f"Has outline: {bool(outline)}")
    print()

    # Recursive tree traversal
    def print_tree(items, indent=0):
        for item in items:
            prefix = "  " * indent + ("└─ " if indent else "")
            print(f"{prefix}[p{item.page + 1}] {item.title}")
            print_tree(item.children, indent + 1)

    print_tree(doc.outline.items)
