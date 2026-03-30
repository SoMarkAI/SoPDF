"""
sopdf.merge — module-level function to merge multiple PDFs into one.
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

import pikepdf
import pypdfium2 as pdfium

from ._exceptions import FileDataError, PasswordError


def merge(
    inputs: list[Union[str, Path]],
    output: Union[str, Path],
) -> None:
    """Merge multiple PDFs into a single output file.

    Parameters
    ----------
    inputs:
        Ordered list of PDF file paths to concatenate.
    output:
        Destination file path.
    """
    if not inputs:
        raise ValueError("inputs must contain at least one file path.")

    merged = pikepdf.new()
    for src in inputs:
        try:
            with pikepdf.open(str(src)) as doc:
                for page in doc.pages:
                    merged.pages.append(page)
        except pikepdf.PasswordError as exc:
            raise PasswordError(f"Password required for {src}: {exc}") from exc
        except pikepdf.PdfError as exc:
            raise FileDataError(f"Cannot read {src}: {exc}") from exc

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    merged.save(str(output))
    merged.close()
