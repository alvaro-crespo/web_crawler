# Web Crawler

**Author:** Alvaro Crespo — alvarocrespo.se@gmail.com

A simple async web crawler that traverses all pages within a single subdomain.

Given a starting URL, the crawler:
- Crawls all pages on the same subdomain.
- Prints each URL visited and a list of links found on that page.
- Prints a summary at the end with the total number of pages visited and the crawl duration.

## Features
- Asynchronous crawling using asyncio and aiohttp for concurrent page fetching.
- Subdomain scoped, never follows external links (e.g. from `crawlme.monzo.com` to `facebook.com`).
- Keeps track of visited URLs to avoid duplicates.
- URL normalization and filtering encapsulated.


## Project Structure
Follows a modular layout with the Crawler and URL handler separated, plus their corresponding unit tests.
```text
.
├── app
│   ├── __init__.py
│   ├── crawler.py        # WebCrawler implementation
│   ├── url_handler.py    # URLHandler with normalization and filtering
│   └── tests
│       ├── test_crawler.py
│       └── test_url_handler.py
├── main.py               # CLI entrypoint
├── pytest.ini            # Pytest configuration
├── requirements.txt      # Dependencies
└── README.md
```

## Installation
Create a virtual environment, activate it and install dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage
Via command-line from project root: 

```bash
python main.py <START_URL> [--workers N]
# General case: default number of workers 10
python main.py https://crawlme.monzo.com/
# Example with more concurrent workers
python main.py https://crawlme.monzo.com/ --workers 20
```

## Behaviour and Design

### Async Architecture
- Use of `asyncio` with `aiohttp` for concurrent crawling to avoid I/O blocking.
- Fixed number of workers coroutines (`--workers`):
    - each worker pulls URLs from an `asyncio.Queue` (FIFO).
    - calls `process_url()` -> `fetch_page()` -> `extract_links()`.
    - enqueues new links back into the queue.
- This gives an explicit approach to concurrency without external frameworks.

### URL handling 
Encapsulated in `URLHandler` class (`url_handler.py`):
- Normalization: 
    - resolves relative paths against base URL.
    - remove fragments to avoid duplicate visits.
    - lower-cases the hostname.
- Filtering:
    - only allows URLs on the same domain as the starting URL.
    - only allows `http` and `https` schemes.
    - only allows `.html` or `.php` file types.

### Crawl strategy
- Uses a BFS queue: 
    - first discovered URLs are processed first.
    - gives more even coverage across the site rather than going deep down a path.
- Uses a set for visited duplication checks `O(1)`.

### Error Handling
- Individual page failures do not stop the entire craw process. Exceptions (e.g. timeouts) are caught and logged.
- Non html responses are skipped without raising errors.


## Dependencies
Listed in the `requirements.txt` file:
- `aiohttp`: async HTTP client.
- `beautifulsoup4`: HTML parser.
- `pytest` and `pytest-asyncio`: test suite.


## Testing
Use pytest for the test suite.
```bash
pytest

```
The goal was to cover the core behaviour. To check test coverage:
```bash
coverage run -m pytest
coverage report -m

```

## Trade-offs, limitations and future improvements

Within this ~4hr scope there were a few trade offs, and some areas of future improvements:

- Async vs sync: 
    - asynchronous I/O is more efficient than sequential requests, at the cost of more complex code.
- Memory vs disk:
    - The visited set of URLs and queued ones are stored in memory. This is simpler and faster, but has limits when scaling.
    - An improvement could be persisting results to a database for very large crawls.
- Best practices:
    - Add rate limiting to be respectful for servers, as of now the crawler sends requests as quickly as a worker is available.
    - Respect robots.txt standard regarding web crawl rules.
- Smarter error handling and retries:
    - Improve resilience by adding limited retries for transient errors (e.g. network issues).
- Test coverage:
    - The current test suite covers core functionalities, but it could be extended to improve coverage.
- Reporting:
    - The crawler prints each URL visited and links found. We could write results to a file or output results in a structured JSON format.
