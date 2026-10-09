"""RAG retriever node — stores scraped documents and retrieves relevant context.

This node sits between the scraper and analyzer in the graph pipeline.
It chunks incoming documents, indexes them in ChromaDB, then performs
similarity search against the original query to produce focused context.
"""

from __future__ import annotations

from typing import Any

from synthera.rag.vectorstore import add_documents_to_store, retrieve_relevant
from synthera.utils import get_logger

logger = get_logger(__name__)


async def store_and_retrieve(state: dict[str, Any]) -> dict[str, Any]:
    """Store new documents in the vector store and retrieve relevant context.

    Node: SCRAPING → RAG → ANALYZING
    Indexes scraped documents, then retrieves the most relevant chunks
    for the original query to provide focused context for analysis.
    """
    query = state["query"]
    documents = state.get("documents", [])

    if not documents:
        logger.warning("No documents to store in RAG pipeline")
        return {"rag_context": ""}

    # Only index documents that haven't been indexed yet
    # Track by checking document count vs stored count
    new_docs = documents[-10:]  # Index the most recent batch

    try:
        chunks_added = add_documents_to_store(new_docs)
        logger.info("Indexed %d chunks from %d new documents", chunks_added, len(new_docs))
    except Exception as e:
        logger.error("Failed to index documents: %s", str(e))
        return {"rag_context": ""}

    # Retrieve relevant context for the research query
    try:
        relevant_chunks = retrieve_relevant(query, k=8)

        # Compile retrieved chunks into a context string
        context_parts = []
        seen_content = set()

        for chunk in relevant_chunks:
            content_hash = hash(chunk.page_content[:100])
            if content_hash in seen_content:
                continue
            seen_content.add(content_hash)

            source = chunk.metadata.get("title", "Unknown")
            url = chunk.metadata.get("source_url", "")
            context_parts.append(
                f"[From: {source}]\n"
                f"URL: {url}\n"
                f"{chunk.page_content}\n"
            )

        rag_context = "\n---\n".join(context_parts)
        logger.info("RAG context compiled: %d unique chunks, %d chars", len(context_parts), len(rag_context))

    except Exception as e:
        logger.error("RAG retrieval failed: %s", str(e))
        rag_context = ""

    return {"rag_context": rag_context}
