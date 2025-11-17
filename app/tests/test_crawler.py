import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.crawler import WebCrawler


class TestWebCrawler:
    """Tests for the WebCrawler."""

    @pytest.mark.asyncio
    async def test_crawler_initialization(self):
        """Basic WebCrawler initialization."""
        crawler = WebCrawler("https://example.com", max_workers=5)
        assert crawler.start_url == "https://example.com"
        assert crawler.max_workers == 5
        assert crawler.visited == set()
        assert crawler.queue.qsize() == 0
        assert crawler.session is None

    def test_extract_links_filters_external(self):
        """Allow same domain URLs and exclude external links."""
        crawler = WebCrawler("https://example.com")
        html = """
        <html>
          <body>
            <a href='/page1'>Link 1</a>
            <a href='https://example.com/page2'>Link 2</a>
            <a href='https://notnotexample.com/page'>External</a>
          </body>
        </html>
        """
        links = crawler.extract_links(html, "https://example.com/")
        assert "https://example.com/page1" in links
        assert "https://example.com/page2" in links
        assert "https://notnotexample.com/page" not in links

    @pytest.mark.asyncio
    async def test_fetch_page_success(self):
        """HTML content is properly retrieved from page."""
        crawler = WebCrawler("https://example.com")
        crawler.session = MagicMock()
        mock_resp = AsyncMock()
        mock_resp.headers = {"Content-Type": "text/html; charset=utf-8"}
        mock_resp.text = AsyncMock(return_value="<html><body>Test</body></html>")
        mock_resp.raise_for_status = MagicMock()

        crawler.session.get.return_value.__aenter__.return_value = mock_resp
        crawler.session.get.return_value.__aexit__.return_value = None

        html = await crawler.fetch_page("https://example.com")

        assert html == "<html><body>Test</body></html>"

    @pytest.mark.asyncio
    async def test_fetch_page_non_html(self):
        """Non html page is filtered ahead of processing."""
        crawler = WebCrawler("https://example.com")
        crawler.session = MagicMock()
        mock_resp = AsyncMock()
        mock_resp.headers = {"Content-Type": "image/png"}
        mock_resp.text = AsyncMock(return_value="png image")
        mock_resp.raise_for_status = MagicMock()

        crawler.session.get.return_value.__aenter__.return_value = mock_resp
        crawler.session.get.return_value.__aexit__.return_value = None

        html = await crawler.fetch_page("https://example.com/image.png")
        assert html is None

    @pytest.mark.asyncio
    async def test_process_url_links_to_queue(self):
        """Process URLs method adds corresponding links to queues."""
        crawler = WebCrawler("https://example.com")

        mock_html = """
        <html>
          <body>
            <a href="/page1">Page 1</a>
            <a href="/page2">Page 2</a>
            <a href="https://notexample.com/page">External</a>
          </body>
        </html>
        """

        with patch.object(crawler, "fetch_page", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_html

            await crawler.process_url("https://example.com")
            # External link gets filtered out
            assert 'Visited: "https://example.com" in captured.out'
            assert "Found 2 links: in captured.out"

            assert "https://example.com/page1" in crawler.visited
            assert "https://example.com/page2" in crawler.visited

            assert crawler.queue.qsize() == 2
            queued = [crawler.queue.get_nowait() for _ in range(2)]
            assert "https://example.com/page1" in queued
            assert "https://example.com/page2" in queued

    @pytest.mark.asyncio
    async def test_no_duplicates_visited_set(self):
        """Visited URL is not added to the queue to process."""
        crawler = WebCrawler("https://example.com")

        visited_link = "https://example.com/visited"
        crawler.visited.add(visited_link)
        mock_html = f'<a href="{visited_link}">Link</a>'

        with patch.object(crawler, "fetch_page", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_html
            # Page in visited set is not added to the queue
            await crawler.process_url("https://example.com")
            assert crawler.queue.qsize() == 0

    @pytest.mark.asyncio
    async def test_worker_processes_queue(self):
        """Worker processes URL from the queue."""
        crawler = WebCrawler("https://example.com")

        test_url = "https://example.com/test"
        await crawler.queue.put(test_url)

        crawler.process_url = AsyncMock()
        worker_task = asyncio.create_task(crawler.worker())
        await crawler.queue.join()

        crawler.process_url.assert_called_with(test_url)
        worker_task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await worker_task
