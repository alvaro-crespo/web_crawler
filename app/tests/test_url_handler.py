import pytest

from app.url_handler import URLHandler


class TestURLHandler:
    """Tests for URL handling logic."""

    def test_urlhandler_initialization(self):
        """Allowed domain from starting URL."""
        handler = URLHandler("https://Example.com/some/path")
        assert handler.allowed_domain == "example.com"

    def test_urlhandler_initialization_invalid_url(self):
        """Invalid starting URL raises ValueError."""
        with pytest.raises(ValueError):
            URLHandler("bad-url")

    def test_normalize_url_relative(self):
        """normalize_url should handle relative URLs."""
        handler = URLHandler("https://example.com")
        assert (
            handler.normalize_url("/page", "https://example.com")
            == "https://example.com/page"
        )

    def test_normalize_url_resolves_fragments(self):
        """normalize_url should handle fragment in URLs."""
        handler = URLHandler("https://example.com")
        assert (
            handler.normalize_url("https://EXAMPLE.com/page#section")
            == "https://example.com/page"
        )
        assert handler.normalize_url("") is None
        assert handler.normalize_url("#fragment") is None

    def test_is_allowed_filters(self):
        """Filters for domain, scheme and file types are applied
        in is_allowed method."""
        handler = URLHandler("https://example.com")

        # Allow: same domain, http/https, extensions
        assert handler.is_allowed("https://example.com/index.html") is True
        assert handler.is_allowed("http://example.com/") is True
        assert handler.is_allowed("https://example.com/page") is True
        assert handler.is_allowed("https://example.com/script.php") is True
        # Not allowed: different domain
        assert handler.is_allowed("https://notexample.com/page") is False
        assert handler.is_allowed("https://notnotexample.com/page") is False
        # Not allowed: different schemas
        assert handler.is_allowed("mailto:test@example.com") is False
        assert handler.is_allowed("javascript:void(0)") is False
        # Not allowed: file types
        assert handler.is_allowed("https://example.com/image.png") is False
