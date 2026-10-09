# API Reference

Base URL: `http://localhost:8000`

## Endpoints

### Health Check

```
GET /api/v1/health
```

Returns API health status and dependent service information.

**Response** `200 OK`
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "api": "up",
    "vectorstore": "configured",
    "search_provider": "tavily",
    "llm_model": "gpt-4o",
    "langsmith": "configured"
  }
}
```

---

### Start Research

```
POST /api/v1/research/start
```

Initiates a new research task. The research runs asynchronously in the background.

**Request Body**
```json
{
  "query": "What are the latest advances in quantum computing?",
  "depth": "comprehensive",
  "max_hops": 3
}
```

| Field     | Type   | Required | Description |
|-----------|--------|----------|-------------|
| query     | string | Yes      | Research question (5-500 chars) |
| depth     | enum   | No       | `quick`, `moderate`, `comprehensive` (default) |
| max_hops  | int    | No       | Max search cycles, 1-10 (default: 3) |

**Response** `200 OK`
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "phase": "queued",
  "progress_pct": 0
}
```

---

### Check Status

```
GET /api/v1/research/status/{task_id}
```

Poll for research task progress.

**Response** `200 OK`
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "phase": "scraping",
  "progress_pct": 50,
  "documents_collected": 8
}
```

---

### Get Result

```
GET /api/v1/research/result/{task_id}
```

Retrieve the full research result after completion.

**Response** `200 OK`
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "query": "What are the latest advances in quantum computing?",
  "status": "completed",
  "report": "# Research Report: ...",
  "citations": [
    {
      "title": "Quantum Computing Advances",
      "url": "https://example.com/article",
      "snippet": "Recent breakthroughs...",
      "accessed_at": "2025-01-15T10:30:00Z"
    }
  ],
  "follow_up_questions": [
    "How will quantum error correction impact timelines?",
    "What are the leading commercial quantum platforms?"
  ],
  "documents_analyzed": 12,
  "hops_completed": 3,
  "errors": []
}
```

---

### Export PDF

```
POST /api/v1/research/export-pdf
```

Generate a formatted PDF from a completed research task.

**Request Body**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response** `200 OK`
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "pdf_path": "reports_output/quantum_computing_advances_20250115_103000.pdf",
  "file_size_kb": 245.8
}
```

---

### Download PDF

```
GET /api/v1/research/download/{task_id}
```

Download the generated PDF file directly.

**Response** `200 OK` — `application/pdf` file download

---

## Error Responses

| Status | Description |
|--------|-------------|
| 404    | Task ID not found |
| 422    | Validation error (bad request body) |
| 202    | Research still in progress (result not ready) |
| 500    | Internal error / research task failed |
