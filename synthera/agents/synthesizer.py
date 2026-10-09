"""Synthesizer agent — generates the final research report with citations.

Takes all collected evidence (scraped documents + RAG context) and produces
a well-structured, comprehensive report. Includes inline citations,
a references section, and suggested follow-up questions.
"""

from __future__ import annotations

from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from synthera.config import settings
from synthera.agents.states import ResearchPhase
from synthera.utils import get_logger, build_citation, format_report_timestamp

logger = get_logger(__name__)

SYNTHESIS_SYSTEM_PROMPT = """\
You are an expert research analyst. Your task is to synthesize evidence from
multiple sources into a comprehensive, well-structured research report.

Rules:
1. Structure the report with clear sections: Executive Summary, Key Findings,
   Detailed Analysis, and Conclusion.
2. Use inline citations in the format [1], [2], etc. referencing the sources.
3. Be objective — present multiple perspectives when sources disagree.
4. Highlight confidence levels: what is well-established vs. emerging/uncertain.
5. End with 3-5 suggested follow-up research questions.
6. Write in a professional, academic tone.
7. Target length: 1500-3000 words depending on depth.
"""

SYNTHESIS_HUMAN_PROMPT = """\
Research Question: {query}

Depth: {depth}
Sources collected: {num_sources}
Research hops completed: {hops}

=== EVIDENCE FROM SOURCES ===
{evidence}

=== RAG RETRIEVED CONTEXT ===
{rag_context}

Generate the comprehensive research report now.
"""


def _build_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0.3,
        max_tokens=4096,
    )


def _compile_evidence(documents: list[dict]) -> str:
    """Format collected documents into numbered evidence blocks."""
    evidence_parts = []
    for i, doc in enumerate(documents, 1):
        evidence_parts.append(
            f"[Source {i}] {doc.get('title', 'Untitled')}\n"
            f"URL: {doc.get('url', 'N/A')}\n"
            f"Content:\n{doc.get('content', '')[:2000]}\n"
        )
    return "\n---\n".join(evidence_parts)


async def synthesize_report(state: dict[str, Any]) -> dict[str, Any]:
    """Generate the final research report from all collected evidence.

    Node: SYNTHESIZING → COMPLETE
    """
    query = state["query"]
    documents = state.get("documents", [])
    rag_context = state.get("rag_context", "")
    depth = state.get("depth", "comprehensive")
    current_hop = state.get("current_hop", 1)

    if not documents:
        logger.warning("No documents available for synthesis")
        return {
            "report": "Unable to generate report — no source documents were collected.",
            "phase": ResearchPhase.ERROR.value,
            "errors": state.get("errors", []) + ["No documents collected for synthesis"],
        }

    logger.info(
        "Synthesizing report from %d documents (depth=%s, hops=%d)",
        len(documents), depth, current_hop,
    )

    evidence_text = _compile_evidence(documents)

    llm = _build_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYNTHESIS_SYSTEM_PROMPT),
        ("human", SYNTHESIS_HUMAN_PROMPT),
    ])

    chain = prompt | llm
    response = await chain.ainvoke({
        "query": query,
        "depth": depth,
        "num_sources": len(documents),
        "hops": current_hop,
        "evidence": evidence_text,
        "rag_context": rag_context[:3000] if rag_context else "No additional RAG context.",
    })

    report_text = response.content.strip()

    # Build structured citations list
    citations = [
        build_citation(
            title=doc.get("title", "Untitled"),
            url=doc.get("url", ""),
            snippet=doc.get("snippet", ""),
        )
        for doc in documents
    ]

    # Extract follow-up questions from the report (if the LLM included them)
    follow_ups = []
    if "follow-up" in report_text.lower() or "further research" in report_text.lower():
        lines = report_text.split("\n")
        capture = False
        for line in lines:
            if "follow-up" in line.lower() or "further research" in line.lower():
                capture = True
                continue
            if capture and line.strip().startswith(("- ", "• ", "1.", "2.", "3.", "4.", "5.")):
                follow_ups.append(line.strip().lstrip("-•0123456789. "))

    # Prepend metadata header
    timestamp = format_report_timestamp()
    header = (
        f"# Research Report: {query}\n\n"
        f"**Generated:** {timestamp}  \n"
        f"**Depth:** {depth}  \n"
        f"**Sources analyzed:** {len(documents)}  \n"
        f"**Research hops:** {current_hop}  \n\n---\n\n"
    )

    final_report = header + report_text

    logger.info("Report generated successfully (%d chars, %d citations)", len(final_report), len(citations))

    return {
        "report": final_report,
        "citations": citations,
        "follow_up_questions": follow_ups[:5],
        "phase": ResearchPhase.COMPLETE.value,
    }
