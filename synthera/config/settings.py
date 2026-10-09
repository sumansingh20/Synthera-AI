"""Centralized configuration management using Pydantic Settings."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class ResearchDepth(str, Enum):
    QUICK = "quick"
    MODERATE = "moderate"
    COMPREHENSIVE = "comprehensive"


class SearchProvider(str, Enum):
    TAVILY = "tavily"
    SERPAPI = "serpapi"


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── LLM ──────────────────────────────────────────────
    openai_api_key: str = Field(..., description="OpenAI API key")
    openai_model: str = Field(default="gpt-4o", description="OpenAI model name")

    # ── Search ───────────────────────────────────────────
    tavily_api_key: Optional[str] = Field(default=None, description="Tavily API key")
    serpapi_api_key: Optional[str] = Field(default=None, description="SerpAPI key")
    search_provider: SearchProvider = Field(default=SearchProvider.TAVILY)
    max_search_results: int = Field(default=10, ge=1, le=50)

    # ── LangSmith ────────────────────────────────────────
    langchain_tracing_v2: bool = Field(default=True)
    langchain_api_key: Optional[str] = Field(default=None)
    langchain_project: str = Field(default="synthera")
    langchain_endpoint: str = Field(default="https://api.smith.langchain.com")

    # ── RAG / Vector Store ───────────────────────────────
    chroma_persist_dir: str = Field(default="./chroma_db")
    embedding_model: str = Field(default="text-embedding-3-small")
    chunk_size: int = Field(default=1000, ge=100, le=4000)
    chunk_overlap: int = Field(default=200, ge=0, le=1000)

    # ── API ──────────────────────────────────────────────
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    api_reload: bool = Field(default=True)
    cors_origins: list[str] = Field(default=["http://localhost:8501"])

    # ── Research ─────────────────────────────────────────
    default_research_depth: ResearchDepth = Field(default=ResearchDepth.COMPREHENSIVE)
    max_scrape_concurrent: int = Field(default=5, ge=1, le=20)
    request_timeout: int = Field(default=30, ge=5, le=120)
    max_hops: int = Field(default=3, ge=1, le=10)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v

    @property
    def chroma_path(self) -> Path:
        return Path(self.chroma_persist_dir).resolve()


settings = Settings()
