"""FastAPI application entry point.

Configures the API server with all routes, middleware, and lifecycle
events. Serves as the backend for the Streamlit research UI.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from synthera.api.middleware.cors import setup_cors
from synthera.api.routes import health, research
from synthera.utils import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    logger.info("Starting Synthera API...")
    logger.info("API docs available at /docs")
    yield
    logger.info("Shutting down Synthera API...")


app = FastAPI(
    title="Synthera API",
    description=(
        "Multi-agent research tool that searches the web, reads articles, "
        "and synthesizes comprehensive reports with citations. "
        "Powered by LangGraph, RAG, and LangSmith."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Middleware
setup_cors(app)

# Routes
app.include_router(health.router, prefix="/api/v1")
app.include_router(research.router, prefix="/api/v1")


@app.get("/", tags=["Root"])
async def root():
    return {
        "name": "Synthera",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }
