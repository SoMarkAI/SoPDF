"""Read document metadata — title, author, dates, and all standard fields."""

import sopdf

with sopdf.open("../../tests/fixtures/metadata.pdf") as doc:
    meta = doc.metadata

    # Individual typed properties
    print(f"Title:    {meta.title}")
    print(f"Author:   {meta.author}")
    print(f"Subject:  {meta.subject}")
    print(f"Keywords: {meta.keywords}")
    print(f"Creator:  {meta.creator}")
    print(f"Producer: {meta.producer}")

    # Date fields — raw PDF string and parsed Python datetime
    print(f"\nCreation date (raw):    {meta.creation_date}")
    print(f"Creation date (parsed): {meta.creation_datetime}")
    print(f"Mod date (raw):         {meta.mod_date}")
    print(f"Mod date (parsed):      {meta.mod_datetime}")

    # Export all fields as a plain dict (lowercase keys)
    print(f"\nAll fields as dict: {meta.to_dict()}")

    # Dict-style access — backward-compatible with the old doc.metadata dict
    print(f"\nmeta['title'] = {meta['title']}")
