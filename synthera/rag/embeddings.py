"""Embedding function factory for the RAG pipeline.

Provides a centralized way to create and configure embedding functions
used by the vector store for document indexing and query matching.
"""

from __future__ import annotations

from functools import lru_cache

from langchain_openai import OpenAIEmbeddings

from synthera.config import settings
from synthera.utils import get_logger

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def get_embedding_function() -> OpenAIEmbeddings:
    """Create and cache the OpenAI embedding function.

    Uses lru_cache to ensure a single embedding instance is reused
    across the application, avoiding redundant initialization.

    Returns:
        Configured OpenAIEmbeddings instance.
    """
    logger.info("Initializing embedding model: %s", settings.embedding_model)

    embeddings = OpenAIEmbeddings(
        model=settings.embedding_model,
        api_key=settings.openai_api_key,
    )

    return embeddings
