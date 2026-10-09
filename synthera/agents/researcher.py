"""Researcher agent — plans sub-queries and drives multi-hop search strategy.

This agent takes the user's high-level research query and decomposes it
into focused sub-queries. On subsequent hops, it analyzes gaps in the
collected evidence and generates targeted follow-up queries.
"""

from __future__ import annotations

from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from synthera.config import settings
from synthera.agents.states import ResearchPhase
from synthera.utils import get_logger

logger = get_logger(__name__)

PLANNER_SYSTEM_PROMPT = """\
You are an expert research strategist. Your job is to decompose a research
question into focused, searchable sub-queries that together will provide
comprehensive coverage of the topic.

Rules:
- Generate {num_queries} distinct sub-queries that cover different facets.
- Each sub-query should be self-contained and specific enough for a web search.
- Avoid redundancy — each query should target unique information.
- Output ONLY the queries, one per line, no numbering or bullets.
"""

GAP_ANALYSIS_PROMPT = """\
You are reviewing evidence gathered so far for a research task.

Original query: {query}
Sub-queries explored: {explored}
Evidence snippets:
{evidence}

Identify 2-3 information gaps that remain and generate targeted search
queries to fill them. Output ONLY the queries, one per line.
"""


def _build_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0.2,
        max_tokens=1024,
    )


async def plan_research(state: dict[str, Any]) -> dict[str, Any]:
    """Generate initial sub-queries from the user's research question.

    Node: PLANNING → SEARCHING
    """
    query = state["query"]
    depth = state.get("depth", "comprehensive")

    num_queries = {"quick": 3, "moderate": 5, "comprehensive": 8}.get(depth, 5)

    logger.info("Planning research for: %s (depth=%s, queries=%d)", query, depth, num_queries)

    llm = _build_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", PLANNER_SYSTEM_PROMPT),
        ("human", "Research question: {query}"),
    ])

    chain = prompt | llm
    response = await chain.ainvoke({"query": query, "num_queries": num_queries})

    sub_queries = [q.strip() for q in response.content.strip().split("\n") if q.strip()]

    logger.info("Generated %d sub-queries", len(sub_queries))

    return {
        "sub_queries": sub_queries,
        "phase": ResearchPhase.SEARCHING.value,
        "current_hop": 1,
    }


async def analyze_gaps(state: dict[str, Any]) -> dict[str, Any]:
    """Analyze collected evidence and produce follow-up queries for the next hop.

    Node: ANALYZING → SEARCHING (if more hops) or SYNTHESIZING
    """
    query = state["query"]
    current_hop = state.get("current_hop", 1)
    max_hops = state.get("max_hops", 3)
    documents = state.get("documents", [])
    explored = state.get("sub_queries", [])

    if current_hop >= max_hops or not documents:
        logger.info("No more hops needed (hop=%d/%d). Moving to synthesis.", current_hop, max_hops)
        return {"phase": ResearchPhase.SYNTHESIZING.value}

    evidence_text = "\n\n".join(
        f"[{doc.get('title', 'Untitled')}]: {doc.get('snippet', '')[:200]}"
        for doc in documents[-10:]
    )

    llm = _build_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", GAP_ANALYSIS_PROMPT),
    ])

    chain = prompt | llm
    response = await chain.ainvoke({
        "query": query,
        "explored": "\n".join(explored),
        "evidence": evidence_text,
    })

    new_queries = [q.strip() for q in response.content.strip().split("\n") if q.strip()]

    logger.info("Gap analysis produced %d follow-up queries (hop %d)", len(new_queries), current_hop + 1)

    return {
        "sub_queries": explored + new_queries,
        "phase": ResearchPhase.SEARCHING.value,
        "current_hop": current_hop + 1,
    }
