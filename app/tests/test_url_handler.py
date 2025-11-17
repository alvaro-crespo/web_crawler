import pytest

from app.url_handler import URLHandler


class TestURLHandler:
    """Tests for URL handling logic."""

    def test_urlhandler_initialization(self):
        """Allowed domain from starting URL."""
        handler = URLHandler("https://Monzo.com/some/path")
        assert handler.allowed_domain == "monzo.com"

    def test_urlhandler_initialization_invalid_url(self):
        """Invalid starting URL raises ValueError."""
        with pytest.raises(ValueError):
            URLHandler("bad-url")

    def test_normalize_url_relative(self):
        """normalize_url should handle relative URLs."""
        handler = URLHandler("https://monzo.com")
        assert (
            handler.normalize_url("/page", "https://monzo.com")
            == "https://monzo.com/page"
        )

    def test_normalize_url_resolves_fragments(self):
        """normalize_url should handle fragment in URLs."""
        handler = URLHandler("https://monzo.com")
        assert (
            handler.normalize_url("https://MONZO.com/page#section")
            == "https://monzo.com/page"
        )
        assert handler.normalize_url("") is None
        assert handler.normalize_url("#fragment") is None

    def test_is_allowed_filters(self):
        """Filters for domain, scheme and file types are applied in is_allowed method."""
        handler = URLHandler("https://monzo.com")

        # Allow: same domain, http/https, extensions
        assert handler.is_allowed("https://monzo.com/index.html") is True
        assert handler.is_allowed("http://monzo.com/") is True
        assert handler.is_allowed("https://monzo.com/page") is True
        assert handler.is_allowed("https://monzo.com/script.php") is True
        # Not allowed: different domain
        assert handler.is_allowed("https://notmonzo.com/page") is False
        assert handler.is_allowed("https://notnotmonzo.com/page") is False
        # Not allowed: different schemas
        assert handler.is_allowed("mailto:test@monzo.com") is False
        assert handler.is_allowed("javascript:void(0)") is False
        # Not allowed: file types
        assert handler.is_allowed("https://monzo.com/image.png") is False
