"""Pydantic request/response schemas for the Research API."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ResearchDepthEnum(str, Enum):
    QUICK = "quick"
    MODERATE = "moderate"
    COMPREHENSIVE = "comprehensive"


# ── Request Schemas ──────────────────────────────────────

class ResearchRequest(BaseModel):
    """Payload to start a new research task."""
    query: str = Field(..., min_length=5, max_length=500, description="Research question")
    depth: ResearchDepthEnum = Field(default=ResearchDepthEnum.COMPREHENSIVE)
    max_hops: int = Field(default=3, ge=1, le=10, description="Max search-analyze cycles")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "query": "What are the latest advances in quantum computing?",
                    "depth": "comprehensive",
                    "max_hops": 3,
                }
            ]
        }
    }


class PDFExportRequest(BaseModel):
    """Request to export a research result as PDF."""
    task_id: str = Field(..., description="ID of the completed research task")


# ── Response Schemas ─────────────────────────────────────

class Citation(BaseModel):
    title: str
    url: str
    snippet: str = ""
    accessed_at: str = ""


class ResearchResponse(BaseModel):
    """Response returned when research completes."""
    task_id: str
    query: str
    status: str
    report: str = ""
    citations: list[Citation] = []
    follow_up_questions: list[str] = []
    documents_analyzed: int = 0
    hops_completed: int = 0
    errors: list[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ResearchStatusResponse(BaseModel):
    """Lightweight status check response."""
    task_id: str
    status: str
    phase: str = ""
    progress_pct: int = 0
    documents_collected: int = 0


class PDFExportResponse(BaseModel):
    """Response after PDF export."""
    task_id: str
    pdf_path: str
    file_size_kb: float


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "1.0.0"
    services: dict[str, str] = {}
