"""Export the outline as a flat list — compatible with PyMuPDF's get_toc() format."""

import sopdf

with sopdf.open("../../tests/fixtures/outline.pdf") as doc:
    # to_list() performs a depth-first traversal and returns
    # [{"level": int, "title": str, "page": int}, ...]
    flat = doc.outline.to_list()

    print(f"{'Level':<8} {'Page':<8} Title")
    print("-" * 40)
    for entry in flat:
        indent = "  " * entry["level"]
        print(f"{entry['level']:<8} {entry['page'] + 1:<8} {indent}{entry['title']}")

    print()
    # Access individual OutlineItem objects for richer data
    for item in doc.outline.items:
        print(f"{item.title!r}  →  page {item.page + 1}  "
              f"({len(item.children)} sub-item(s))")
        d = item.to_dict()   # serialise to plain dict if needed
        print(f"  as dict: {d}")
