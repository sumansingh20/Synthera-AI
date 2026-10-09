"""LangGraph orchestration — defines the multi-agent research workflow.

The graph implements a cyclic, multi-hop research pipeline:

    ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌────────────┐
    │  PLAN    │────▶│  SEARCH  │────▶│  SCRAPE  │────▶│  ANALYZE   │
    └──────────┘     └──────────┘     └──────────┘     └────────────┘
                           ▲                                  │
                           │     (if more hops needed)        │
                           └──────────────────────────────────┘
                                                              │
                                                    (if done) ▼
                                                     ┌──────────────┐
                                                     │  SYNTHESIZE  │
                                                     └──────────────┘
                                                              │
                                                              ▼
                                                     ┌──────────────┐
                                                     │   COMPLETE   │
                                                     └──────────────┘
"""

from __future__ import annotations

from langgraph.graph import StateGraph, END

from synthera.agents.states import ResearchState, ResearchPhase
from synthera.agents.researcher import plan_research, analyze_gaps
from synthera.agents.scraper import scrape_sources
from synthera.agents.synthesizer import synthesize_report
from synthera.tools.search import execute_search
from synthera.rag.retriever import store_and_retrieve
from synthera.utils import get_logger

logger = get_logger(__name__)


def _route_after_analysis(state: dict) -> str:
    """Decide whether to do another search hop or move to synthesis."""
    phase = state.get("phase", "")
    if phase == ResearchPhase.SEARCHING.value:
        return "search"
    return "synthesize"


def _route_after_scrape(state: dict) -> str:
    """Route from scraping to RAG storage then analysis."""
    return "rag_store"


def build_research_graph() -> StateGraph:
    """Construct and compile the LangGraph research workflow.

    Returns:
        Compiled StateGraph ready for invocation.
    """
    workflow = StateGraph(dict)

    # ── Register Nodes ───────────────────────────────────
    workflow.add_node("plan", plan_research)
    workflow.add_node("search", execute_search)
    workflow.add_node("scrape", scrape_sources)
    workflow.add_node("rag_store", store_and_retrieve)
    workflow.add_node("analyze", analyze_gaps)
    workflow.add_node("synthesize", synthesize_report)

    # ── Define Edges ─────────────────────────────────────
    workflow.set_entry_point("plan")

    # Plan → Search
    workflow.add_edge("plan", "search")

    # Search → Scrape
    workflow.add_edge("search", "scrape")

    # Scrape → RAG Store
    workflow.add_edge("scrape", "rag_store")

    # RAG Store → Analyze
    workflow.add_edge("rag_store", "analyze")

    # Analyze → conditional: back to Search or forward to Synthesize
    workflow.add_conditional_edges(
        "analyze",
        _route_after_analysis,
        {
            "search": "search",
            "synthesize": "synthesize",
        },
    )

    # Synthesize → END
    workflow.add_edge("synthesize", END)

    graph = workflow.compile()
    logger.info("Research graph compiled successfully")

    return graph


async def run_research(query: str, depth: str = "comprehensive", max_hops: int = 3) -> dict:
    """Execute the full research pipeline for a given query.

    Args:
        query: The research question.
        depth: Research depth — 'quick', 'moderate', or 'comprehensive'.
        max_hops: Maximum number of search-scrape-analyze cycles.

    Returns:
        Final state dict containing the report, citations, and metadata.
    """
    graph = build_research_graph()

    initial_state = ResearchState.default()
    initial_state.update({
        "query": query,
        "depth": depth,
        "max_hops": max_hops,
    })

    logger.info("Starting research pipeline: query='%s', depth=%s, max_hops=%d", query, depth, max_hops)

    final_state = await graph.ainvoke(initial_state)

    logger.info(
        "Research complete: %d documents, %d citations, phase=%s",
        len(final_state.get("documents", [])),
        len(final_state.get("citations", [])),
        final_state.get("phase", "unknown"),
    )

    return final_state
