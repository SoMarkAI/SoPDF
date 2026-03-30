"""Append one open document's pages to another, then save."""

import sopdf

doc_a = sopdf.open("../../tests/fixtures/simple.pdf")
doc_b = sopdf.open("../../tests/fixtures/multipage.pdf")

doc_a.append(doc_b)           # adds all pages from doc_b into doc_a
print(f"Combined pages: {doc_a.page_count}")

doc_a.save("combined.pdf")    # save the merged result
doc_a.close()
doc_b.close()
