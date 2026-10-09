"""ChromaDB vector store management for the RAG pipeline.

Handles initialization, persistence, and lifecycle of the ChromaDB
collection used to store and retrieve research document embeddings.
"""

from __future__ import annotations

from functools import lru_cache

from langchain_chroma import Chroma
from langchain_core.documents import Document

from synthera.config import settings
from synthera.rag.embeddings import get_embedding_function
from synthera.utils import get_logger

logger = get_logger(__name__)

COLLECTION_NAME = "research_documents"


@lru_cache(maxsize=1)
def get_vectorstore() -> Chroma:
    """Create or connect to the persistent ChromaDB vector store.

    Returns:
        Initialized Chroma vector store instance.
    """
    persist_dir = str(settings.chroma_path)
    logger.info("Connecting to ChromaDB at: %s", persist_dir)

    vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=get_embedding_function(),
        persist_directory=persist_dir,
    )

    logger.info("ChromaDB ready (collection: %s)", COLLECTION_NAME)
    return vectorstore


def reset_vectorstore() -> None:
    """Clear all documents from the vector store.

    Useful between research sessions to prevent cross-contamination
    of context between unrelated queries.
    """
    get_vectorstore.cache_clear()
    store = get_vectorstore()
    store.delete_collection()
    get_vectorstore.cache_clear()
    logger.info("Vector store reset — collection deleted")


def add_documents_to_store(documents: list[dict]) -> int:
    """Chunk and add documents to the vector store.

    Args:
        documents: List of document dicts with 'content', 'url', 'title' keys.

    Returns:
        Number of chunks added to the store.
    """
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    store = get_vectorstore()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    langchain_docs = []
    for doc in documents:
        chunks = splitter.split_text(doc.get("content", ""))
        for i, chunk in enumerate(chunks):
            langchain_docs.append(
                Document(
                    page_content=chunk,
                    metadata={
                        "source_url": doc.get("url", ""),
                        "title": doc.get("title", "Untitled"),
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                    },
                )
            )

    if langchain_docs:
        store.add_documents(langchain_docs)
        logger.info("Added %d chunks from %d documents to vector store", len(langchain_docs), len(documents))

    return len(langchain_docs)


def retrieve_relevant(query: str, k: int = 8) -> list[Document]:
    """Retrieve the top-k most relevant document chunks for a query.

    Args:
        query: Search query string.
        k: Number of chunks to retrieve.

    Returns:
        List of relevant LangChain Document objects.
    """
    store = get_vectorstore()
    results = store.similarity_search(query, k=k)
    logger.info("Retrieved %d chunks for query: '%s'", len(results), query[:60])
    return results
