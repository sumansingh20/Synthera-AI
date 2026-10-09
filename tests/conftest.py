"""Shared test fixtures and configuration."""

from __future__ import annotations

import os

import pytest

# Set test environment variables before importing app modules
os.environ.setdefault("OPENAI_API_KEY", "test-key-not-real")
os.environ.setdefault("TAVILY_API_KEY", "test-tavily-key")
os.environ.setdefault("LANGCHAIN_TRACING_V2", "false")


@pytest.fixture
def sample_search_results() -> list[dict]:
    """Sample search results for testing."""
    return [
        {
            "title": "Quantum Computing Advances 2025",
            "url": "https://example.com/quantum-advances",
            "snippet": "Recent breakthroughs in quantum error correction have brought us closer to fault-tolerant quantum computing.",
            "score": 0.95,
        },
        {
            "title": "The State of Modern Research",
            "url": "https://example.com/ai-research",
            "snippet": "Large language models continue to advance, with new architectures pushing the boundaries of capability.",
            "score": 0.88,
        },
        {
            "title": "Machine Learning in Healthcare",
            "url": "https://example.com/ml-healthcare",
            "snippet": "Data-driven diagnostics are showing promising results in early cancer detection studies.",
            "score": 0.82,
        },
    ]


@pytest.fixture
def sample_documents() -> list[dict]:
    """Sample scraped documents for testing."""
    return [
        {
            "url": "https://example.com/quantum-advances",
            "title": "Quantum Computing Advances 2025",
            "content": (
                "Quantum computing has seen remarkable progress in recent years. "
                "Researchers at major labs have demonstrated quantum error correction "
                "codes that significantly reduce error rates. The development of "
                "topological qubits represents a major milestone. Commercial quantum "
                "computers are expected to solve certain optimization problems faster "
                "than classical supercomputers within the next decade."
            ),
            "snippet": "Recent breakthroughs in quantum error correction...",
            "token_count": 150,
        },
        {
            "url": "https://example.com/ai-research",
            "title": "The State of Modern Research",
            "content": (
                "Artificial intelligence research continues at an unprecedented pace. "
                "Transformer architectures have been adapted for everything from protein "
                "folding to autonomous driving. Multi-modal models that combine vision "
                "and language understanding represent the next frontier. The focus is "
                "shifting from scaling to efficiency and alignment."
            ),
            "snippet": "Large language models continue to advance...",
            "token_count": 130,
        },
    ]


@pytest.fixture
def sample_research_state(sample_search_results, sample_documents) -> dict:
    """Complete research state for testing."""
    return {
        "query": "What are the latest advances in quantum computing?",
        "depth": "comprehensive",
        "max_hops": 3,
        "phase": "analyzing",
        "current_hop": 1,
        "sub_queries": [
            "quantum computing breakthroughs 2025",
            "quantum error correction advances",
            "commercial quantum computing timeline",
        ],
        "messages": [],
        "search_results": sample_search_results,
        "visited_urls": {"https://example.com/quantum-advances", "https://example.com/ai-research"},
        "documents": sample_documents,
        "rag_context": "Quantum computing has seen remarkable progress...",
        "report": "",
        "citations": [],
        "follow_up_questions": [],
        "errors": [],
    }
