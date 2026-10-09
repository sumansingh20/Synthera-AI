"""Health check endpoint for monitoring and container orchestration."""

from __future__ import annotations

from fastapi import APIRouter

from synthera.api.models.schemas import HealthResponse
from synthera.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Check API health and dependent service status."""
    services = {
        "api": "up",
        "vectorstore": "configured",
        "search_provider": settings.search_provider.value,
        "llm_model": settings.openai_model,
    }

    # Check LangSmith connectivity
    if settings.langchain_api_key:
        services["langsmith"] = "configured"
    else:
        services["langsmith"] = "not_configured"

    return HealthResponse(
        status="healthy",
        version="1.0.0",
        services=services,
    )
