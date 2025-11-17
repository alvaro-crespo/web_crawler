import argparse
import asyncio
import logging
import sys
import time

from app.crawler import WebCrawler

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    """Main entry point."""
    # Get args from CLI
    parser = argparse.ArgumentParser(
        description="Web crawler for single subdomain traversal"
    )
    parser.add_argument("url", help="Starting URL to crawl")
    parser.add_argument(
        "--workers",
        type=int,
        default=10,
        help="Number of concurrent workers (default: 10)",
    )
    args = parser.parse_args()
    start_time = time.monotonic()
    # Initialize crawler
    try:
        crawler = WebCrawler(args.url, max_workers=args.workers)
        await crawler.crawl()
    except Exception as e:
        logger.error(f"Crawling {args.url} failed: {e}")
        sys.exit(1)

    # Compute duration
    end_time = time.monotonic()
    duration = end_time - start_time
    print(f"Crawl Duration: {duration:.2f} seconds")


if __name__ == "__main__":
    asyncio.run(main())
