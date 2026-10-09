# Architecture Overview

## System Design

The Synthera follows a **multi-agent pipeline architecture** where specialized agents handle distinct phases of the research process. The system is orchestrated by LangGraph, which manages state transitions and conditional routing between agents.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Streamlit Frontend                          │
│  ┌──────────┐  ┌──────────────┐  ┌────────────────────────┐   │
│  │ Sidebar   │  │ Research     │  │ Report Viewer          │   │
│  │ Config    │  │ Input + Chat │  │ + Citations + Export   │   │
│  └──────────┘  └──────────────┘  └────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP/REST
┌────────────────────────▼────────────────────────────────────────┐
│                     FastAPI Backend                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ /health      │  │ /research/*  │  │ /export-pdf          │  │
│  │ endpoint     │  │ CRUD + async │  │ PDF generation       │  │
│  └──────────────┘  └──────┬───────┘  └──────────────────────┘  │
└───────────────────────────┼─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                  LangGraph Orchestration                         │
│                                                                  │
│   ┌──────┐    ┌────────┐    ┌────────┐    ┌──────────┐         │
│   │ PLAN │───▶│ SEARCH │───▶│ SCRAPE │───▶│ RAG      │         │
│   │      │    │        │    │        │    │ Store +   │         │
│   └──────┘    └────────┘    └────────┘    │ Retrieve  │         │
│                    ▲                       └────┬─────┘         │
│                    │                            │               │
│                    │    ┌──────────┐             │               │
│                    └────│ ANALYZE  │◀────────────┘               │
│                         │ (gaps?)  │                             │
│                         └────┬─────┘                             │
│                              │                                   │
│                    ┌─────────▼──────────┐                       │
│                    │    SYNTHESIZE      │                        │
│                    │  (final report)    │                        │
│                    └───────────────────┘                         │
└─────────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────────┐
│ Tavily /     │  │ ChromaDB     │  │ LangSmith        │
│ SerpAPI      │  │ Vector Store │  │ Tracing          │
│ (Web Search) │  │ (RAG)        │  │ (Observability)  │
└──────────────┘  └──────────────┘  └──────────────────┘
```

## Agent Descriptions

### 1. Researcher Agent (`researcher.py`)
- **Role**: Strategic planner that decomposes queries into sub-queries
- **Input**: User's research question + depth setting
- **Output**: List of targeted sub-queries
- **Multi-hop**: Performs gap analysis after each cycle to identify missing information

### 2. Search Tool (`search.py`)
- **Role**: Executes web searches across configured providers
- **Providers**: Tavily (default) or SerpAPI
- **Deduplication**: Tracks visited URLs to avoid redundant searches

### 3. Scraper Agent (`scraper.py`)
- **Role**: Fetches and cleans web content from search result URLs
- **Features**: Concurrent scraping, domain filtering, content extraction
- **Output**: Cleaned document objects with metadata

### 4. RAG Pipeline (`rag/`)
- **Role**: Indexes scraped documents and retrieves relevant context
- **Store**: ChromaDB with OpenAI embeddings
- **Chunking**: Recursive character splitting with configurable size/overlap

### 5. Synthesizer Agent (`synthesizer.py`)
- **Role**: Generates the final research report
- **Output**: Structured report with inline citations, references, follow-up questions

## Data Flow

1. User submits a research query via the Streamlit UI
2. Frontend sends POST to `/api/v1/research/start`
3. Backend creates a background task and returns a task ID
4. LangGraph executes the multi-agent pipeline:
   - **Plan** → decompose query into sub-queries
   - **Search** → execute web searches for each sub-query
   - **Scrape** → fetch and clean web content
   - **RAG Store** → index documents in ChromaDB
   - **Analyze** → check for information gaps
   - Loop back to Search if more hops needed
   - **Synthesize** → generate final report
5. Frontend polls `/api/v1/research/status/{id}` for progress
6. On completion, frontend fetches full result and renders report
7. User can export to PDF via `/api/v1/research/export-pdf`

## Technology Stack

| Component       | Technology                          |
|----------------|-------------------------------------|
| Orchestration  | LangGraph                           |
| LLM            | OpenAI GPT-4o                       |
| Web Search     | Tavily / SerpAPI                    |
| Web Scraping   | BeautifulSoup + httpx               |
| Vector Store   | ChromaDB                            |
| Embeddings     | OpenAI text-embedding-3-small       |
| Backend API    | FastAPI + Uvicorn                   |
| Frontend       | Streamlit                           |
| Tracing        | LangSmith                           |
| PDF Export     | fpdf2                               |
| Containerization | Docker + Docker Compose           |
