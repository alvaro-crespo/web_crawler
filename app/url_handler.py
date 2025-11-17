#!/usr/bin/env python3
"""
URL handling for the web crawler.

Handles normalization and filtering of the URLs:
- single domain allowed
- resolve relative URLs
- filter by scheme and filetype.
- skip fragments
"""

import logging
import pathlib
from typing import Optional, Set
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)


class URLHandler:
    """Handles URL validation, filtering and normalization."""

    DEFAULT_ALLOWED_FILETYPES = {".html", ".php", ""}
    DEFAULT_ALLOWED_SCHEMES = {"http", "https"}

    def __init__(
        self,
        start_url: str,
        allowed_filetypes: Set[str] | None = None,
        allowed_schemes: Set[str] | None = None,
    ):
        """Initialize with the starting URL to determine allowed domain."""
        parsed = urlparse(start_url)
        self.allowed_domain = parsed.netloc.lower()
        if not self.allowed_domain:
            raise ValueError(f"Invalid starting URL: {start_url}")
        self.allowed_filetypes = allowed_filetypes or self.DEFAULT_ALLOWED_FILETYPES
        self.allowed_schemes = allowed_schemes or self.DEFAULT_ALLOWED_SCHEMES

    def normalize_url(self, url: str, base_url: Optional[str] = None) -> Optional[str]:
        """Resolve relative URLs to absolute and clean fragments"""
        if not url or url.startswith("#"):
            return None
        try:
            absolute = urljoin(base_url, url)
        except ValueError:
            return None
        parsed = urlparse(absolute)
        # Simple normalization dropping fragment
        normalized = parsed._replace(
            netloc=parsed.netloc.lower(),
            fragment="",
        )
        return normalized.geturl()

    def is_allowed(self, url: str) -> bool:
        """Filter by domain, scheme and file type."""
        parsed = urlparse(url)
        if parsed.netloc.lower() != self.allowed_domain:
            return False
        if parsed.scheme.lower() not in self.allowed_schemes:
            return False
        ext = pathlib.Path(parsed.path).suffix
        if ext not in self.allowed_filetypes:
            return False
        return True
