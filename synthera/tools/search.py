"""Web search tool — abstraction layer over Tavily and SerpAPI.

Provides a unified interface for executing search queries across
different search providers. Results are normalized into a consistent
format regardless of the underlying provider.
"""

from __future__ import annotations

import asyncio
from typing import Any

from synthera.config import settings
from synthera.agents.states import ResearchPhase
from synthera.utils import get_logger

logger = get_logger(__name__)


async def _search_tavily(query: str, max_results: int) -> list[dict]:
    """Execute search using Tavily API."""
    from tavily import TavilyClient

    client = TavilyClient(api_key=settings.tavily_api_key)

    # Tavily's search is synchronous, run in executor
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        lambda: client.search(
            query=query,
            max_results=max_results,
            search_depth="advanced",
            include_raw_content=False,
        ),
    )

    results = []
    for item in response.get("results", []):
        results.append({
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "snippet": item.get("content", ""),
            "score": item.get("score", 0.0),
        })

    return results


async def _search_serpapi(query: str, max_results: int) -> list[dict]:
    """Execute search using SerpAPI."""
    import httpx

    params = {
        "q": query,
        "api_key": settings.serpapi_api_key,
        "engine": "google",
        "num": max_results,
    }

    async with httpx.AsyncClient() as client:
        response = await client.get("https://serpapi.com/search", params=params, timeout=20)
        response.raise_for_status()
        data = response.json()

    results = []
    for item in data.get("organic_results", []):
        results.append({
            "title": item.get("title", ""),
            "url": item.get("link", ""),
            "snippet": item.get("snippet", ""),
            "score": item.get("position", 0),
        })

    return results[:max_results]


async def execute_search(state: dict[str, Any]) -> dict[str, Any]:
    """Execute web searches for all pending sub-queries.

    Node: SEARCHING → SCRAPING
    Searches each sub-query that hasn't been searched yet and aggregates results.
    """
    sub_queries = state.get("sub_queries", [])
    existing_results = list(state.get("search_results", []))
    visited_urls = set(state.get("visited_urls", set()))

    # Determine which queries to search (last batch of new queries)
    current_hop = state.get("current_hop", 1)
    depth = state.get("depth", "comprehensive")
    max_results = {"quick": 3, "moderate": 5, "comprehensive": settings.max_search_results}.get(depth, 5)

    # Only search queries from the current hop
    queries_to_search = sub_queries[-(max_results):]

    logger.info("Searching %d queries (hop=%d, provider=%s)", len(queries_to_search), current_hop, settings.search_provider)

    search_fn = _search_tavily if settings.search_provider == "tavily" else _search_serpapi

    all_new_results = []
    for query in queries_to_search:
        try:
            results = await search_fn(query, max_results=max_results)
            # Filter out already-visited URLs
            fresh = [r for r in results if r["url"] not in visited_urls]
            all_new_results.extend(fresh)
            logger.info("Query '%s' returned %d results (%d new)", query[:50], len(results), len(fresh))
        except Exception as e:
            logger.error("Search failed for '%s': %s", query[:50], str(e))

    # Deduplicate by URL
    seen_urls = {r["url"] for r in existing_results}
    for result in all_new_results:
        if result["url"] not in seen_urls:
            existing_results.append(result)
            seen_urls.add(result["url"])

    logger.info("Total search results: %d", len(existing_results))

    return {
        "search_results": existing_results,
        "phase": ResearchPhase.SCRAPING.value,
    }
