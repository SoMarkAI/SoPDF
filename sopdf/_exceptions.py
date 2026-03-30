"""
sopdf exceptions — all inherit from PDFError → RuntimeError.
"""


class PDFError(RuntimeError):
    """Base exception for all sopdf errors."""


class PasswordError(PDFError):
    """Raised when a password is required but missing, or the given password is wrong."""


class FileDataError(PDFError):
    """Raised when a PDF is corrupted or otherwise unreadable."""


class PageError(PDFError):
    """Raised when an invalid page index is requested."""
