"""Scraper agent — fetches and cleans web content from search result URLs.

Handles concurrent scraping with rate limiting, error recovery, and
content extraction using BeautifulSoup. Feeds cleaned documents into
the RAG pipeline for storage and retrieval.
"""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
from bs4 import BeautifulSoup

from synthera.config import settings
from synthera.agents.states import ResearchPhase
from synthera.utils import get_logger, clean_html, truncate_text, estimate_tokens

logger = get_logger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

EXCLUDED_DOMAINS = {
    "youtube.com", "twitter.com", "x.com", "facebook.com",
    "instagram.com", "tiktok.com", "reddit.com",
}


async def _scrape_single_url(client: httpx.AsyncClient, url: str) -> dict | None:
    """Fetch and parse a single URL, returning a document dict or None on failure."""
    try:
        response = await client.get(url, headers=HEADERS, timeout=settings.request_timeout)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")

        # Remove noise elements
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            tag.decompose()

        title = soup.title.string.strip() if soup.title and soup.title.string else url

        # Extract main content — prioritize <article> or <main>
        main_content = soup.find("article") or soup.find("main") or soup.find("body")
        raw_text = main_content.get_text(separator=" ", strip=True) if main_content else ""

        if len(raw_text) < 100:
            logger.warning("Skipping %s — content too short (%d chars)", url, len(raw_text))
            return None

        content = truncate_text(raw_text, max_chars=8000)

        return {
            "url": url,
            "title": title,
            "content": content,
            "snippet": truncate_text(raw_text, 300),
            "token_count": estimate_tokens(content),
        }

    except httpx.HTTPStatusError as e:
        logger.warning("HTTP %d for %s", e.response.status_code, url)
        return None
    except Exception as e:
        logger.warning("Scrape failed for %s: %s", url, str(e)[:100])
        return None


def _should_scrape(url: str, visited: set) -> bool:
    """Check if a URL should be scraped based on domain rules and visit history."""
    if url in visited:
        return False
    try:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.lower()
        return not any(exc in domain for exc in EXCLUDED_DOMAINS)
    except Exception:
        return False


async def scrape_sources(state: dict[str, Any]) -> dict[str, Any]:
    """Scrape URLs from search results concurrently.

    Node: SEARCHING → SCRAPING → ANALYZING
    """
    search_results = state.get("search_results", [])
    visited = set(state.get("visited_urls", set()))
    existing_docs = list(state.get("documents", []))

    urls_to_scrape = [
        r["url"] for r in search_results
        if _should_scrape(r.get("url", ""), visited)
    ][:settings.max_scrape_concurrent]

    if not urls_to_scrape:
        logger.info("No new URLs to scrape. Moving to analysis.")
        return {"phase": ResearchPhase.ANALYZING.value}

    logger.info("Scraping %d URLs (concurrency=%d)", len(urls_to_scrape), settings.max_scrape_concurrent)

    semaphore = asyncio.Semaphore(settings.max_scrape_concurrent)

    async def _limited_scrape(client: httpx.AsyncClient, url: str) -> dict | None:
        async with semaphore:
            return await _scrape_single_url(client, url)

    async with httpx.AsyncClient(follow_redirects=True) as client:
        tasks = [_limited_scrape(client, url) for url in urls_to_scrape]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    new_docs = []
    for result in results:
        if isinstance(result, dict):
            new_docs.append(result)
            visited.add(result["url"])

    logger.info("Successfully scraped %d/%d URLs", len(new_docs), len(urls_to_scrape))

    return {
        "documents": existing_docs + new_docs,
        "visited_urls": visited,
        "phase": ResearchPhase.ANALYZING.value,
    }
