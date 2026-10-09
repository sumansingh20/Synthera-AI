"""State definitions for the LangGraph research workflow.

The ResearchState is the central data structure that flows through every node
in the graph. Each agent reads from and writes to specific fields, enabling
clean hand-offs between the search, scrape, analyze, and synthesis phases.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Annotated, Any

from langgraph.graph.message import add_messages


class ResearchPhase(str, Enum):
    PLANNING = "planning"
    SEARCHING = "searching"
    SCRAPING = "scraping"
    ANALYZING = "analyzing"
    SYNTHESIZING = "synthesizing"
    COMPLETE = "complete"
    ERROR = "error"


class ResearchDepth(str, Enum):
    QUICK = "quick"           # single search pass, top 3 results
    MODERATE = "moderate"     # 2 hops, top 5 results per hop
    COMPREHENSIVE = "comprehensive"  # up to max_hops, full result set


@dataclass
class SourceDocument:
    """A scraped and processed web document."""
    url: str
    title: str
    content: str
    snippet: str = ""
    relevance_score: float = 0.0
    token_count: int = 0


@dataclass
class SearchResult:
    """Raw search result from the search provider."""
    title: str
    url: str
    snippet: str
    score: float = 0.0


class ResearchState(dict):
    """Typed state dictionary for the research graph.

    Using TypedDict-style access via dict subclass so LangGraph can
    serialize / checkpoint the state across nodes.
    """

    @staticmethod
    def default() -> dict[str, Any]:
        return {
            # Input
            "query": "",
            "depth": ResearchDepth.COMPREHENSIVE.value,
            "max_hops": 3,

            # Workflow tracking
            "phase": ResearchPhase.PLANNING.value,
            "current_hop": 0,
            "sub_queries": [],
            "messages": [],

            # Search results
            "search_results": [],       # list[SearchResult dict]
            "visited_urls": set(),

            # Scraped content
            "documents": [],            # list[SourceDocument dict]

            # RAG
            "rag_context": "",

            # Output
            "report": "",
            "citations": [],
            "follow_up_questions": [],

            # Errors
            "errors": [],
        }
