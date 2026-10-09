"""Research API routes — start, status, and export endpoints.

Provides async research execution with task tracking. Research jobs
run in background tasks, with status polling and PDF export support.
"""

from __future__ import annotations

import uuid
import asyncio
from typing import Any

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

from synthera.api.models.schemas import (
    ResearchRequest,
    ResearchResponse,
    ResearchStatusResponse,
    PDFExportRequest,
    PDFExportResponse,
)
from synthera.agents.graph import run_research
from synthera.tools.pdf_export import export_to_pdf
from synthera.rag.vectorstore import reset_vectorstore
from synthera.utils import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/research", tags=["Research"])

# In-memory task store (production would use Redis or a database)
_tasks: dict[str, dict[str, Any]] = {}


async def _execute_research(task_id: str, query: str, depth: str, max_hops: int) -> None:
    """Background task that runs the full research pipeline."""
    try:
        _tasks[task_id]["status"] = "running"
        _tasks[task_id]["phase"] = "planning"

        # Reset vector store for fresh research session
        reset_vectorstore()

        result = await run_research(query=query, depth=depth, max_hops=max_hops)

        _tasks[task_id].update({
            "status": "completed",
            "phase": result.get("phase", "complete"),
            "result": result,
        })

        logger.info("Task %s completed successfully", task_id)

    except Exception as e:
        logger.error("Task %s failed: %s", task_id, str(e))
        _tasks[task_id].update({
            "status": "failed",
            "phase": "error",
            "error": str(e),
        })


@router.post("/start", response_model=ResearchStatusResponse)
async def start_research(
    request: ResearchRequest,
    background_tasks: BackgroundTasks,
) -> ResearchStatusResponse:
    """Start a new research task.

    The research pipeline runs asynchronously. Use the /status endpoint
    to poll for completion, then retrieve results via /result.
    """
    task_id = str(uuid.uuid4())

    _tasks[task_id] = {
        "task_id": task_id,
        "query": request.query,
        "depth": request.depth.value,
        "max_hops": request.max_hops,
        "status": "queued",
        "phase": "queued",
        "result": None,
        "error": None,
    }

    background_tasks.add_task(
        _execute_research,
        task_id=task_id,
        query=request.query,
        depth=request.depth.value,
        max_hops=request.max_hops,
    )

    logger.info("Research task queued: %s (query='%s')", task_id, request.query[:60])

    return ResearchStatusResponse(
        task_id=task_id,
        status="queued",
        phase="queued",
        progress_pct=0,
    )


@router.get("/status/{task_id}", response_model=ResearchStatusResponse)
async def get_research_status(task_id: str) -> ResearchStatusResponse:
    """Check the status of a running research task."""
    if task_id not in _tasks:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    task = _tasks[task_id]
    result = task.get("result") or {}

    # Estimate progress based on phase
    phase_progress = {
        "queued": 0, "planning": 10, "searching": 30,
        "scraping": 50, "analyzing": 65, "synthesizing": 85,
        "complete": 100, "error": 0,
    }

    return ResearchStatusResponse(
        task_id=task_id,
        status=task["status"],
        phase=task.get("phase", ""),
        progress_pct=phase_progress.get(task.get("phase", ""), 0),
        documents_collected=len(result.get("documents", [])),
    )


@router.get("/result/{task_id}", response_model=ResearchResponse)
async def get_research_result(task_id: str) -> ResearchResponse:
    """Retrieve the full result of a completed research task."""
    if task_id not in _tasks:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    task = _tasks[task_id]

    if task["status"] == "running":
        raise HTTPException(status_code=202, detail="Research still in progress")

    if task["status"] == "failed":
        raise HTTPException(status_code=500, detail=task.get("error", "Unknown error"))

    result = task.get("result", {})

    return ResearchResponse(
        task_id=task_id,
        query=task["query"],
        status=task["status"],
        report=result.get("report", ""),
        citations=[
            {"title": c["title"], "url": c["url"], "snippet": c.get("snippet", ""), "accessed_at": c.get("accessed_at", "")}
            for c in result.get("citations", [])
        ],
        follow_up_questions=result.get("follow_up_questions", []),
        documents_analyzed=len(result.get("documents", [])),
        hops_completed=result.get("current_hop", 0),
        errors=result.get("errors", []),
    )


@router.post("/export-pdf", response_model=PDFExportResponse)
async def export_research_pdf(request: PDFExportRequest) -> PDFExportResponse:
    """Export a completed research report as a formatted PDF."""
    if request.task_id not in _tasks:
        raise HTTPException(status_code=404, detail=f"Task {request.task_id} not found")

    task = _tasks[request.task_id]

    if task["status"] != "completed":
        raise HTTPException(status_code=400, detail="Research must be completed before export")

    result = task["result"]

    pdf_path = export_to_pdf(
        report=result.get("report", ""),
        citations=result.get("citations", []),
        query=task["query"],
        metadata={
            "Research Query": task["query"],
            "Depth": task["depth"],
            "Sources": str(len(result.get("documents", []))),
            "Hops": str(result.get("current_hop", 0)),
        },
    )

    file_size_kb = pdf_path.stat().st_size / 1024

    return PDFExportResponse(
        task_id=request.task_id,
        pdf_path=str(pdf_path),
        file_size_kb=round(file_size_kb, 2),
    )


@router.get("/download/{task_id}")
async def download_pdf(task_id: str) -> FileResponse:
    """Download the generated PDF report."""
    if task_id not in _tasks:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    task = _tasks[task_id]
    if task["status"] != "completed":
        raise HTTPException(status_code=400, detail="Research must be completed first")

    result = task["result"]
    pdf_path = export_to_pdf(
        report=result.get("report", ""),
        citations=result.get("citations", []),
        query=task["query"],
    )

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=pdf_path.name,
    )
