#!/usr/bin/env python3
"""
The web crawler. A simple async crawler for subdomain traversal.

The crawler visits all pages within the starting URLs, prints
each URL visited and a list of links found on that page.
"""

import asyncio
import logging
from typing import List, Optional

import aiohttp
from bs4 import BeautifulSoup

from .url_handler import URLHandler

logger = logging.getLogger(__name__)


class WebCrawler:
    """Asynchronous web crawler for single subdomain traversal."""

    def __init__(self, start_url: str, max_workers: int = 10):
        """
        Initialize the crawler.

        Args:
            start_url: Starting URL domain for crawling
            max_workers: Maximum number of concurrent workers
        """
        self.start_url = start_url
        self.max_workers = max_workers
        # URL handler
        self.url_handler = URLHandler(start_url)
        # Manage states
        self.queue: asyncio.Queue = asyncio.Queue()
        self.visited = set()
        # HTTP client session
        self.session: Optional[aiohttp.ClientSession] = None

    async def fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch a page and return its content.
        """
        try:
            async with self.session.get(
                url, timeout=aiohttp.ClientTimeout(total=30), allow_redirects=True
            ) as response:
                response.raise_for_status()
                # Process only html
                if "text/html" not in response.headers.get("Content-Type", ""):
                    logger.debug(f"Skiping {url} without html content")
                    return None
                return await response.text()
        except asyncio.TimeoutError:
            logger.warning(f"Timeout fetching {url}")
            return None
        except Exception:
            logger.error(f"Error fetching {url}")
            return None

    def extract_links(self, html: str, base_url: str) -> List[str]:
        """
        Extract all links from HTML content.
        """
        links = []
        try:
            soup = BeautifulSoup(html, "html.parser")
            # Normalize and filter href
            for tag in soup.find_all("a"):
                href = tag.get("href")
                normalized = self.url_handler.normalize_url(href, base_url)
                if normalized and self.url_handler.is_allowed(normalized):
                    links.append(normalized)
        except Exception as e:
            logger.error(f"Error parsing HTML from {base_url}: {e}")
        return links

    async def process_url(self, url: str):
        """Process a single URL: fetch, parse html and extract links."""
        try:
            # Fetch page content. Skip it if not HTML or error
            html = await self.fetch_page(url)
            if not html:
                return
            # Extract links from HTML
            links = self.extract_links(html, url)

            # Print results
            print(f"Visited: {url}")
            print(f"  Found {len(links)} links:")
            for link in links:
                print(f"    - {link}")

            # Mark links as visited and add them to the queue
            for link in links:
                if link not in self.visited:
                    self.visited.add(link)
                    await self.queue.put(link)
        except Exception as e:
            logger.error(f"Error processing {url}: {e}")

    async def worker(self):
        """
        Worker that processes URLs to crawl from the queue.
        """
        while True:
            try:
                url = await self.queue.get()
                try:
                    await self.process_url(url)
                finally:
                    self.queue.task_done()
            except Exception as e:
                logger.error(f"Worker error: {e}")
                self.queue.task_done()

    async def crawl(self):
        """
        Start web crawling.
        """
        print(
            f"Starting crawl of {self.start_url} with {self.max_workers}"
            f" concurrent workers"
        )

        # Normalize starting URL
        normalized_start = self.url_handler.normalize_url(
            self.start_url, self.start_url
        )
        if not normalized_start:
            print(f"Error: Invalid starting URL: {self.start_url}")
            return
        # Initialize queue and mark domain as visited
        self.visited.add(normalized_start)
        self.queue.put_nowait(normalized_start)

        # Create HTTP session
        self.session = aiohttp.ClientSession()

        workers = []
        try:
            # Start worker tasks
            for _ in range(self.max_workers):
                workers.append(asyncio.create_task(self.worker()))
            await self.queue.join()
        finally:
            # Clean up workers
            for w in workers:
                w.cancel()
            # Wait for workers to actually stop
            await asyncio.gather(*workers, return_exceptions=True)
            await self.session.close()

        # Print summary
        print(f"{'=' * 50}")
        print(f"Crawl of {self.start_url} completed")
        print(f"Total pages visited: {len(self.visited)}")
        print(f"{'=' * 50}")
